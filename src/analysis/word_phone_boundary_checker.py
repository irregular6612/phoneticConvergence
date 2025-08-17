"""
Word-Phone Boundary Checker

TextGrid 파일의 word tier와 phone tier 간의 경계 매칭을 확인하고 수정하는 모듈입니다.
- check_word_phone_boundaries: word와 phone tier 간 경계 불일치 확인
- fix_word_boundaries: word tier의 경계를 phone tier에 맞춰 수정

Author: Juhyeon Park
Date: 2025-01-27
"""

import os
import logging
from typing import List, Tuple, Dict, Optional
from textgrid_io import TextGridReader, Interval

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WordPhoneBoundaryChecker:
    """
    Word와 Phone tier 간의 경계 매칭을 확인하고 수정하는 클래스
    """
    
    def __init__(self, textgrid_path: str):
        """
        WordPhoneBoundaryChecker 초기화
        
        Args:
            textgrid_path (str): TextGrid 파일 경로
        """
        self.textgrid_path = textgrid_path
        self.reader = TextGridReader(textgrid_path)
        self.textgrid_data = self.reader.textgrid_data
        
        if not self.textgrid_data:
            raise ValueError("TextGrid 데이터를 로드할 수 없습니다.")
    
    def get_word_phone_mapping(self) -> Dict[str, List[Interval]]:
        """
        각 word에 해당하는 phone interval들을 매핑합니다.
        word의 음소 분해에 해당하는 phone들만 찾습니다.
        
        Returns:
            Dict[str, List[Interval]]: word text를 key로 하고 해당 phone intervals를 value로 하는 딕셔너리
        """
        if 'word' not in self.textgrid_data.tiers or 'phone' not in self.textgrid_data.tiers:
            raise ValueError("word 또는 phone tier가 존재하지 않습니다.")
        
        word_tier = self.textgrid_data.tiers['word']
        phone_tier = self.textgrid_data.tiers['phone']
        
        # word와 phone tier의 interval들을 시간순으로 정렬
        word_intervals = sorted(word_tier.intervals, key=lambda x: x.xmin)
        phone_intervals = sorted(phone_tier.intervals, key=lambda x: x.xmin)
        
        word_phone_mapping = {}
        print(word_intervals[0].text)
        print(phone_intervals[10].text)
        
        for word_interval in word_intervals:
            word_text = word_interval.text
            if word_text == '':  # 빈 word는 건너뛰기
                continue
                
            word_phones = []

            # word interval 내에 완전히 포함되는 phone들을 찾기
            for phone_interval in phone_intervals:
                if not (phone_interval.text in word_interval.text):
                    continue
                                
                # phone이 word interval 내에 있는지, 
                print(f"word: {word_interval.text}, word_interval: {word_interval.xmin} ~ {word_interval.xmax}, phone: {phone_interval.text}, phone_interval: {phone_interval.xmin} ~ {phone_interval.xmax}")
                if (word_interval.xmin <= phone_interval.xmin and phone_interval.xmax <= word_interval.xmax):
                    word_phones.append(phone_interval)
                # 혹은 걸치는지 확인.
                elif (phone_interval.xmin <= word_interval.xmin and word_interval.xmin <= phone_interval.xmax) or \
                    (phone_interval.xmax <= word_interval.xmax and word_interval.xmax <= phone_interval.xmax):
                    word_phones.append(phone_interval)
            
            if word_phones:
                # 시간순으로 정렬
                word_phones.sort(key=lambda x: x.xmin)
                word_phone_mapping[word_text] = word_phones
                logger.debug(f"Word '{word_text}': {len(word_phones)}개 phone 매핑됨")
            else:
                logger.warning(f"Word '{word_text}'에 해당하는 phone을 찾을 수 없습니다.")
        
        return word_phone_mapping
    
    def check_word_phone_boundaries(self) -> Dict[str, List[Tuple[str, float, float, float, float]]]:
        """
        word와 phone tier 간의 경계 불일치를 확인합니다.
        word의 첫 번째 phone의 xmin과 word의 xmin이 일치하는지,
        word의 마지막 phone의 xmax와 word의 xmax가 일치하는지 확인합니다.
        
        Returns:
            Dict[str, List[Tuple]]: 각 word별로 (word_text, word_xmin, first_phone_xmin, word_xmax, last_phone_xmax) 정보
        """
        if not self.textgrid_data:
            logger.error("TextGrid 데이터가 로드되지 않았습니다.")
            return {}
        
        word_phone_mapping = self.get_word_phone_mapping()
        boundary_issues = {}
        
        word_tier = self.textgrid_data.tiers['word']
        
        for word_interval in word_tier.intervals:
            word_text = word_interval.text.strip()
            
            if word_text == '' or word_text not in word_phone_mapping:
                continue
            
            phones = word_phone_mapping[word_text]
            
            if not phones:
                continue
            
            # word에 포함된 phone들이 시간순으로 정렬되어 있으므로
            # 첫 번째 phone과 마지막 phone을 직접 가져옴
            first_phone = phones[0]  # 가장 이른 시간의 phone
            last_phone = phones[-1]  # 가장 늦은 시간의 phone
            
            # 경계 불일치 확인 (1ms 허용 오차)
            xmin_mismatch = word_interval.xmin != first_phone.xmin
            xmax_mismatch = word_interval.xmax != last_phone.xmax
            
            if xmin_mismatch or xmax_mismatch:
                boundary_issues[word_text] = [
                    (word_text, word_interval.xmin, first_phone.xmin, 
                     word_interval.xmax, last_phone.xmax)
                ]
                logger.debug(f"Word '{word_text}' 경계 불일치 발견:")
                logger.debug(f"  Word xmin: {word_interval.xmin:.3f}, First phone xmin: {first_phone.xmin:.3f}")
                logger.debug(f"  Word xmax: {word_interval.xmax:.3f}, Last phone xmax: {last_phone.xmax:.3f}")
        
        return boundary_issues
    
    def print_boundary_issues(self, boundary_issues: Dict[str, List[Tuple[str, float, float, float, float]]]):
        """
        경계 불일치 문제를 출력합니다.
        
        Args:
            boundary_issues (Dict): check_word_phone_boundaries()의 결과
        """
        if not boundary_issues:
            logger.info("🎉 모든 word-phone 경계가 일치합니다!")
            return
        
        logger.warning(f"❌ {len(boundary_issues)}개의 word에서 경계 불일치가 발견되었습니다:")
        logger.warning("=" * 80)
        
        for word_text, issues in boundary_issues.items():
            for issue in issues:
                word_text, word_xmin, first_phone_xmin, word_xmax, last_phone_xmax = issue
                
                logger.warning(f"Word: '{word_text}'")
                logger.warning(f"  Word xmin: {word_xmin:.3f} | 첫 번째 phone xmin: {first_phone_xmin:.3f}")
                logger.warning(f"  Word xmax: {word_xmax:.3f} | 마지막 phone xmax: {last_phone_xmax:.3f}")
                
                if abs(word_xmin - first_phone_xmin) > 0.001:
                    logger.error(f"  ❌ xmin 불일치: {abs(word_xmin - first_phone_xmin):.3f}초 차이")
                
                if abs(word_xmax - last_phone_xmax) > 0.001:
                    logger.error(f"  ❌ xmax 불일치: {abs(word_xmax - last_phone_xmax):.3f}초 차이")
                
                logger.warning("-" * 40)
    
    def fix_word_boundaries(self, backup: bool = True, inplace: bool = False, 
                          output_path: Optional[str] = None) -> bool:
        """
        word tier의 경계를 phone tier에 맞춰 수정합니다.
        
        Args:
            backup (bool): 백업 파일 생성 여부
            inplace (bool): 원본 파일에 덮어쓰기 여부
            output_path (Optional[str]): 출력 파일 경로
            
        Returns:
            bool: 수정 성공 여부
        """
        if not self.textgrid_data:
            logger.error("TextGrid 데이터가 로드되지 않았습니다.")
            return False
        
        logger.info(f"Word-phone 경계 수정 시작: {self.textgrid_path}")
        
        # 백업 생성
        if backup and not inplace:
            backup_path = self.textgrid_path + '.word_phone_backup'
            try:
                import shutil
                shutil.copy2(self.textgrid_path, backup_path)
                logger.info(f"백업 파일 생성: {backup_path}")
            except Exception as e:
                logger.error(f"백업 생성 실패: {e}")
                return False
        
        word_phone_mapping = self.get_word_phone_mapping()
        word_tier = self.textgrid_data.tiers['word']
        total_fixes = 0
        
        for word_interval in word_tier.intervals:
            word_text = word_interval.text.strip()
            
            if word_text == '' or word_text not in word_phone_mapping:
                continue
            
            phones = word_phone_mapping[word_text]
            
            if not phones:
                continue
            
            # word에 포함된 phone들이 시간순으로 정렬되어 있으므로
            # 첫 번째 phone과 마지막 phone을 직접 가져옴
            first_phone = phones[0]  # 가장 이른 시간의 phone
            last_phone = phones[-1]  # 가장 늦은 시간의 phone
            
            # 경계 수정
            old_xmin, old_xmax = word_interval.xmin, word_interval.xmax
            word_interval.xmin = first_phone.xmin
            word_interval.xmax = last_phone.xmax
            
            if old_xmin != word_interval.xmin or old_xmax != word_interval.xmax:
                logger.info(f"Word '{word_text}' 경계 수정:")
                logger.info(f"  xmin: {old_xmin:.3f} -> {word_interval.xmin:.3f}")
                logger.info(f"  xmax: {old_xmax:.3f} -> {word_interval.xmax:.3f}")
                total_fixes += 1
        
        # word tier의 전체 범위 업데이트
        if word_tier.intervals:
            old_tier_xmin, old_tier_xmax = word_tier.xmin, word_tier.xmax
            sorted_words = sorted(word_tier.intervals, key=lambda x: x.xmin)
            word_tier.xmin = sorted_words[0].xmin
            word_tier.xmax = sorted_words[-1].xmax
            
            if old_tier_xmin != word_tier.xmin or old_tier_xmax != word_tier.xmax:
                logger.info(f"Word tier 전체 범위 업데이트:")
                logger.info(f"  xmin: {old_tier_xmin:.3f} -> {word_tier.xmin:.3f}")
                logger.info(f"  xmax: {old_tier_xmax:.3f} -> {word_tier.xmax:.3f}")
        
        # 출력 파일 경로 결정
        if inplace:
            final_output_path = self.textgrid_path
        elif output_path:
            final_output_path = output_path
        else:
            base_name = os.path.splitext(self.textgrid_path)[0]
            final_output_path = f"{base_name}_fixed.TextGrid"
        
        # 수정된 파일 저장
        success = self.reader.write(final_output_path)
        
        if success:
            logger.info(f"Word-phone 경계 수정 완료: {total_fixes}개 word 수정, 출력: {final_output_path}")
        else:
            logger.error("Word-phone 경계 수정 실패")
        
        return success
    
    def get_summary(self) -> Dict[str, any]:
        """
        word-phone 매칭에 대한 요약 정보를 반환합니다.
        
        Returns:
            Dict: 요약 정보
        """
        if not self.textgrid_data:
            return {}
        
        word_phone_mapping = self.get_word_phone_mapping()
        boundary_issues = self.check_word_phone_boundaries()
        
        total_words = len(word_phone_mapping)
        total_issues = len(boundary_issues)
        
        summary = {
            'total_words': total_words,
            'words_with_issues': total_issues,
            'issue_percentage': (total_issues / total_words * 100) if total_words > 0 else 0,
            'word_phone_mapping': word_phone_mapping,
            'boundary_issues': boundary_issues
        }
        
        return summary


def main():
    """
    테스트용 메인 함수
    """
    # 예시 사용법
    textgrid_path = "/Users/bagjuhyeon/Documents/WorkSpace/phoneticConvergence/data/experiment_data/results-KFA-reviewed/participant_LY002/02_stage2_20250404_1349.TextGrid"
    
    try:
        checker = WordPhoneBoundaryChecker(textgrid_path)
        
        # 경계 불일치 확인
        boundary_issues = checker.check_word_phone_boundaries()
        checker.print_boundary_issues(boundary_issues)
        
        # 요약 정보 출력
        summary = checker.get_summary()
        print(f"\n📊 요약:")
        print(f"총 word 수: {summary['total_words']}")
        print(f"경계 문제가 있는 word 수: {summary['words_with_issues']}")
        print(f"문제 비율: {summary['issue_percentage']:.1f}%")
        
        # 경계 수정 (필요시)
        if boundary_issues:
            print(f"\n🔧 경계 수정을 원하시면 다음 코드를 실행하세요:")
            print(f"checker.fix_word_boundaries(backup=True, inplace=False)")
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")


if __name__ == "__main__":
    main()
