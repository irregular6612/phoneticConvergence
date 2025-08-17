"""
Word Tier Generator 테스트 스크립트

사용 예시를 보여주는 테스트 스크립트입니다.
"""

import os
import sys
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from word_tier_generator import WordTierGenerator

def test_word_tier_generation():
    """
    Word tier 생성 테스트
    """
    # 테스트할 TextGrid 파일 경로 (실제 파일 경로로 변경하세요)
    textgrid_path = "path/to/your/textgrid/file.TextGrid"
    
    if not os.path.exists(textgrid_path):
        print(f"❌ 파일을 찾을 수 없습니다: {textgrid_path}")
        print("실제 TextGrid 파일 경로로 변경해주세요.")
        return
    
    print(f"📁 TextGrid 파일: {textgrid_path}")
    
    # WordTierGenerator 생성
    generator = WordTierGenerator(textgrid_path)
    
    # 1. 기존 TextGrid에 Word tier 추가
    print("\n🔧 기존 TextGrid에 Word tier 추가 중...")
    success = generator.add_word_tier_to_textgrid()
    
    if success:
        print("✅ Word tier가 기존 TextGrid에 추가되었습니다.")
    else:
        print("❌ Word tier 추가에 실패했습니다.")
    
    # 2. Word tier만 포함하는 새로운 TextGrid 생성
    print("\n🆕 Word tier만 포함하는 새로운 TextGrid 생성 중...")
    success = generator.create_new_textgrid_with_word_tier()
    
    if success:
        print("✅ Word tier만 포함한 새로운 TextGrid가 생성되었습니다.")
    else:
        print("❌ 새로운 TextGrid 생성에 실패했습니다.")

def show_usage_examples():
    """
    사용법 예시 출력
    """
    print("📖 Word Tier Generator 사용법:")
    print()
    print("1. 명령줄에서 실행:")
    print("   python word_tier_generator.py your_file.TextGrid")
    print("   python word_tier_generator.py your_file.TextGrid --output new_file.TextGrid")
    print("   python word_tier_generator.py your_file.TextGrid --word-only")
    print("   python word_tier_generator.py your_file.TextGrid --keep-existing")
    print("   python word_tier_generator.py your_file.TextGrid --verbose")
    print()
    print("2. Python 코드에서 사용:")
    print("   from word_tier_generator import WordTierGenerator")
    print("   generator = WordTierGenerator('your_file.TextGrid', verbose=True)")
    print("   generator.add_word_tier_to_textgrid()")
    print()

if __name__ == "__main__":
    print("🚀 Word Tier Generator 테스트")
    print("=" * 50)
    
    show_usage_examples()
    
    # 실제 파일이 있으면 테스트 실행
    # test_word_tier_generation()
