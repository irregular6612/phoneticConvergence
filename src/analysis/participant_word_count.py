import pandas as pd
import os
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_participant_word_count():
    """
    참가자별로 단어 개수를 분석하고 엑셀 파일로 저장
    """
    # 프로젝트 디렉토리 설정
    proj_dir = Path.home() / "Documents" / "WorkSpace" / "phoneticConvergence"
    
    # formant_results_all_vowels.xlsx 파일 읽기
    excel_path = os.path.join(proj_dir, "formant_results_all_vowels.xlsx")
    
    try:
        logger.info(f"엑셀 파일 읽기: {excel_path}")
        p_formants_df = pd.read_excel(excel_path)
        logger.info(f"데이터 로드 완료. 총 {len(p_formants_df)} 행")
        
        # 데이터 구조 확인
        logger.info("데이터 컬럼:")
        for col in p_formants_df.columns:
            logger.info(f"  - {col}")
        
        # 참가자 컬럼 찾기 (participant, participant_id, participant_name 등)
        participant_cols = [col for col in p_formants_df.columns if 'participant' in col.lower()]
        logger.info(f"참가자 관련 컬럼: {participant_cols}")
        
        # 단어 컬럼 찾기 (word, word_name, word_id 등)
        word_cols = [col for col in p_formants_df.columns if 'word' in col.lower()]
        logger.info(f"단어 관련 컬럼: {word_cols}")
        
        # 참가자 컬럼 선택 (첫 번째 참가자 컬럼 사용)
        if participant_cols:
            participant_col = participant_cols[0]
            logger.info(f"참가자 컬럼으로 사용: {participant_col}")
        else:
            # 참가자 컬럼이 없으면 파일명에서 추출
            logger.warning("참가자 컬럼을 찾을 수 없습니다. 파일명에서 추출을 시도합니다.")
            participant_col = 'participant_from_filename'
            # 파일명에서 참가자 정보 추출하는 로직 추가 필요
        
        # 단어 컬럼 선택 (첫 번째 단어 컬럼 사용)
        if word_cols:
            word_col = word_cols[0]
            logger.info(f"단어 컬럼으로 사용: {word_col}")
        else:
            logger.warning("단어 컬럼을 찾을 수 없습니다.")
            word_col = None
        
        # 참가자별 단어 개수 계산
        if participant_col in p_formants_df.columns and word_col and word_col in p_formants_df.columns:
            try:
                # 참가자 ID를 문자열로 변환하여 정렬 문제 해결
                p_formants_df[participant_col] = p_formants_df[participant_col].astype(str)
                
                # 단어 라벨도 문자열로 변환
                p_formants_df[word_col] = p_formants_df[word_col].astype(str)
                
                logger.info("데이터 타입 변환 완료")
                
                # 참가자별 고유 단어 개수 계산
                participant_word_counts = p_formants_df.groupby(participant_col)[word_col].nunique().reset_index()
                participant_word_counts.columns = ['참가자', '단어_개수']
                
                logger.info("참가자별 단어 개수 계산 완료")
                
                # 참가자별 총 발화 개수 계산
                participant_total_utterances = p_formants_df.groupby(participant_col).size().reset_index()
                participant_total_utterances.columns = ['참가자', '총_발화_개수']
                
                logger.info("참가자별 총 발화 개수 계산 완료")
                
                # 두 데이터프레임 병합
                result_df = pd.merge(participant_word_counts, participant_total_utterances, on='참가자')
                
                logger.info("데이터프레임 병합 완료")
                
                # 참가자별 단어 목록도 추가
                participant_word_lists = p_formants_df.groupby(participant_col)[word_col].apply(list).reset_index()
                participant_word_lists.columns = ['참가자', '단어_목록']
                
                logger.info("참가자별 단어 목록 생성 완료")
                
                # 고유 단어 목록으로 변경
                participant_word_lists['고유_단어_목록'] = participant_word_lists['단어_목록'].apply(lambda x: list(set(x)))
                participant_word_lists['고유_단어_목록_문자열'] = participant_word_lists['고유_단어_목록'].apply(lambda x: ', '.join(sorted(x)))
                
                logger.info("고유 단어 목록 생성 완료")
                
                # 최종 결과에 단어 목록 추가
                result_df = pd.merge(result_df, participant_word_lists[['참가자', '고유_단어_목록_문자열']], on='참가자')
                
                logger.info("최종 결과 병합 완료")
                
            except Exception as e:
                logger.error(f"데이터 처리 중 오류 발생: {str(e)}")
                logger.error(f"오류 발생 위치: {e.__traceback__.tb_lineno}")
                return None
            
            # 평균 단어 개수 계산
            avg_word_count = result_df['단어_개수'].mean()
            total_participants = len(result_df)
            
            logger.info(f"분석 결과:")
            logger.info(f"  - 총 참가자 수: {total_participants}")
            logger.info(f"  - 평균 단어 개수: {avg_word_count:.2f}")
            logger.info(f"  - 최대 단어 개수: {result_df['단어_개수'].max()}")
            logger.info(f"  - 최소 단어 개수: {result_df['단어_개수'].min()}")
            
            # 결과 출력
            print("\n=== 참가자별 단어 개수 분석 결과 ===")
            print(result_df.to_string(index=False))
            
            # 엑셀 파일로 저장
            output_path = os.path.join(proj_dir, "participant_word_count_analysis.xlsx")
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 메인 결과 시트
                result_df.to_excel(writer, sheet_name='참가자별_단어_개수', index=False)
                
                # 요약 통계 시트
                summary_data = {
                    '통계': ['총 참가자 수', '평균 단어 개수', '최대 단어 개수', '최소 단어 개수', '표준편차'],
                    '값': [total_participants, avg_word_count, result_df['단어_개수'].max(), 
                          result_df['단어_개수'].min(), result_df['단어_개수'].std()]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='요약_통계', index=False)
                
                # 원본 데이터 샘플 시트
                sample_df = p_formants_df.head(100)
                sample_df.to_excel(writer, sheet_name='원본_데이터_샘플', index=False)
            
            logger.info(f"결과가 저장되었습니다: {output_path}")
            
            return result_df
            
        else:
            logger.error("참가자 또는 단어 컬럼을 찾을 수 없습니다.")
            logger.info("사용 가능한 컬럼:")
            for i, col in enumerate(p_formants_df.columns):
                logger.info(f"  {i+1}. {col}")
            return None
            
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {excel_path}")
        return None
    except Exception as e:
        logger.error(f"파일 읽기 중 오류 발생: {str(e)}")
        return None

if __name__ == "__main__":
    result = analyze_participant_word_count()
    if result is not None:
        print("\n분석이 완료되었습니다!")
    else:
        print("\n분석 중 오류가 발생했습니다.")
