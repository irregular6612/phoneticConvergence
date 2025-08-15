"""
TextGrid Modifier Module

TextGrid 파일을 수정할 수 있는 함수들을 제공합니다.
- parse: TextGrid 파일 파싱
- find_interval: 특정 tier_name과 text로 interval 찾기
- modify_interval_boundaries: interval의 xmin, xmax 값 수정
- boundary_fix: 전체 boundary 수정

Author: Juhyeon Park
Date: 2025-01-08
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Interval:
    """Interval 정보를 담는 데이터 클래스"""
    xmin: float
    xmax: float
    text: str
    interval_number: int

@dataclass
class Tier:
    """Tier 정보를 담는 데이터 클래스"""
    name: str
    xmin: float
    xmax: float
    intervals: List[Interval]

@dataclass
class TextGridData:
    """TextGrid 전체 데이터를 담는 데이터 클래스"""
    xmin: float
    xmax: float
    tiers: Dict[str, Tier]

def parse_textgrid(file_path: str) -> TextGridData:
    """
    TextGrid 파일을 파싱하여 구조화된 데이터로 변환
    
    Args:
        file_path (str): TextGrid 파일 경로
        
    Returns:
        TextGridData: 파싱된 TextGrid 데이터
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    logger.info(f"TextGrid 파일 파싱 시작: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 파일 정보 파싱
    file_info = {}
    for line in lines:
        line = line.strip()
        if '=' in line and not line.startswith('item') and not line.startswith('intervals'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"')
            file_info[key] = value
    
    xmin = float(file_info.get('xmin', 0))
    xmax = float(file_info.get('xmax', 0))
    
    # Tier 정보 파싱
    tiers = {}
    current_tier = None
    current_intervals = []
    reading_interval = False
    interval_data = {}
    interval_number = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Tier 시작 - "item [1]:" 다음에 "class = "IntervalTier""와 "name = "xxx""가 있는지 확인
        if line.startswith('item [') and i + 2 < len(lines):
            # 다음 두 줄을 확인
            next_line = lines[i + 1].strip()
            next_next_line = lines[i + 2].strip()
            
            if ('class = "IntervalTier"' in next_line and 'name = "' in next_next_line):
                # 이전 tier 저장
                if current_tier is not None:
                    tiers[current_tier] = Tier(
                        name=current_tier,
                        xmin=xmin,
                        xmax=xmax,
                        intervals=current_intervals
                    )
                
                # 새 tier 시작
                current_tier = next_next_line.split('"')[1]
                current_intervals = []
                reading_interval = False
                logger.debug(f"새 tier 발견: {current_tier}")
        
        # Interval 시작
        elif 'intervals [' in line:
            reading_interval = True
            interval_data = {}
            try:
                interval_number = int(line.split('[')[1].split(']')[0])
            except (IndexError, ValueError):
                interval_number = None
        
        # Interval 데이터 읽기
        elif reading_interval and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"')
            interval_data[key] = value
            
            # Interval 완성 (xmin, xmax, text 모두 있으면)
            if 'xmin' in interval_data and 'xmax' in interval_data and 'text' in interval_data:
                start = float(interval_data['xmin'])
                end = float(interval_data['xmax'])
                text = interval_data['text']
                
                current_intervals.append(Interval(
                    xmin=start,
                    xmax=end,
                    text=text,
                    interval_number=interval_number
                ))
                reading_interval = False
                interval_data = {}
        
        i += 1
    
    # 마지막 tier 추가
    if current_tier is not None:
        tiers[current_tier] = Tier(
            name=current_tier,
            xmin=xmin,
            xmax=xmax,
            intervals=current_intervals
        )
    
    logger.info(f"파싱 완료: {len(tiers)}개 tier, 총 {sum(len(t.intervals) for t in tiers.values())}개 interval")
    
    return TextGridData(xmin=xmin, xmax=xmax, tiers=tiers)

def find_interval(textgrid_data: TextGridData, tier_name: str, text: str) -> Optional[Interval]:
    """
    특정 tier_name과 text로 해당 interval을 찾습니다.
    
    Args:
        textgrid_data (TextGridData): 파싱된 TextGrid 데이터
        tier_name (str): 찾을 tier 이름
        text (str): 찾을 텍스트
        
    Returns:
        Optional[Interval]: 찾은 interval 또는 None
    """
    if tier_name not in textgrid_data.tiers:
        logger.warning(f"Tier '{tier_name}'을 찾을 수 없습니다.")
        return None
    
    tier = textgrid_data.tiers[tier_name]
    
    for interval in tier.intervals:
        if interval.text == text:
            logger.info(f"Interval 찾음: tier='{tier_name}', text='{text}', "
                       f"xmin={interval.xmin:.3f}, xmax={interval.xmax:.3f}, "
                       f"interval_number={interval.interval_number}")
            return interval
    
    logger.warning(f"Tier '{tier_name}'에서 text '{text}'를 찾을 수 없습니다.")
    return None

def find_intervals_by_text(textgrid_data: TextGridData, tier_name: str, text: str) -> List[Interval]:
    """
    특정 tier_name과 text로 해당하는 모든 interval을 찾습니다.
    
    Args:
        textgrid_data (TextGridData): 파싱된 TextGrid 데이터
        tier_name (str): 찾을 tier 이름
        text (str): 찾을 텍스트
        
    Returns:
        List[Interval]: 찾은 interval들의 리스트
    """
    if tier_name not in textgrid_data.tiers:
        logger.warning(f"Tier '{tier_name}'을 찾을 수 없습니다.")
        return []
    
    tier = textgrid_data.tiers[tier_name]
    found_intervals = []
    
    for interval in tier.intervals:
        if interval.text == text:
            found_intervals.append(interval)
    
    logger.info(f"Tier '{tier_name}'에서 text '{text}'를 가진 {len(found_intervals)}개 interval을 찾았습니다.")
    return found_intervals

def modify_interval_boundaries(textgrid_data: TextGridData, tier_name: str, 
                              text: str, new_xmin: Optional[float] = None, 
                              new_xmax: Optional[float] = None, 
                              interval_number: Optional[int] = None) -> bool:
    """
    특정 interval의 xmin, xmax 값을 수정합니다 (overwrite 방식).
    
    Args:
        textgrid_data (TextGridData): 수정할 TextGrid 데이터
        tier_name (str): 수정할 tier 이름
        text (str): 수정할 텍스트
        new_xmin (Optional[float]): 새로운 xmin 값
        new_xmax (Optional[float]): 새로운 xmax 값
        interval_number (Optional[int]): 특정 interval 번호 (여러 개가 있을 경우)
        
    Returns:
        bool: 수정 성공 여부
    """
    if tier_name not in textgrid_data.tiers:
        logger.error(f"Tier '{tier_name}'을 찾을 수 없습니다.")
        return False
    
    tier = textgrid_data.tiers[tier_name]
    target_intervals = []
    
    # 조건에 맞는 interval 찾기
    for interval in tier.intervals:
        if interval.text == text:
            if interval_number is None or interval.interval_number == interval_number:
                target_intervals.append(interval)
    
    if not target_intervals:
        logger.error(f"Tier '{tier_name}'에서 text '{text}'를 가진 interval을 찾을 수 없습니다.")
        return False
    
    if len(target_intervals) > 1 and interval_number is None:
        logger.warning(f"여러 개의 interval이 발견되었습니다. interval_number를 지정하거나 find_intervals_by_text를 사용하세요.")
        return False
    
    # 수정 실행
    modified_count = 0
    for interval in target_intervals:
        old_xmin, old_xmax = interval.xmin, interval.xmax
        
        if new_xmin is not None:
            interval.xmin = new_xmin
        if new_xmax is not None:
            interval.xmax = new_xmax
        
        logger.info(f"Interval 수정 완료: tier='{tier_name}', text='{text}', "
                   f"interval_number={interval.interval_number}")
        logger.info(f"  xmin: {old_xmin:.3f} -> {interval.xmin:.3f}")
        logger.info(f"  xmax: {old_xmax:.3f} -> {interval.xmax:.3f}")
        modified_count += 1
    
    # 수정 후 tier의 xmin, xmax 자동 업데이트
    if tier.intervals:
        sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
        old_tier_xmin, old_tier_xmax = tier.xmin, tier.xmax
        tier.xmin = sorted_intervals[0].xmin
        tier.xmax = sorted_intervals[-1].xmax
        
        if old_tier_xmin != tier.xmin or old_tier_xmax != tier.xmax:
            logger.info(f"Tier '{tier_name}' 범위 자동 업데이트:")
            logger.info(f"  xmin: {old_tier_xmin:.3f} -> {tier.xmin:.3f}")
            logger.info(f"  xmax: {old_tier_xmax:.3f} -> {tier.xmax:.3f}")
    
    # 전체 파일의 xmin, xmax 자동 업데이트
    all_xmins = []
    all_xmaxs = []
    for t in textgrid_data.tiers.values():
        if t.intervals:
            sorted_intervals = sorted(t.intervals, key=lambda x: x.xmin)
            all_xmins.append(sorted_intervals[0].xmin)
            all_xmaxs.append(sorted_intervals[-1].xmax)
    
    if all_xmins and all_xmaxs:
        old_file_xmin, old_file_xmax = textgrid_data.xmin, textgrid_data.xmax
        textgrid_data.xmin = min(all_xmins)
        textgrid_data.xmax = max(all_xmaxs)
        
        if old_file_xmin != textgrid_data.xmin or old_file_xmax != textgrid_data.xmax:
            logger.info(f"파일 전체 범위 자동 업데이트:")
            logger.info(f"  xmin: {old_file_xmin:.3f} -> {textgrid_data.xmin:.3f}")
            logger.info(f"  xmax: {old_file_xmax:.3f} -> {textgrid_data.xmax:.3f}")
    
    logger.info(f"총 {modified_count}개 interval 수정 완료")
    return True

def write_textgrid(textgrid_data: TextGridData, output_path: str) -> bool:
    """
    TextGrid 데이터를 파일로 저장합니다.
    
    Args:
        textgrid_data (TextGridData): 저장할 TextGrid 데이터
        output_path (str): 출력 파일 경로
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        # 전체 파일의 xmin, xmax 계산 (모든 tier의 최소/최대값)
        all_xmins = []
        all_xmaxs = []
        for tier in textgrid_data.tiers.values():
            if tier.intervals:
                sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
                all_xmins.append(sorted_intervals[0].xmin)
                all_xmaxs.append(sorted_intervals[-1].xmax)
        
        if all_xmins and all_xmaxs:
            file_xmin = min(all_xmins)
            file_xmax = max(all_xmaxs)
        else:
            file_xmin = textgrid_data.xmin
            file_xmax = textgrid_data.xmax
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 파일 헤더
            f.write('File type = "ooTextFile"\n')
            f.write('Object class = "TextGrid"\n\n')
            
            # 파일 정보
            f.write(f'xmin = {file_xmin}\n')
            f.write(f'xmax = {file_xmax}\n')
            f.write('tiers? <exists>\n')
            f.write(f'size = {len(textgrid_data.tiers)}\n')
            f.write('item []:\n')
            
            # Tier 정보
            for tier_idx, (tier_name, tier) in enumerate(textgrid_data.tiers.items(), 1):
                # 각 tier의 xmin, xmax 계산 (해당 tier의 첫 번째/마지막 interval 기준)
                if tier.intervals:
                    sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
                    tier_xmin = sorted_intervals[0].xmin
                    tier_xmax = sorted_intervals[-1].xmax
                else:
                    tier_xmin = tier.xmin
                    tier_xmax = tier.xmax
                
                f.write(f'    item [{tier_idx}]:\n')
                f.write('        class = "IntervalTier"\n')
                f.write(f'        name = "{tier.name}"\n')
                f.write(f'        xmin = {tier_xmin}\n')
                f.write(f'        xmax = {tier_xmax}\n')
                f.write(f'        intervals: size = {len(tier.intervals)}\n')
                
                # Interval 정보
                for interval_idx, interval in enumerate(tier.intervals, 1):
                    f.write(f'        intervals [{interval_idx}]:\n')
                    f.write(f'            xmin = {interval.xmin}\n')
                    f.write(f'            xmax = {interval.xmax}\n')
                    f.write(f'            text = "{interval.text}"\n')
        
        logger.info(f"TextGrid 파일 저장 완료: {output_path}")
        logger.info(f"파일 범위: {file_xmin:.3f} ~ {file_xmax:.3f}")
        return True
        
    except Exception as e:
        logger.error(f"파일 저장 실패: {e}")
        return False

def boundary_fix(file_path: str, output_path: Optional[str] = None, 
                backup: bool = True, inplace: bool = False) -> bool:
    """
    TextGrid 파일의 boundary 문제를 수정합니다.
    
    Args:
        file_path (str): 수정할 TextGrid 파일 경로
        output_path (Optional[str]): 출력 파일 경로 (None이면 자동 생성)
        backup (bool): 백업 파일 생성 여부
        inplace (bool): 원본 파일에 덮어쓰기 여부
        
    Returns:
        bool: 수정 성공 여부
    """
    logger.info(f"Boundary 수정 시작: {file_path}")
    
    # 백업 생성
    if backup and not inplace:
        backup_path = file_path + '.backup'
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"백업 파일 생성: {backup_path}")
        except Exception as e:
            logger.error(f"백업 생성 실패: {e}")
            return False
    
    # 파일 파싱
    try:
        textgrid_data = parse_textgrid(file_path)
    except Exception as e:
        logger.error(f"파일 파싱 실패: {e}")
        return False
    
    # 각 tier별로 boundary 수정
    total_fixes = 0
    for tier_name, tier in textgrid_data.tiers.items():
        if not tier.intervals:
            continue
        
        logger.info(f"Tier '{tier_name}' boundary 수정 중...")
        tier_fixes = 0
        
        # Interval들을 시작 시간 기준으로 정렬
        sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
        
        for i in range(len(sorted_intervals) - 1):
            current = sorted_intervals[i]
            next_interval = sorted_intervals[i + 1]
            
            # 경계 불일치 검사 및 수정
            if abs(current.xmax - next_interval.xmin) > 1e-6:
                old_current_xmax = current.xmax
                old_next_xmin = next_interval.xmin
                
                # 경계를 평균값으로 조정
                new_boundary = (current.xmax + next_interval.xmin) / 2.0
                current.xmax = new_boundary
                next_interval.xmin = new_boundary
                
                logger.info(f"  Boundary 수정: interval {current.interval_number} ~ {next_interval.interval_number}")
                logger.info(f"    {old_current_xmax:.3f} ~ {old_next_xmin:.3f} -> {new_boundary:.3f}")
                tier_fixes += 1
        
        # 수정 후 tier의 xmin, xmax 자동 업데이트
        if tier.intervals:
            old_tier_xmin, old_tier_xmax = tier.xmin, tier.xmax
            tier.xmin = sorted_intervals[0].xmin
            tier.xmax = sorted_intervals[-1].xmax
            
            if old_tier_xmin != tier.xmin or old_tier_xmax != tier.xmax:
                logger.info(f"  Tier '{tier_name}' 범위 자동 업데이트:")
                logger.info(f"    xmin: {old_tier_xmin:.3f} -> {tier.xmin:.3f}")
                logger.info(f"    xmax: {old_tier_xmax:.3f} -> {tier.xmax:.3f}")
        
        total_fixes += tier_fixes
        logger.info(f"Tier '{tier_name}': {tier_fixes}개 boundary 수정 완료")
    
    # 전체 파일의 xmin, xmax 자동 업데이트
    all_xmins = []
    all_xmaxs = []
    for tier in textgrid_data.tiers.values():
        if tier.intervals:
            sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
            all_xmins.append(sorted_intervals[0].xmin)
            all_xmaxs.append(sorted_intervals[-1].xmax)
    
    if all_xmins and all_xmaxs:
        old_file_xmin, old_file_xmax = textgrid_data.xmin, textgrid_data.xmax
        textgrid_data.xmin = min(all_xmins)
        textgrid_data.xmax = max(all_xmaxs)
        
        if old_file_xmin != textgrid_data.xmin or old_file_xmax != textgrid_data.xmax:
            logger.info(f"파일 전체 범위 자동 업데이트:")
            logger.info(f"  xmin: {old_file_xmin:.3f} -> {textgrid_data.xmin:.3f}")
            logger.info(f"  xmax: {old_file_xmax:.3f} -> {textgrid_data.xmax:.3f}")
    
    # 출력 파일 경로 결정
    if inplace:
        final_output_path = file_path
    elif output_path:
        final_output_path = output_path
    else:
        base_name = os.path.splitext(file_path)[0]
        final_output_path = f"{base_name}_fixed.TextGrid"
    
    # 수정된 파일 저장
    success = write_textgrid(textgrid_data, final_output_path)
    
    if success:
        logger.info(f"Boundary 수정 완료: {total_fixes}개 수정, 출력: {final_output_path}")
    else:
        logger.error("Boundary 수정 실패")
    
    return success

def validate_boundaries(textgrid_data: TextGridData, tolerance: float = 1e-6) -> Dict[str, List[Tuple[int, float, float]]]:
    """
    TextGrid 데이터의 boundary 무결성을 검사합니다.
    
    Args:
        textgrid_data (TextGridData): 검사할 TextGrid 데이터
        tolerance (float): 허용 오차
        
    Returns:
        Dict[str, List[Tuple[int, float, float]]]: 각 tier별 문제점들
    """
    issues = {}
    
    for tier_name, tier in textgrid_data.tiers.items():
        if not tier.intervals:
            continue
        
        tier_issues = []
        sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
        
        for i in range(len(sorted_intervals) - 1):
            current = sorted_intervals[i]
            next_interval = sorted_intervals[i + 1]
            
            if abs(current.xmax - next_interval.xmin) > tolerance:
                tier_issues.append((
                    current.interval_number,
                    current.xmax,
                    next_interval.xmin
                ))
        
        if tier_issues:
            issues[tier_name] = tier_issues
    
    return issues
