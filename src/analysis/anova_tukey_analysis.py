import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.formula.api import ols
import warnings
warnings.filterwarnings('ignore')


def perform_anova(df, group_column, dependent_column):
    """
    일원분산분석(One-way ANOVA)을 수행합니다.
    
    Parameters:
    df (pd.DataFrame): 분석할 데이터프레임
    group_column (str): 그룹 변수 열 이름
    dependent_column (str): 종속 변수 열 이름
    
    Returns:
    dict: ANOVA 결과를 포함한 딕셔너리
    """
    try:
        # 데이터 검증
        if group_column not in df.columns:
            raise ValueError(f"그룹 변수 '{group_column}'이 데이터프레임에 없습니다.")
        if dependent_column not in df.columns:
            raise ValueError(f"종속 변수 '{dependent_column}'이 데이터프레임에 없습니다.")
        
        # 결측값 제거
        clean_df = df[[group_column, dependent_column]].dropna()
        
        if len(clean_df) == 0:
            raise ValueError("분석할 유효한 데이터가 없습니다.")
        
        # 그룹별 데이터 분리
        groups = [group_data[dependent_column].values 
                 for name, group_data in clean_df.groupby(group_column)]
        
        # 그룹 이름
        group_names = list(clean_df[group_column].unique())
        
        # ANOVA 수행
        f_stat, p_value = stats.f_oneway(*groups)
        
        # 그룹별 통계량 계산
        group_stats = clean_df.groupby(group_column)[dependent_column].agg([
            'count', 'mean', 'std', 'min', 'max'
        ]).round(4)
        
        # 전체 통계량
        overall_mean = clean_df[dependent_column].mean()
        overall_std = clean_df[dependent_column].std()
        
        # 결과 정리
        result = {
            'anova_results': {
                'f_statistic': f_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            },
            'group_statistics': group_stats,
            'overall_statistics': {
                'mean': overall_mean,
                'std': overall_std,
                'total_n': len(clean_df)
            },
            'group_names': group_names,
            'group_data': groups
        }
        
        return result
        
    except Exception as e:
        print(f"ANOVA 분석 중 오류 발생: {str(e)}")
        return None


def perform_tukey_hsd(df, group_column, dependent_column, alpha=0.05):
    """
    Tukey HSD 사후 검정을 수행합니다.
    
    Parameters:
    df (pd.DataFrame): 분석할 데이터프레임
    group_column (str): 그룹 변수 열 이름
    dependent_column (str): 종속 변수 열 이름
    alpha (float): 유의수준 (기본값: 0.05)
    
    Returns:
    dict: Tukey HSD 결과를 포함한 딕셔너리
    """
    try:
        # 데이터 검증
        if group_column not in df.columns:
            raise ValueError(f"그룹 변수 '{group_column}'이 데이터프레임에 없습니다.")
        if dependent_column not in df.columns:
            raise ValueError(f"종속 변수 '{dependent_column}'이 데이터프레임에 없습니다.")
        
        # 결측값 제거
        clean_df = df[[group_column, dependent_column]].dropna()
        
        if len(clean_df) == 0:
            raise ValueError("분석할 유효한 데이터가 없습니다.")
        
        # 그룹 수 확인 (최소 2개 그룹 필요)
        unique_groups = clean_df[group_column].nunique()
        if unique_groups < 2:
            raise ValueError("Tukey HSD 검정을 위해서는 최소 2개의 그룹이 필요합니다.")
        
        # Tukey HSD 수행
        tukey_result = pairwise_tukeyhsd(
            endog=clean_df[dependent_column],
            groups=clean_df[group_column],
            alpha=alpha
        )
        
        # 결과를 데이터프레임으로 변환
        tukey_df = pd.DataFrame(data=tukey_result._results_table.data[1:], 
                               columns=tukey_result._results_table.data[0])
        
        # 결과 정리
        result = {
            'tukey_results': tukey_df,
            'summary': tukey_result.summary(),
            'alpha': alpha,
            'significant_pairs': tukey_df[tukey_df['reject'] == True] if 'reject' in tukey_df.columns else None
        }
        
        return result
        
    except Exception as e:
        print(f"Tukey HSD 분석 중 오류 발생: {str(e)}")
        return None


def anova_tukey_analysis(df, group_column, dependent_column, alpha=0.05, verbose=True):
    """
    ANOVA와 Tukey HSD 검정을 순차적으로 수행합니다.
    
    Parameters:
    df (pd.DataFrame): 분석할 데이터프레임
    group_column (str): 그룹 변수 열 이름
    dependent_column (str): 종속 변수 열 이름
    alpha (float): 유의수준 (기본값: 0.05)
    verbose (bool): 상세 결과 출력 여부 (기본값: True)
    
    Returns:
    dict: ANOVA와 Tukey HSD 결과를 포함한 딕셔너리
    """
    print(f"=== ANOVA 및 Tukey HSD 분석 ===")
    print(f"그룹 변수: {group_column}")
    print(f"종속 변수: {dependent_column}")
    print(f"유의수준: {alpha}")
    print("-" * 50)
    
    # ANOVA 수행
    anova_result = perform_anova(df, group_column, dependent_column)
    
    if anova_result is None:
        return None
    
    # ANOVA 결과 출력
    if verbose:
        print("1. 일원분산분석(ANOVA) 결과:")
        print(f"   F-통계량: {anova_result['anova_results']['f_statistic']:.4f}")
        print(f"   p-값: {anova_result['anova_results']['p_value']:.4f}")
        print(f"   유의성: {'유의함' if anova_result['anova_results']['significant'] else '유의하지 않음'} (α = {alpha})")
        print()
        
        print("2. 그룹별 기술통계:")
        print(anova_result['group_statistics'])
        print()
        
        print("3. 전체 통계:")
        print(f"   전체 평균: {anova_result['overall_statistics']['mean']:.4f}")
        print(f"   전체 표준편차: {anova_result['overall_statistics']['std']:.4f}")
        print(f"   전체 표본 수: {anova_result['overall_statistics']['total_n']}")
        print()
    
    # ANOVA가 유의한 경우에만 Tukey HSD 수행
    if anova_result['anova_results']['significant']:
        print("4. Tukey HSD 사후 검정 (ANOVA가 유의하므로 수행):")
        tukey_result = perform_tukey_hsd(df, group_column, dependent_column, alpha)
        
        if tukey_result is not None and verbose:
            print(tukey_result['summary'])
            print()
            
            if tukey_result['significant_pairs'] is not None and len(tukey_result['significant_pairs']) > 0:
                print("5. 유의한 그룹 쌍:")
                print(tukey_result['significant_pairs'][['group1', 'group2', 'meandiff', 'p-adj']])
            else:
                print("5. 유의한 그룹 쌍이 없습니다.")
        
        # 결과 통합
        combined_result = {
            'anova': anova_result,
            'tukey': tukey_result,
            'analysis_type': 'anova_tukey'
        }
        
    else:
        print("4. ANOVA가 유의하지 않으므로 Tukey HSD 검정을 수행하지 않습니다.")
        combined_result = {
            'anova': anova_result,
            'tukey': None,
            'analysis_type': 'anova_only'
        }
    
    return combined_result


def quick_analysis(df, group_column, dependent_column, alpha=0.05):
    """
    간단한 분석 함수 (결과만 반환, 출력 없음)
    
    Parameters:
    df (pd.DataFrame): 분석할 데이터프레임
    group_column (str): 그룹 변수 열 이름
    dependent_column (str): 종속 변수 열 이름
    alpha (float): 유의수준 (기본값: 0.05)
    
    Returns:
    dict: 분석 결과
    """
    return anova_tukey_analysis(df, group_column, dependent_column, alpha, verbose=False)


# 사용 예시
if __name__ == "__main__":
    # 예시 데이터 생성
    np.random.seed(42)
    
    # 3개 그룹의 가상 데이터 생성
    group_a = np.random.normal(10, 2, 30)
    group_b = np.random.normal(12, 2, 30)
    group_c = np.random.normal(8, 2, 30)
    
    # 데이터프레임 생성
    example_df = pd.DataFrame({
        'group': ['A'] * 30 + ['B'] * 30 + ['C'] * 30,
        'value': np.concatenate([group_a, group_b, group_c])
    })
    
    print("예시 데이터:")
    print(example_df.head(10))
    print()
    
    # 분석 수행
    result = anova_tukey_analysis(example_df, 'group', 'value')
    
    if result:
        print("\n=== 분석 완료 ===")
        print("결과는 'result' 변수에 저장되었습니다.")
        print("result['anova']: ANOVA 결과")
        print("result['tukey']: Tukey HSD 결과 (ANOVA가 유의한 경우)")
