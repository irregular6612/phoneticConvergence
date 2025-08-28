import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from pathlib import Path

def plot_formant_chart(participant_id, model_data_path, participant_data_path, survey_data_path):
    """
    모델과 특정 참가자의 모음별 F1, F2 포먼트 차트를 그립니다.

    Args:
        participant_id (int): 플롯을 그릴 참가자의 ID.
        model_data_path (str): 모델 데이터 엑셀 파일 경로.
        participant_data_path (str): 참가자 데이터 엑셀 파일 경로.
        survey_data_path (str): 설문조사 데이터 엑셀 파일 경로.
    """
    # 데이터 불러오기
    df_model = pd.read_excel(model_data_path)
    df_participant = pd.read_excel(participant_data_path)
    df_survey = pd.read_excel(survey_data_path)

    # 설문조사 데이터에서 참가자 정보 추출
    df_survey['participant_num'] = df_survey['1. 참가자 번호'].str.replace('LY', '').astype(int)
    participant_info = df_survey[df_survey['participant_num'] == participant_id]
    
    gender = participant_info['Gender'].iloc[0] if not participant_info.empty else 'N/A'
    list_num = participant_info['Actual_list_Num'].iloc[0] if not participant_info.empty else 'N/A'


    # 특정 참가자 데이터 필터링
    df_participant_filtered = df_participant[df_participant['participant_id'] == participant_id].copy()
    
    # stage 순서 정렬을 위해 stage 번호 추출
    df_participant_filtered['stage_num'] = df_participant_filtered['stage'].str.replace('stage', '').astype(int)
    df_participant_filtered = df_participant_filtered.sort_values(by=['vowel_label', 'stage_num'])

    # 플롯 생성
    fig, ax = plt.subplots(figsize=(12, 10))

    # 모음 종류 및 색상 설정
    vowels = sorted(df_model['vowel_label'].unique())
    colors = plt.cm.tab10(range(len(vowels)))
    vowel_color_map = {vowel: color for vowel, color in zip(vowels, colors)}

    # 모델 데이터 플롯 (기준점)
    for _, row in df_model.iterrows():
        ax.scatter(row['F2_mean'], row['F1_mean'], c=[vowel_color_map[row['vowel_label']]], 
                    marker='D', s=80, edgecolor='k', linewidth=0.5, zorder=3)
        ax.text(row['F2_mean'] + 10, row['F1_mean'], row['vowel_label'], 
                 fontsize=14, ha='left', va='center')

    # 참가자 데이터 플롯 (경로)
    for vowel in vowels:
        vowel_data = df_participant_filtered[df_participant_filtered['vowel_label'] == vowel]
        if not vowel_data.empty:
            points = vowel_data[['F2_mean', 'F1_mean']].values
            
            # Scatter plot
            ax.scatter(points[:, 0], points[:, 1], c=[vowel_color_map[vowel]], 
                        s=40, zorder=2)

            # 화살표 그리기 (annotate 사용)
            for i in range(len(points) - 1):
                ax.annotate("",
                             xy=(points[i+1, 0], points[i+1, 1]), 
                             xytext=(points[i, 0], points[i, 1]),
                             arrowprops=dict(arrowstyle="->", color=vowel_color_map[vowel],
                                             shrinkA=5, shrinkB=5,
                                             patchA=None, patchB=None,
                                             connectionstyle="arc3,rad=0.1"))

    # 플롯 설정
    ax.set_title(f'Formant Chart for Participant {participant_id}', fontsize=16)
    ax.set_xlabel('F2 (Hz)', fontsize=12)
    ax.set_ylabel('F1 (Hz)', fontsize=12)
    ax.invert_xaxis()
    ax.invert_yaxis()
    ax.grid(True, linestyle='--', alpha=0.6)

    # 커스텀 범례 생성
    legend_elements = [
        mlines.Line2D([0], [0], marker='D', color='w', label='Model',
                      markerfacecolor='gray', markeredgecolor='k', markersize=10),
        mlines.Line2D([0], [0], marker='o', color='w', label='Participant',
                      markerfacecolor='gray', markersize=8)
    ]
    for vowel, color in vowel_color_map.items():
        legend_elements.append(mlines.Line2D([0], [0], color=color, lw=4, label=f'Vowel: {vowel}'))

    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0.)
    
    # 참가자 정보 텍스트 추가
    info_text = f"Gender: {gender}\nList: {list_num}"
    fig.text(0.86, 0.6, info_text, fontsize=12, transform=plt.gcf().transFigure)

    plt.tight_layout(rect=[0, 0, 0.85, 1]) # 범례가 들어갈 공간 확보
    plt.show()

if __name__ == '__main__':
    # 예시: 참가자 ID 5에 대한 플롯 생성
    model_file = Path.home() / 'Documents' / 'WorkSpace' / 'phoneticConvergence' / 'src' / 'analysis' / 'formant_results_all_vowels_model_standard.xlsx'
    participant_file = Path.home() / 'Documents' / 'WorkSpace' / 'phoneticConvergence' / 'src' / 'analysis' / 'formant_results_all_vowels_participant_stage.xlsx'
    survey_file = Path.home() / 'Documents' / 'WorkSpace' / 'phoneticConvergence' / 'data' / 'experiment_data' / 'survey-latest.xlsx'
    
    # 사용 가능한 참가자 ID 목록 확인
    df_participant_all = pd.read_excel(participant_file)
    participant_ids = df_participant_all['participant_id'].unique()
    print(f"Available participant IDs: {participant_ids}")

    if len(participant_ids) > 0:
        plot_formant_chart(participant_ids[5], model_file, participant_file, survey_file)
    else:
        print("No participant data found.")


# z-score norm 개인 내.