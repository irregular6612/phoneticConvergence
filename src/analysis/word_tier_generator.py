"""
Word Tier Generator

Phone tier의 'sp' 토큰을 기준으로 단어 구간을 찾아서 새로운 Word tier를 생성합니다.
- phone tier에서 'sp' 토큰을 찾아서 단어 경계를 결정
- sp 전후의 phone들을 하나의 단어로 묶기
- 파일 시작/끝 부분의 sp 처리
- 새로운 Word tier 생성 및 저장

Author: Juhyeon Park
Date: 2025-01-27
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import logging

# 현재 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from textgrid_io import TextGridReader, Interval, Tier, TextGridData

# Configure logging
logger = logging.getLogger(__name__)

class WordTierGenerator:
    """
    Phone tier를 기반으로 Word tier를 생성하는 클래스
    """
    
    def __init__(self, textgrid_path: str, verbose: bool = False):
        """
        WordTierGenerator 초기화
        
        Args:
            textgrid_path (str): TextGrid 파일 경로
            verbose (bool): 상세 출력 여부 (기본값: False)
        """
        self.textgrid_path = textgrid_path
        self.verbose = verbose
        
        # Logging 설정
        if verbose:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        else:
            # verbose가 False일 때는 모든 로그를 완전히 비활성화
            logging.disable(logging.CRITICAL)
        
        self.reader = TextGridReader(textgrid_path, verbose=verbose)
        self.phone_tier_name = None
        self.word_tier_name = "word"
        
    def find_phone_tier(self) -> Optional[str]:
        """
        Phone tier 이름을 찾습니다.
        
        Returns:
            Optional[str]: Phone tier 이름 또는 None
        """
        tier_names = self.reader.get_tier_names()
        
        # 일반적인 phone tier 이름들
        phone_tier_candidates = ['phone', 'phones', 'phoneme', 'phonemes', 'PHONE', 'PHONES']
        
        for candidate in phone_tier_candidates:
            if candidate in tier_names:
                self.phone_tier_name = candidate
                if self.verbose:
                    logger.info(f"Phone tier 발견: {candidate}")
                return candidate
        
        # 정확히 일치하는 이름이 없으면 첫 번째 tier 사용
        if tier_names:
            self.phone_tier_name = tier_names[0]
            if self.verbose:
                logger.warning(f"Phone tier를 찾을 수 없어 첫 번째 tier 사용: {tier_names[0]}")
            return tier_names[0]
        
        if self.verbose:
            logger.error("사용 가능한 tier가 없습니다.")
        return None
    
    def extract_word_intervals(self) -> List[Interval]:
        """
        Phone tier에서 모든 interval을 단어로 처리합니다.
        - 'sp' 토큰은 'sp'라는 단어로 처리
        - 다른 phone들은 하나의 단어로 묶기
        
        Returns:
            List[Interval]: 생성된 단어 interval들
        """
        if not self.phone_tier_name:
            if self.verbose:
                logger.error("Phone tier가 설정되지 않았습니다.")
            return []
        
        phone_intervals = self.reader.get_intervals_by_tier(self.phone_tier_name)
        if not phone_intervals:
            if self.verbose:
                logger.error(f"Phone tier '{self.phone_tier_name}'에 interval이 없습니다.")
            return []
        
        if self.verbose:
            logger.info(f"Phone intervals 분석 시작: {len(phone_intervals)}개")
        
        word_intervals = []
        current_word_start = None
        current_word_phones = []
        word_number = 1
        
        for i, phone_interval in enumerate(phone_intervals):
            phone_text = phone_interval.text.strip()
            
            # 'sp' 토큰인 경우 - 별도 단어로 처리
            if phone_text == 'sp':
                # 이전에 누적된 단어가 있으면 먼저 처리
                if current_word_start is not None and current_word_phones:
                    word_text = ''.join(current_word_phones)
                    word_intervals.append(Interval(
                        xmin=current_word_start,
                        xmax=phone_interval.xmin,
                        text=word_text,
                        interval_number=word_number
                    ))
                    if self.verbose:
                        logger.debug(f"단어 {word_number}: '{word_text}' ({current_word_start:.3f} ~ {phone_interval.xmin:.3f})")
                    word_number += 1
                    current_word_start = None
                    current_word_phones = []
                
                # sp를 별도 단어로 추가
                word_intervals.append(Interval(
                    xmin=phone_interval.xmin,
                    xmax=phone_interval.xmax,
                    text='sp',
                    interval_number=word_number
                ))
                if self.verbose:
                    logger.debug(f"단어 {word_number}: 'sp' ({phone_interval.xmin:.3f} ~ {phone_interval.xmax:.3f})")
                word_number += 1
            
            # 'sp' 토큰이 아닌 경우 (실제 음소)
            else:
                if current_word_start is None:
                    # 단어 시작
                    current_word_start = phone_interval.xmin
                current_word_phones.append(phone_text)
        
        # 마지막에 남은 단어 처리
        if current_word_start is not None and current_word_phones:
            word_text = ''.join(current_word_phones)
            word_intervals.append(Interval(
                xmin=current_word_start,
                xmax=phone_intervals[-1].xmax,
                text=word_text,
                interval_number=word_number
            ))
            if self.verbose:
                logger.debug(f"단어 {word_number}: '{word_text}' ({current_word_start:.3f} ~ {phone_intervals[-1].xmax:.3f})")
        
        if self.verbose:
            logger.info(f"단어 구간 추출 완료: {len(word_intervals)}개 단어")
        return word_intervals
    
    def create_word_tier(self) -> Optional[Tier]:
        """
        추출된 단어 구간으로 Word tier를 생성합니다.
        
        Returns:
            Optional[Tier]: 생성된 Word tier 또는 None
        """
        word_intervals = self.extract_word_intervals()
        if not word_intervals:
            if self.verbose:
                logger.error("단어 구간을 추출할 수 없습니다.")
            return None
        
        # 전체 파일 범위 계산
        file_xmin = min(interval.xmin for interval in word_intervals)
        file_xmax = max(interval.xmax for interval in word_intervals)
        
        word_tier = Tier(
            name=self.word_tier_name,
            xmin=file_xmin,
            xmax=file_xmax,
            intervals=word_intervals
        )
        
        if self.verbose:
            logger.info(f"Word tier 생성 완료: {len(word_intervals)}개 단어")
            logger.info(f"Tier 범위: {file_xmin:.3f} ~ {file_xmax:.3f}")
        
        return word_tier
    
    def add_word_tier_to_textgrid(self, output_path: Optional[str] = None, remove_existing: bool = True, inplace: bool = False) -> bool:
        """
        기존 TextGrid에 Word tier를 추가합니다.
        
        Args:
            output_path (Optional[str]): 출력 파일 경로 (None이면 자동 생성)
            remove_existing (bool): 기존 word tier 삭제 여부 (기본값: True)
            
        Returns:
            bool: 성공 여부
        """
        # Phone tier 찾기
        if not self.find_phone_tier():
            if self.verbose:
                logger.error("Phone tier를 찾을 수 없습니다.")
            return False
        
        # Word tier 생성
        word_tier = self.create_word_tier()
        if not word_tier:
            return False
        
        # 기존 TextGrid 데이터에 Word tier 추가
        if self.reader.textgrid_data:
            # 기존 Word tier 관련 tier들 삭제
            if remove_existing:
                word_related_tiers = ['word', 'words', 'WORD', 'WORDS', 'Word', 'Words']
                for tier_name in word_related_tiers:
                    if tier_name in self.reader.textgrid_data.tiers:
                        if self.verbose:
                            logger.info(f"기존 '{tier_name}' tier를 제거합니다.")
                        del self.reader.textgrid_data.tiers[tier_name]
            
            # 새로운 Word tier 추가
            self.reader.textgrid_data.tiers[self.word_tier_name] = word_tier
            
            # 출력 파일 경로 결정
            if output_path is None:
                base_name = os.path.splitext(self.textgrid_path)[0]
                if inplace == True:
                    output_path = f"{base_name}.TextGrid"
                else:
                    output_path = f"{base_name}_with_word.TextGrid"
            
            # 파일 저장
            success = self.reader.write(output_path)
            
            if success:
                if self.verbose:
                    logger.info(f"Word tier가 추가된 TextGrid 저장 완료: {output_path}")
                return True
            else:
                if self.verbose:
                    logger.error("파일 저장에 실패했습니다.")
                return False
        else:
            if self.verbose:
                logger.error("TextGrid 데이터가 로드되지 않았습니다.")
            return False
    
    def create_new_textgrid_with_word_tier(self, output_path: Optional[str] = None) -> bool:
        """
        Word tier만 포함하는 새로운 TextGrid를 생성합니다.
        
        Args:
            output_path (Optional[str]): 출력 파일 경로 (None이면 자동 생성)
            
        Returns:
            bool: 성공 여부
        """
        # Phone tier 찾기
        if not self.find_phone_tier():
            if self.verbose:
                logger.error("Phone tier를 찾을 수 없습니다.")
            return False
        
        # Word tier 생성
        word_tier = self.create_word_tier()
        if not word_tier:
            if self.verbose:
                logger.error("Word tier 생성에 실패했습니다.")
            return False
        
        # 새로운 TextGrid 데이터 생성
        new_textgrid_data = TextGridData(
            xmin=word_tier.xmin,
            xmax=word_tier.xmax,
            tiers={self.word_tier_name: word_tier}
        )
        
        # 임시로 reader의 데이터를 교체
        original_data = self.reader.textgrid_data
        self.reader.textgrid_data = new_textgrid_data
        
        # 출력 파일 경로 결정
        if output_path is None:
            base_name = os.path.splitext(self.textgrid_path)[0]
            output_path = f"{base_name}_word_only.TextGrid"
        
        # 파일 저장
        success = self.reader.write(output_path)
        
        # 원본 데이터 복원
        self.reader.textgrid_data = original_data
        
        if success:
            if self.verbose:
                logger.info(f"Word tier만 포함한 TextGrid 생성 완료: {output_path}")
            return True
        else:
            if self.verbose:
                logger.error("파일 저장에 실패했습니다.")
            return False

def main():
    """
    메인 실행 함수
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Phone tier를 기반으로 Word tier를 생성합니다.')
    parser.add_argument('textgrid_path', help='TextGrid 파일 경로')
    parser.add_argument('--output', '-o', help='출력 파일 경로')
    parser.add_argument('--word-only', action='store_true', 
                       help='Word tier만 포함하는 새로운 TextGrid 생성')
    parser.add_argument('--keep-existing', action='store_true',
                       help='기존 word tier를 유지 (기본값: 삭제)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='상세 출력 (기본값: False)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.textgrid_path):
        print(f"❌ 파일을 찾을 수 없습니다: {args.textgrid_path}")
        return
    
    # WordTierGenerator 생성
    generator = WordTierGenerator(args.textgrid_path, verbose=args.verbose)
    
    try:
        if args.word_only:
            success = generator.create_new_textgrid_with_word_tier(args.output)
        else:
            success = generator.add_word_tier_to_textgrid(args.output, remove_existing=not args.keep_existing)
        
        if success:
            print("🎉 Word tier 생성이 완료되었습니다!")
        else:
            print("❌ Word tier 생성에 실패했습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
