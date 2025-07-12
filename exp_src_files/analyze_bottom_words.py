import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

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
    bottom_df = analyze_bottom_words('word_frequency.xlsx', 100) 