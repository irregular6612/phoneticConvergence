import argparse
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Interval:
    xmin: float
    xmax: float
    text: str


@dataclass
class IntervalTier:
    name: str
    xmin: float
    xmax: float
    intervals: List[Interval]


@dataclass
class TextGrid:
    xmin: float
    xmax: float
    tiers: List[IntervalTier]


EPS = 1e-7


def is_close(a: float, b: float, *, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def is_vowel_label(label: str) -> bool:
    if not label:
        return False
    norm = label.strip().lower()
    if norm in {"sp", "sil", "silence", "pau"}:
        return False
    # Detect vowels in common roman/IPA/hangul-jamo forms
    roman_vowel_chars = set("aeiou")
    ipa_vowel_chars = set("iyɨʉɯuɪʏʊeøɘɵɤoəœɜɞʌɔæɐaɶɑɒ")
    hangul_jamo_vowels = set("ㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣㅐㅔㅒㅖㅘㅙㅚㅝㅞㅟㅢ")
    return any(c in roman_vowel_chars or c in ipa_vowel_chars or c in hangul_jamo_vowels for c in norm)


def parse_textgrid_long(path: str) -> TextGrid:
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    def get_value_after_equals(line: str) -> str:
        # handles patterns like: name = "phone" or xmin = 0.0
        return line.split("=", 1)[1].strip().strip('"')

    # Header
    # We assume long TextGrid format as in sample
    # Find global xmin/xmax
    tg_xmin = float(get_value_after_equals(next(l for l in lines if l.strip().startswith("xmin = "))))
    tg_xmax = float(get_value_after_equals(next(l for l in lines if l.strip().startswith("xmax = "))))

    # Parse tiers
    tiers: List[IntervalTier] = []
    i = 0
    n = len(lines)

    # Seek to 'item []:'
    while i < n and not lines[i].strip().startswith("item []:"):
        i += 1
    if i >= n:
        return TextGrid(xmin=tg_xmin, xmax=tg_xmax, tiers=[])
    i += 1

    while i < n:
        line = lines[i]
        if line.strip().startswith("item ["):
            # Expect an IntervalTier
            i += 1
            cls = get_value_after_equals(lines[i]).strip()
            i += 1
            name = get_value_after_equals(lines[i]).strip()
            i += 1
            tier_xmin = float(get_value_after_equals(lines[i]))
            i += 1
            tier_xmax = float(get_value_after_equals(lines[i]))
            i += 1
            # intervals: size = N
            size_line = lines[i]
            assert "intervals: size" in size_line
            size = int(get_value_after_equals(size_line).split()[0])
            i += 1

            intervals: List[Interval] = []
            for _ in range(size):
                assert lines[i].strip().startswith("intervals [")
                i += 1
                xmin = float(get_value_after_equals(lines[i]))
                i += 1
                xmax = float(get_value_after_equals(lines[i]))
                i += 1
                text = get_value_after_equals(lines[i])
                i += 1
                intervals.append(Interval(xmin=xmin, xmax=xmax, text=text))

            if cls == "IntervalTier":
                tiers.append(IntervalTier(name=name, xmin=tier_xmin, xmax=tier_xmax, intervals=intervals))
        else:
            i += 1

    return TextGrid(xmin=tg_xmin, xmax=tg_xmax, tiers=tiers)


def serialize_textgrid_long(tg: TextGrid) -> str:
    # Match Praat long TextGrid format indentation (4 spaces)
    lines: List[str] = []
    lines.append('File type = "ooTextFile"')
    lines.append('Object class = "TextGrid"')
    lines.append("")
    lines.append(f"xmin = {tg.xmin}")
    lines.append(f"xmax = {tg.xmax}")
    lines.append("tiers? <exists>")
    lines.append(f"size = {len(tg.tiers)}")
    lines.append("item []:")
    for t_idx, tier in enumerate(tg.tiers, start=1):
        lines.append(f"    item [{t_idx}]:")
        lines.append('        class = "IntervalTier"')
        lines.append(f'        name = "{tier.name}"')
        lines.append(f"        xmin = {tier.xmin}")
        lines.append(f"        xmax = {tier.xmax}")
        lines.append(f"        intervals: size = {len(tier.intervals)}")
        for i_idx, itv in enumerate(tier.intervals, start=1):
            lines.append(f"        intervals [{i_idx}]:")
            lines.append(f"            xmin = {itv.xmin}")
            lines.append(f"            xmax = {itv.xmax}")
            lines.append(f'            text = "{itv.text}"')
    return "\n".join(lines) + "\n"


def align_adjacent_phone_boundaries(phone_tier: IntervalTier) -> Tuple[int, List[Tuple[int, float, float]]]:
    """
    Align adjacent boundaries in the phone tier according to rules:
    - If exactly one of the adjacent intervals is a vowel, keep the vowel's boundary and adjust the non-vowel.
    - Otherwise (both vowels or both non-vowels), set boundary to the average of the two times.
    Returns number of fixes and a list of (boundary_index, old_boundary, new_boundary).
    """
    fixes = 0
    changes: List[Tuple[int, float, float]] = []
    for i in range(len(phone_tier.intervals) - 1):
        left = phone_tier.intervals[i]
        right = phone_tier.intervals[i + 1]
        if is_close(left.xmax, right.xmin):
            continue
        left_is_vowel = is_vowel_label(left.text)
        right_is_vowel = is_vowel_label(right.text)

        old_left_xmax = left.xmax
        old_right_xmin = right.xmin

        if left_is_vowel ^ right_is_vowel:
            if left_is_vowel:
                # Keep left.xmax; move right.xmin to left.xmax
                right.xmin = left.xmax
                boundary = right.xmin
            else:
                # Keep right.xmin; move left.xmax to right.xmin
                left.xmax = right.xmin
                boundary = left.xmax
        else:
            # Average
            boundary = (left.xmax + right.xmin) / 2.0
            left.xmax = boundary
            right.xmin = boundary

        # Guard against inversion or going out of tier bounds
        left.xmax = max(left.xmin, min(left.xmax, phone_tier.xmax))
        right.xmin = min(right.xmax, max(right.xmin, phone_tier.xmin))

        fixes += 1
        changes.append((i + 1, (old_left_xmax + old_right_xmin) / 2.0, boundary))

    return fixes, changes


def adjust_word_tier_to_phone(word_tier: IntervalTier, phone_tier: IntervalTier, original_word_times: List[Tuple[float, float]]) -> int:
    """
    For each word interval, adjust [xmin, xmax] to match the span of overlapping phone intervals
    determined by the original word times.
    Returns number of intervals adjusted.
    """
    adjusted = 0
    for idx, word in enumerate(word_tier.intervals):
        orig_start, orig_end = original_word_times[idx]
        # Collect phones that overlap with original word span
        overlapped: List[Interval] = []
        for ph in phone_tier.intervals:
            start = max(ph.xmin, orig_start)
            end = min(ph.xmax, orig_end)
            if end - start > EPS:
                overlapped.append(ph)
        if overlapped:
            new_start = overlapped[0].xmin
            new_end = overlapped[-1].xmax
            if not (is_close(word.xmin, new_start) and is_close(word.xmax, new_end)):
                word.xmin = new_start
                word.xmax = new_end
                adjusted += 1
        else:
            # Fallback to nearest phone boundaries
            all_bounds = sorted({b for ph in phone_tier.intervals for b in (ph.xmin, ph.xmax)})
            # Nearest to orig_start and orig_end respectively
            if all_bounds:
                nearest_start = min(all_bounds, key=lambda v: abs(v - orig_start))
                nearest_end = min(all_bounds, key=lambda v: abs(v - orig_end))
                if nearest_end < nearest_start:
                    nearest_start, nearest_end = nearest_end, nearest_start
                if not (is_close(word.xmin, nearest_start) and is_close(word.xmax, nearest_end)):
                    word.xmin = nearest_start
                    word.xmax = nearest_end
                    adjusted += 1
    return adjusted


def align_word_boundaries_to_phone(word_tier: IntervalTier, phone_tier: IntervalTier) -> int:
    """
    Make adjacent word intervals meet exactly at a shared boundary snapped to the nearest
    phone boundary, preserving adjacency and cross-tier consistency.
    Returns number of boundary adjustments performed.
    """
    if not word_tier.intervals:
        return 0

    phone_bounds = sorted({b for ph in phone_tier.intervals for b in (ph.xmin, ph.xmax)})
    if not phone_bounds:
        return 0

    fixes = 0
    for i in range(len(word_tier.intervals) - 1):
        left = word_tier.intervals[i]
        right = word_tier.intervals[i + 1]
        if is_close(left.xmax, right.xmin):
            continue
        # target boundary near the average of the two touching edges
        target = (left.xmax + right.xmin) / 2.0
        # snap to nearest phone boundary
        snap = min(phone_bounds, key=lambda v: abs(v - target))
        # keep within each interval's feasible range to avoid inversion
        snap = max(left.xmin, min(snap, right.xmax))
        # apply to both sides
        left.xmax = snap
        right.xmin = snap
        fixes += 1

    # Ensure tier bounds still consistent
    if word_tier.intervals:
        word_tier.xmin = min(word_tier.xmin, word_tier.intervals[0].xmin)
        word_tier.xmax = max(word_tier.xmax, word_tier.intervals[-1].xmax)
    return fixes


def validate_tier_adjacency(tier: IntervalTier, *, tol: float = 1e-6) -> Tuple[int, List[Tuple[int, float, float]]]:
    mismatches = 0
    details: List[Tuple[int, float, float]] = []
    for i in range(len(tier.intervals) - 1):
        a = tier.intervals[i].xmax
        b = tier.intervals[i + 1].xmin
        if not is_close(a, b, tol=tol):
            mismatches += 1
            details.append((i + 1, a, b))
    return mismatches, details


def process_textgrid(path: str, *, inplace: bool = False, backup: bool = True) -> Tuple[str, dict]:
    tg = parse_textgrid_long(path)

    # Extract phone and word tiers
    phone_tier = next((t for t in tg.tiers if t.name.lower() == "phone"), None)
    word_tier = next((t for t in tg.tiers if t.name.lower() == "word"), None)

    if phone_tier is None or word_tier is None:
        return path, {"status": "skipped", "reason": "missing phone or word tier"}

    # Store original word times to resolve overlaps after phone edits
    original_word_times = [(w.xmin, w.xmax) for w in word_tier.intervals]

    # Align phone tier boundaries
    phone_fixes, phone_changes = align_adjacent_phone_boundaries(phone_tier)

    # Adjust word tier to match updated phone tier
    word_adjusts = adjust_word_tier_to_phone(word_tier, phone_tier, original_word_times)
    # Then enforce adjacency inside word tier, snapping boundaries to nearest phone boundary
    word_boundary_fixes = align_word_boundaries_to_phone(word_tier, phone_tier)

    # Validation
    phone_mismatch_count, phone_mismatches = validate_tier_adjacency(phone_tier)
    word_mismatch_count, word_mismatches = validate_tier_adjacency(word_tier)

    # Serialize and save
    output_text = serialize_textgrid_long(tg)
    if inplace:
        if backup:
            bak = path + ".bak"
            if not os.path.exists(bak):
                with open(bak, "w", encoding="utf-8") as f:
                    f.write(open(path, "r", encoding="utf-8").read())
        with open(path, "w", encoding="utf-8") as f:
            f.write(output_text)
        out_path = path
    else:
        out_path = os.path.splitext(path)[0] + ".fixed.TextGrid"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output_text)

    report = {
        "status": "ok",
        "output": out_path,
        "phone_fixes": phone_fixes,
        "word_adjusts": word_adjusts,
        "word_boundary_fixes": word_boundary_fixes,
        "phone_remaining_mismatches": phone_mismatch_count,
        "word_remaining_mismatches": word_mismatch_count,
        "phone_change_samples": phone_changes[:5],
        "phone_mismatch_samples": phone_mismatches[:5],
        "word_mismatch_samples": word_mismatches[:5],
    }
    return path, report


def iter_textgrid_files(target: str) -> List[str]:
    files: List[str] = []
    if os.path.isdir(target):
        for root, _, filenames in os.walk(target):
            for fn in filenames:
                if fn.lower().endswith(".textgrid"):
                    files.append(os.path.join(root, fn))
    elif os.path.isfile(target) and target.lower().endswith(".textgrid"):
        files.append(target)
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description="Fix TextGrid phone/word tier boundary mismatches and validate.")
    parser.add_argument("target", help="TextGrid file or directory to process")
    parser.add_argument("--inplace", action="store_true", help="Overwrite files in place (create .bak backups)")
    args = parser.parse_args()

    tg_files = iter_textgrid_files(args.target)
    if not tg_files:
        print("No TextGrid files found.")
        return

    total = 0
    any_errors = 0
    for p in tg_files:
        total += 1
        src, rep = process_textgrid(p, inplace=args.inplace, backup=True)
        if rep["status"] != "ok":
            print(f"[SKIP] {src}: {rep.get('reason')}")
            continue
        print(f"[OK] {src}")
        print(f"  -> output: {rep['output']}")
        print(f"  phone_fixes: {rep['phone_fixes']}, word_adjusts: {rep['word_adjusts']}")
        print(f"  remaining mismatches - phone: {rep['phone_remaining_mismatches']}, word: {rep['word_remaining_mismatches']}")
        if rep['phone_remaining_mismatches'] or rep['word_remaining_mismatches']:
            any_errors += 1
            if rep['phone_mismatch_samples']:
                i, a, b = rep['phone_mismatch_samples'][0]
                print(f"    sample phone mismatch at boundary {i}: {a} vs {b}")
            if rep['word_mismatch_samples']:
                i, a, b = rep['word_mismatch_samples'][0]
                print(f"    sample word mismatch at boundary {i}: {a} vs {b}")

    print("")
    print(f"Processed {total} files. Files with remaining mismatches: {any_errors}.")


if __name__ == "__main__":
    main()


