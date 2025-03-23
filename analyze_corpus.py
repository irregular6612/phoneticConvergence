import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from konlpy.tag import Okt
import seaborn as sns
import numpy as np
from tqdm import tqdm

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def get_all_files(corpus_dir):
    """코퍼스 디렉토리에서 모든 JSON 파일의 경로를 가져옵니다."""
    json_files = []
    for root, dirs, files in os.walk(corpus_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files

def extract_text_from_json(file_path):
    """JSON 파일에서 대화 텍스트를 추출합니다."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        text = ""
        # document 배열의 모든 요소 확인
        if 'document' in data and isinstance(data['document'], list):
            for doc in data['document']:
                if 'utterance' in doc:
                    for utterance in doc['utterance']:
                        if isinstance(utterance, dict) and 'form' in utterance:
                            text += utterance['form'] + " "
                            
            # document가 비어있는 경우 로그 출력
            if len(data['document']) == 0:
                print(f"\nWarning: Empty document array in {os.path.basename(file_path)}")
            # document가 여러 개인 경우 로그 출력
            elif len(data['document']) > 1:
                print(f"\nInfo: Multiple documents ({len(data['document'])}) found in {os.path.basename(file_path)}")
    return text.strip()

def analyze_corpus(corpus_dir):
    # Okt 형태소 분석기 초기화
    print("형태소 분석기 초기화 중...")
    okt = Okt()
    
    # 단어 빈도를 저장할 Counter 객체
    word_freq = Counter()
    
    # 전체 파일 목록 가져오기
    json_files = get_all_files(corpus_dir)
    print(f"총 {len(json_files)}개의 JSON 파일을 찾았습니다.")
    
    # 파일 처리 진행률 표시
    for file_path in tqdm(json_files, desc="파일 처리 중"):
        try:
            # JSON 파일에서 텍스트 추출
            text = extract_text_from_json(file_path)
            
            # 형태소 분석 (명사와 동사 추출)
            nouns = okt.nouns(text)  # 명사 추출
            verbs = [word for word, pos in okt.pos(text) if pos.startswith('Verb')]  # 동사 추출
            
            # 2글자 이상인 단어만 선택
            words = [word for word in nouns + verbs if len(word) > 1]
            
            # 빈도 계산
            word_freq.update(words)
        except Exception as e:
            print(f"\nError processing {os.path.basename(file_path)}: {e}")
    
    return word_freq

def visualize_and_save(word_freq, output_prefix='word_frequency'):
    print("\n데이터 시각화 및 저장 중...")
    
    # 데이터프레임 생성
    df = pd.DataFrame(word_freq.most_common(), columns=['단어', '빈도'])
    
    # 엑셀 파일로 저장
    print("엑셀 파일 저장 중...")
    df.to_excel(f'{output_prefix}.xlsx', index=False)
    
    # CSV 파일로 저장
    print("CSV 파일 저장 중...")
    df.to_csv(f'{output_prefix}.csv', index=False, encoding='utf-8-sig')
    
    if len(df) > 0:  # 데이터가 있는 경우에만 시각화
        # 상위 20개 단어 시각화
        print("상위 20개 단어 시각화 중...")
        plt.figure(figsize=(15, 8))
        sns.barplot(data=df.head(20), x='단어', y='빈도')
        plt.xticks(rotation=45, ha='right')
        plt.title('상위 20개 단어 빈도')
        plt.tight_layout()
        plt.savefig(f'{output_prefix}_top20.png', dpi=300, bbox_inches='tight')
        plt.close()  # 메모리 해제를 위해 figure 닫기
        
        # 빈도 분포 히스토그램
        print("빈도 분포 히스토그램 생성 중...")
        plt.figure(figsize=(12, 6))
        plt.hist(df['빈도'], bins=50)
        plt.title('단어 빈도 분포')
        plt.xlabel('빈도')
        plt.ylabel('단어 수')
        if df['빈도'].min() > 0:  # 양수 값이 있는 경우에만 로그 스케일 적용
            plt.yscale('log')
        plt.tight_layout()
        plt.savefig(f'{output_prefix}_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()  # 메모리 해제를 위해 figure 닫기
    
    return df

def analyze_bottom_words(input_file='word_frequency.xlsx', n_words=100):
    """하위 빈도 단어를 분석하고 시각화합니다."""
    print(f"\n=== 하위 {n_words}개 단어 분석 시작 ===")
    
    # 엑셀 파일 읽기
    df = pd.read_excel(input_file)
    
    # 하위 n개 단어 추출
    bottom_df = df.tail(n_words).iloc[::-1]  # 역순으로 정렬
    
    # 결과 저장
    output_prefix = 'bottom_words'
    print("하위 단어 데이터 저장 중...")
    bottom_df.to_excel(f'{output_prefix}.xlsx', index=False)
    bottom_df.to_csv(f'{output_prefix}.csv', index=False, encoding='utf-8-sig')
    
    # 시각화
    print("하위 단어 시각화 중...")
    plt.figure(figsize=(15, 8))
    sns.barplot(data=bottom_df, x='단어', y='빈도')
    plt.xticks(rotation=90, ha='right')
    plt.title(f'하위 {n_words}개 단어 빈도')
    plt.tight_layout()
    plt.savefig(f'{output_prefix}.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n=== 하위 {n_words}개 단어 분석 완료 ===")
    print("\n가장 빈도가 낮은 10개 단어:")
    print(bottom_df.head(10).to_string(index=False))
    
    print("\n생성된 파일:")
    print(f"1. {output_prefix}.xlsx - 하위 {n_words}개 단어 (엑셀)")
    print(f"2. {output_prefix}.csv - 하위 {n_words}개 단어 (CSV)")
    print(f"3. {output_prefix}.png - 하위 {n_words}개 단어 그래프")
    
    return bottom_df

if __name__ == "__main__":
    # NIKL 코퍼스 디렉토리 경로 설정
    corpus_dir = "./NIKL_DIALOUGUE_2023"
    
    # 기존 분석 실행
    print("=== 코퍼스 분석 시작 ===")
    word_freq = analyze_corpus(corpus_dir)
    
    df = visualize_and_save(word_freq)
    print("\n=== 분석 완료 ===")
    print(f"총 {len(df):,}개의 고유 단어가 발견되었습니다.")
    print("\n가장 빈도가 높은 10개 단어:")
    print(df.head(10).to_string(index=False))
    
    print("\n생성된 파일:")
    print("1. word_frequency.xlsx - 전체 단어 빈도 (엑셀)")
    print("2. word_frequency.csv - 전체 단어 빈도 (CSV)")
    print("3. word_frequency_top20.png - 상위 20개 단어 그래프")
    print("4. word_frequency_distribution.png - 빈도 분포 히스토그램")
    
    # 하위 100개 단어 분석
    bottom_df = analyze_bottom_words('word_frequency.xlsx', 100) 