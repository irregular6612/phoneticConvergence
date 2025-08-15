"""
TextGrid I/O 통합 모듈 사용 예제

통합된 TextGridReader 클래스를 사용하는 방법을 보여줍니다.

Author: Juhyeon Park
Date: 2025-01-08
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'analysis'))
from textgrid_io import TextGridReader, Interval, Tier, TextGridData

def example_usage():
    """TextGridReader 클래스 사용 예제"""
    
    # 예제 파일 경로
    file_path = "data/experiment_data/results-KFA-reviewed/participant_LY023/23_stage2_20250408_1343.TextGrid"
    
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return
    
    print("=== TextGridReader 클래스 사용 예제 ===\n")
    
    # 1. TextGridReader 초기화 및 파일 읽기
    print("1. TextGridReader 초기화 및 파일 읽기")
    print("-" * 50)
    
    # 자동으로 파일을 읽어서 초기화
    reader = TextGridReader(file_path)
    print(f"파일 로드 완료: {len(reader.get_tier_names())}개 tier")
    for tier_name in reader.get_tier_names():
        intervals = reader.get_intervals_by_tier(tier_name)
        print(f"  - {tier_name}: {len(intervals)}개 interval")
    
    print()
    
    # 2. 특정 interval 찾기
    print("2. 특정 interval 찾기")
    print("-" * 50)
    
    # phone tier에서 "a" 텍스트를 가진 interval 찾기
    interval = reader.find_interval("phone", "a")
    if interval:
        print(f"찾은 interval: xmin={interval.xmin:.3f}, xmax={interval.xmax:.3f}, "
              f"text='{interval.text}', number={interval.interval_number}")
    else:
        print("interval을 찾을 수 없습니다.")
    
    # word tier에서 "MILSA" 텍스트를 가진 interval 찾기
    word_interval = reader.find_interval("word", "MILSA")
    if word_interval:
        print(f"찾은 word interval: xmin={word_interval.xmin:.3f}, xmax={word_interval.xmax:.3f}, "
              f"text='{word_interval.text}', number={word_interval.interval_number}")
    
    print()
    
    # 3. 여러 interval 찾기
    print("3. 여러 interval 찾기")
    print("-" * 50)
    
    # phone tier에서 "sp" 텍스트를 가진 모든 interval 찾기
    sp_intervals = reader.find_intervals_by_text("phone", "sp")
    print(f"'sp' 텍스트를 가진 interval 개수: {len(sp_intervals)}")
    if sp_intervals:
        print("처음 3개:")
        for i, interval in enumerate(sp_intervals[:3]):
            print(f"  {i+1}. xmin={interval.xmin:.3f}, xmax={interval.xmax:.3f}, number={interval.interval_number}")
    
    print()
    
    # 4. Interval boundary 수정
    print("4. Interval boundary 수정")
    print("-" * 50)
    
    # phone tier의 첫 번째 interval로 테스트
    phone_intervals = reader.get_intervals_by_tier("phone")
    if phone_intervals:
        test_interval = phone_intervals[0]
        print(f"테스트 interval: text='{test_interval.text}', xmin={test_interval.xmin:.3f}, xmax={test_interval.xmax:.3f}")
        
        # xmin을 0.1초 늘리고 xmax를 0.05초 줄이기
        success = reader.modify_interval_boundaries(
            "phone", 
            test_interval.text, 
            new_xmin=test_interval.xmin + 0.1,
            new_xmax=test_interval.xmax - 0.05,
            interval_number=test_interval.interval_number
        )
        
        if success:
            print("수정 성공!")
            # 수정된 interval 다시 찾기
            modified_interval = reader.find_interval("phone", test_interval.text)
            if modified_interval and modified_interval.interval_number == test_interval.interval_number:
                print(f"수정 후: xmin={modified_interval.xmin:.3f}, xmax={modified_interval.xmax:.3f}")
        else:
            print("수정 실패")
    
    print()
    
    # 5. Boundary 무결성 검사
    print("5. Boundary 무결성 검사")
    print("-" * 50)
    
    issues = reader.validate_boundaries()
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
    print("-" * 50)
    
    output_path = "modified_class_example.TextGrid"
    success = reader.write(output_path)
    if success:
        print(f"파일 저장 성공: {output_path}")
    else:
        print("파일 저장 실패")
    
    print()
    
    # 7. 전체 boundary 수정
    print("7. 전체 boundary 수정")
    print("-" * 50)
    
    # 원본 파일을 복사해서 테스트
    test_file = "test_class_boundary_fix.TextGrid"
    import shutil
    shutil.copy2(file_path, test_file)
    
    # 새로운 reader 인스턴스 생성
    test_reader = TextGridReader(test_file)
    success = test_reader.boundary_fix(backup=True, inplace=False)
    if success:
        print("Boundary 수정 완료!")
        
        # 수정 후 무결성 검사
        fixed_issues = test_reader.validate_boundaries()
        if not fixed_issues:
            print("수정 후 모든 boundary가 정상입니다.")
        else:
            print("수정 후에도 일부 문제가 남아있습니다.")
    else:
        print("Boundary 수정 실패")
    
    print()
    
    # 8. 클래스 메서드 활용 예제
    print("8. 클래스 메서드 활용 예제")
    print("-" * 50)
    
    print(f"총 지속 시간: {reader.get_total_duration():.3f}초")
    print(f"Tier 이름들: {reader.get_tier_names()}")
    
    # 특정 tier의 모든 interval 정보 출력
    phone_tier_intervals = reader.get_intervals_by_tier("phone")
    print(f"Phone tier의 첫 5개 interval:")
    for i, interval in enumerate(phone_tier_intervals[:5]):
        print(f"  {i+1}. [{interval.xmin:.3f}-{interval.xmax:.3f}] '{interval.text}' (번호: {interval.interval_number})")

def advanced_usage():
    """고급 사용법 예제"""
    print("\n=== 고급 사용법 예제 ===\n")
    
    file_path = "data/experiment_data/results-KFA-reviewed/participant_LY023/23_stage2_20250408_1343.TextGrid"
    
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return
    
    # 1. 여러 interval을 한 번에 수정
    print("1. 여러 interval을 한 번에 수정")
    print("-" * 40)
    
    reader = TextGridReader(file_path)
    
    # "sp" 텍스트를 가진 모든 interval 찾기
    sp_intervals = reader.find_intervals_by_text("phone", "sp")
    print(f"수정 전 'sp' interval 개수: {len(sp_intervals)}")
    
    # 첫 번째 "sp" interval만 수정
    if sp_intervals:
        first_sp = sp_intervals[0]
        print(f"첫 번째 'sp' interval 수정: {first_sp.xmin:.3f} -> {first_sp.xmin + 0.05:.3f}")
        
        reader.modify_interval_boundaries(
            "phone", "sp", 
            new_xmin=first_sp.xmin + 0.05,
            interval_number=first_sp.interval_number
        )
    
    print()
    
    # 2. Boundary 무결성 검사 및 자동 수정
    print("2. Boundary 무결성 검사 및 자동 수정")
    print("-" * 40)
    
    # 무결성 검사
    issues = reader.validate_boundaries()
    if issues:
        print(f"발견된 문제: {sum(len(issues_list) for issues_list in issues.values())}개")
        
        # 자동 수정
        print("자동 수정 시작...")
        success = reader.boundary_fix(backup=True, inplace=False)
        if success:
            print("자동 수정 완료!")
            
            # 수정 후 재검사
            fixed_issues = reader.validate_boundaries()
            if not fixed_issues:
                print("모든 문제가 해결되었습니다!")
            else:
                print(f"수정 후에도 {sum(len(issues_list) for issues_list in fixed_issues.values())}개 문제가 남아있습니다.")
    else:
        print("모든 boundary가 정상입니다.")
    
    print()
    
    # 3. 파일 저장 및 백업
    print("3. 파일 저장 및 백업")
    print("-" * 40)
    
    # 원본 파일 백업
    backup_path = file_path + ".backup"
    import shutil
    shutil.copy2(file_path, backup_path)
    print(f"원본 파일 백업: {backup_path}")
    
    # 수정된 파일 저장
    modified_path = "advanced_modified.TextGrid"
    success = reader.write(modified_path)
    if success:
        print(f"수정된 파일 저장: {modified_path}")
    else:
        print("파일 저장 실패")

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
        advanced_usage()

if __name__ == "__main__":
    main()
