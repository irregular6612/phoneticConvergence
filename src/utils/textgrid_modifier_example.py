"""
TextGrid Modifier 사용 예제

이 스크립트는 textgrid_modifier 모듈의 주요 함수들을 사용하는 방법을 보여줍니다.

Author: Juhyeon Park
Date: 2025-01-08
"""

import os
import sys
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'analysis'))
from textgrid_io import (
    parse_textgrid, 
    find_interval, 
    find_intervals_by_text,
    modify_interval_boundaries, 
    boundary_fix, 
    validate_boundaries,
    write_textgrid
)

def example_usage():
    """TextGrid 수정 함수들의 사용 예제"""
    
    # 예제 파일 경로 (실제 파일 경로로 변경하세요)
    file_path = "data/experiment_data/results-KFA-reviewed/participant_LY023/23_stage2_20250408_1343.TextGrid"
    
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return
    
    print("=== TextGrid Modifier 사용 예제 ===\n")
    
    # 1. TextGrid 파일 파싱
    print("1. TextGrid 파일 파싱")
    print("-" * 40)
    try:
        textgrid_data = parse_textgrid(file_path)
        print(f"파싱 성공: {len(textgrid_data.tiers)}개 tier")
        for tier_name, tier in textgrid_data.tiers.items():
            print(f"  - {tier_name}: {len(tier.intervals)}개 interval")
    except Exception as e:
        print(f"파싱 실패: {e}")
        return
    
    print()
    
    # 2. 특정 interval 찾기
    print("2. 특정 interval 찾기")
    print("-" * 40)
    
    # phone tier에서 "a" 텍스트를 가진 interval 찾기
    interval = find_interval(textgrid_data, "phone", "a")
    if interval:
        print(f"찾은 interval: xmin={interval.xmin:.3f}, xmax={interval.xmax:.3f}, "
              f"text='{interval.text}', number={interval.interval_number}")
    else:
        print("interval을 찾을 수 없습니다.")
    
    # word tier에서 "MILSA" 텍스트를 가진 interval 찾기
    word_interval = find_interval(textgrid_data, "word", "MILSA")
    if word_interval:
        print(f"찾은 word interval: xmin={word_interval.xmin:.3f}, xmax={word_interval.xmax:.3f}, "
              f"text='{word_interval.text}', number={word_interval.interval_number}")
    
    print()
    
    # 3. 여러 interval 찾기
    print("3. 여러 interval 찾기")
    print("-" * 40)
    
    # phone tier에서 "sp" 텍스트를 가진 모든 interval 찾기
    sp_intervals = find_intervals_by_text(textgrid_data, "phone", "sp")
    print(f"'sp' 텍스트를 가진 interval 개수: {len(sp_intervals)}")
    if sp_intervals:
        print("처음 3개:")
        for i, interval in enumerate(sp_intervals[:3]):
            print(f"  {i+1}. xmin={interval.xmin:.3f}, xmax={interval.xmax:.3f}, number={interval.interval_number}")
    
    print()
    
    # 4. Interval boundary 수정
    print("4. Interval boundary 수정")
    print("-" * 40)
    
    # phone tier의 첫 번째 interval로 테스트
    phone_tier = textgrid_data.tiers.get("phone")
    if phone_tier and phone_tier.intervals:
        test_interval = phone_tier.intervals[0]
        print(f"테스트 interval: text='{test_interval.text}', xmin={test_interval.xmin:.3f}, xmax={test_interval.xmax:.3f}")
        
        # xmin을 0.1초 늘리고 xmax를 0.05초 줄이기
        success = modify_interval_boundaries(
            textgrid_data, 
            "phone", 
            test_interval.text, 
            new_xmin=test_interval.xmin + 0.1,
            new_xmax=test_interval.xmax - 0.05,
            interval_number=test_interval.interval_number
        )
        
        if success:
            print("수정 성공!")
            # 수정된 interval 다시 찾기
            modified_interval = find_interval(textgrid_data, "phone", test_interval.text)
            if modified_interval and modified_interval.interval_number == test_interval.interval_number:
                print(f"수정 후: xmin={modified_interval.xmin:.3f}, xmax={modified_interval.xmax:.3f}")
        else:
            print("수정 실패")
    
    print()
    
    # 5. Boundary 무결성 검사
    print("5. Boundary 무결성 검사")
    print("-" * 40)
    
    issues = validate_boundaries(textgrid_data)
    if issues:
        print("발견된 boundary 문제:")
        for tier_name, tier_issues in issues.items():
            print(f"  {tier_name}: {len(tier_issues)}개 문제")
            for interval_num, xmax, next_xmin in tier_issues[:3]:  # 처음 3개만 표시
                print(f"    interval {interval_num}: {xmax:.3f} vs {next_xmin:.3f}")
    else:
        print("모든 boundary가 정상입니다.")
    
    print()
    
    # 6. 수정된 파일 저장
    print("6. 수정된 파일 저장")
    print("-" * 40)
    
    output_path = "modified_example.TextGrid"
    success = write_textgrid(textgrid_data, output_path)
    if success:
        print(f"파일 저장 성공: {output_path}")
    else:
        print("파일 저장 실패")
    
    print()
    
    # 7. 전체 boundary 수정
    print("7. 전체 boundary 수정")
    print("-" * 40)
    
    # 원본 파일을 복사해서 테스트
    test_file = "test_boundary_fix.TextGrid"
    import shutil
    shutil.copy2(file_path, test_file)
    
    success = boundary_fix(test_file, backup=True, inplace=False)
    if success:
        print("Boundary 수정 완료!")
        
        # 수정 후 무결성 검사
        fixed_data = parse_textgrid(test_file.replace('.TextGrid', '_fixed.TextGrid'))
        fixed_issues = validate_boundaries(fixed_data)
        if not fixed_issues:
            print("수정 후 모든 boundary가 정상입니다.")
        else:
            print("수정 후에도 일부 문제가 남아있습니다.")
    else:
        print("Boundary 수정 실패")

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        # 명령행 인수로 파일 경로를 받은 경우
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            print(f"지정된 파일로 예제 실행: {file_path}")
            # 여기서 file_path를 사용하여 예제를 실행할 수 있습니다
        else:
            print(f"파일을 찾을 수 없습니다: {file_path}")
    else:
        # 기본 예제 실행
        example_usage()

if __name__ == "__main__":
    main()
