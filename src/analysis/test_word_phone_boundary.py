"""
Word-Phone Boundary Checker 테스트 스크립트

사용 예시를 보여주는 테스트 파일입니다.
"""

from word_phone_boundary_checker import WordPhoneBoundaryChecker
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_word_phone_boundary_checker():
    """
    WordPhoneBoundaryChecker 테스트 함수
    """
    # TextGrid 파일 경로
    textgrid_path = "/Users/bagjuhyeon/Documents/WorkSpace/phoneticConvergence/data/experiment_data/results-KFA-reviewed/participant_LY002/02_stage2_20250404_1349.TextGrid"
    
    try:
        print("🔍 Word-Phone Boundary Checker 테스트 시작")
        print("=" * 60)
        
        # Checker 초기화
        checker = WordPhoneBoundaryChecker(textgrid_path)
        
        # 1. word-phone 매핑 정보 확인
        print("\n1️⃣ Word-Phone 매핑 정보:")
        word_phone_mapping = checker.get_word_phone_mapping()
        print(f"총 {len(word_phone_mapping)}개의 word가 phone과 매핑되었습니다.")
        
        # 처음 몇 개의 매핑 예시 출력
        for i, (word, phones) in enumerate(list(word_phone_mapping.items())[:3]):
            print(f"  '{word}': {len(phones)}개 phone")
            for phone in phones:  # 모든 phone 출력
                print(f"    - {phone.text}: {phone.xmin:.3f} ~ {phone.xmax:.3f}")
            print()
        
        # 2. 경계 불일치 확인
        print("\n2️⃣ 경계 불일치 확인:")
        boundary_issues = checker.check_word_phone_boundaries()
        checker.print_boundary_issues(boundary_issues)
        
        # 3. 요약 정보 출력
        print("\n3️⃣ 요약 정보:")
        summary = checker.get_summary()
        print(f"📊 총 word 수: {summary['total_words']}")
        print(f"📊 경계 문제가 있는 word 수: {summary['words_with_issues']}")
        print(f"📊 문제 비율: {summary['issue_percentage']:.1f}%")
        
        # 4. 경계 수정 (선택적)
        if boundary_issues:
            print(f"\n4️⃣ 경계 수정 옵션:")
            print("경계를 수정하려면 다음 중 하나를 선택하세요:")
            print("  a) 새 파일로 저장: checker.fix_word_boundaries(backup=True, inplace=False)")
            print("  b) 원본 파일 덮어쓰기: checker.fix_word_boundaries(backup=True, inplace=True)")
            print("  c) 특정 경로에 저장: checker.fix_word_boundaries(output_path='path/to/output.TextGrid')")
            
            # 자동으로 새 파일로 저장 (테스트용)
            print(f"\n🔧 테스트를 위해 새 파일로 저장합니다...")
            success = checker.fix_word_boundaries(backup=True, inplace=False)
            if success:
                print("✅ 경계 수정 완료!")
            else:
                print("❌ 경계 수정 실패!")
        else:
            print("✅ 모든 경계가 정상이므로 수정이 필요하지 않습니다.")
        
        print("\n" + "=" * 60)
        print("🎉 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_word_phone_boundary_checker()
