import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from pathlib import Path
import numpy as np

def plot_formant_chart(participant_id, model_data_path, participant_data_path, survey_data_path, save_dir=".", use_zscore=True):
    """
    모델과 특정 참가자의 모음별 F1, F2 포먼트 차트를 그립니다.

    Args:
        participant_id (int): 플롯을 그릴 참가자의 ID.
        model_data_path (str): 모델 데이터 엑셀 파일 경로.
        participant_data_path (str): 참가자 데이터 엑셀 파일 경로.
        survey_data_path (str): 설문조사 데이터 엑셀 파일 경로.
        save_dir (str): 이미지 저장 디렉토리.
        use_zscore (bool): True면 z-score 값 사용, False면 원본 Hz 값 사용.
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
    
    # 사용할 데이터 컬럼 선택
    if use_zscore:
        model_f1_col = 'F1_mid_mean(z)'
        model_f2_col = 'F2_mid_mean(z)'
        participant_f1_col = 'F1_mid_point_zscore'
        participant_f2_col = 'F2_mid_point_zscore'
        f1_label = 'F1 (z-score)'
        f2_label = 'F2 (z-score)'
    else:
        model_f1_col = 'F1_mid_mean'
        model_f2_col = 'F2_mid_mean'
        participant_f1_col = 'F1_mid_point'
        participant_f2_col = 'F2_mid_point'
        f1_label = 'F1 (Hz)'
        f2_label = 'F2 (Hz)'

    # 플롯 생성
    fig, ax = plt.subplots(figsize=(12, 10))

    # 모음 종류 및 색상 설정
    vowels = sorted(df_model['vowel_label'].unique())
    colors = plt.cm.tab10(range(len(vowels)))
    vowel_color_map = {vowel: color for vowel, color in zip(vowels, colors)}

    # 모델 데이터 플롯 (기준점)
    for _, row in df_model.iterrows():
        ax.scatter(row[model_f2_col], row[model_f1_col], c=[vowel_color_map[row['vowel_label']]], 
                    marker='D', s=50, edgecolor='k', linewidth=0.5, zorder=3)
        ax.text(row[model_f2_col] + 0.1, row[model_f1_col], row['vowel_label'], 
                 fontsize=12, ha='left', va='center', weight='bold')

    # 참가자 데이터 플롯 (경로)
    for vowel in vowels:
        vowel_data = df_participant_filtered[df_participant_filtered['vowel_label'] == vowel]
        if not vowel_data.empty:
            points = vowel_data[[participant_f2_col, participant_f1_col]].values
            
            # Scatter plot
            ax.scatter(points[:, 0], points[:, 1], c=[vowel_color_map[vowel]], 
                        s=20, zorder=2)

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
    ax.set_xlabel(f2_label, fontsize=12)
    ax.set_ylabel(f1_label, fontsize=12)
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
    
    # 이미지 저장
    output_filename = Path(save_dir) / f"formant_chart_participant_{participant_id}.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Image saved as: {output_filename}")
    plt.show()

def plot_all_participants_subplot(model_data_path, participant_data_path, survey_data_path, 
                                 max_participants_per_row=5, figsize_per_subplot=(6, 4.5), save_dir=".", use_zscore=True):
    """
    모든 참가자의 포먼트 차트를 subplot으로 그립니다.
    
    Args:
        model_data_path (str): 모델 데이터 엑셀 파일 경로
        participant_data_path (str): 참가자 데이터 엑셀 파일 경로
        survey_data_path (str): 설문조사 데이터 엑셀 파일 경로
        max_participants_per_row (int): 한 행에 표시할 최대 참가자 수 (기본값: 5)
        figsize_per_subplot (tuple): 각 subplot의 크기 (기본값: (4, 3))
        save_dir (str): 이미지 저장 디렉토리
        use_zscore (bool): True면 z-score 값 사용, False면 원본 Hz 값 사용
    """
    # 데이터 불러오기
    df_model = pd.read_excel(model_data_path)
    df_participant = pd.read_excel(participant_data_path)
    df_survey = pd.read_excel(survey_data_path)
    
    # 설문조사 데이터에서 참가자 정보 추출
    df_survey['participant_num'] = df_survey['1. 참가자 번호'].str.replace('LY', '').astype(int)
    
    # 참가자 ID 목록 가져오기
    participant_ids = sorted(df_participant['participant_id'].unique())
    n_participants = len(participant_ids)
    
    # subplot 그리드 계산
    n_rows = int(np.ceil(n_participants / max_participants_per_row))
    n_cols = min(max_participants_per_row, n_participants)
    
    # 전체 figure 크기 계산 (여백을 고려하여 더 크게)
    fig_width = n_cols * figsize_per_subplot[0] + 2  # 여백 추가
    fig_height = n_rows * figsize_per_subplot[1] + 3  # 여백 추가
    
    # figure 생성
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height))
    
    # axes를 1차원 배열로 변환 (단일 subplot인 경우 처리)
    if n_participants == 1:
        axes = [axes]
    elif n_rows == 1:
        axes = axes if isinstance(axes, list) else [axes]
    else:
        axes = axes.flatten()
    
    # 사용할 데이터 컬럼 선택
    if use_zscore:
        model_f1_col = 'F1_mid_mean(z)'
        model_f2_col = 'F2_mid_mean(z)'
        participant_f1_col = 'F1_mid_point_zscore'
        participant_f2_col = 'F2_mid_point_zscore'
        f1_label = 'F1 (z-score)'
        f2_label = 'F2 (z-score)'
    else:
        model_f1_col = 'F1_mid_mean'
        model_f2_col = 'F2_mid_mean'
        participant_f1_col = 'F1_mid_point'
        participant_f2_col = 'F2_mid_point'
        f1_label = 'F1 (Hz)'
        f2_label = 'F2 (Hz)'
    
    # 모음 종류 및 색상 설정
    vowels = sorted(df_model['vowel_label'].unique())
    colors = plt.cm.tab10(range(len(vowels)))
    vowel_color_map = {vowel: color for vowel, color in zip(vowels, colors)}
    
    # 각 참가자에 대해 subplot 생성
    for idx, participant_id in enumerate(participant_ids):
        ax = axes[idx]
        
        # 참가자 정보 가져오기
        participant_info = df_survey[df_survey['participant_num'] == participant_id]
        gender = participant_info['Gender'].iloc[0] if not participant_info.empty else 'N/A'
        list_num = participant_info['Actual_list_Num'].iloc[0] if not participant_info.empty else 'N/A'
        
        # 특정 참가자 데이터 필터링
        df_participant_filtered = df_participant[df_participant['participant_id'] == participant_id].copy()
        
        # stage 순서 정렬을 위해 stage 번호 추출
        df_participant_filtered['stage_num'] = df_participant_filtered['stage'].str.replace('stage', '').astype(int)
        df_participant_filtered = df_participant_filtered.sort_values(by=['vowel_label', 'stage_num'])
        
        # 모델 데이터 플롯 (기준점)
        for _, row in df_model.iterrows():
            ax.scatter(row[model_f2_col], row[model_f1_col], c=[vowel_color_map[row['vowel_label']]], 
                        marker='D', s=40, edgecolor='k', linewidth=0.5, zorder=3)
            ax.text(row[model_f2_col] + 0.1, row[model_f1_col], row['vowel_label'], 
                     fontsize=9, ha='left', va='center', weight='bold')
        
        # 참가자 데이터 플롯 (경로)
        for vowel in vowels:
            vowel_data = df_participant_filtered[df_participant_filtered['vowel_label'] == vowel]
            if not vowel_data.empty:
                points = vowel_data[[participant_f2_col, participant_f1_col]].values
                
                # Scatter plot
                ax.scatter(points[:, 0], points[:, 1], c=[vowel_color_map[vowel]], 
                            s=15, zorder=2)
                
                # 화살표 그리기
                for i in range(len(points) - 1):
                    ax.annotate("",
                                 xy=(points[i+1, 0], points[i+1, 1]), 
                                 xytext=(points[i, 0], points[i, 1]),
                                 arrowprops=dict(arrowstyle="->", color=vowel_color_map[vowel],
                                                 shrinkA=3, shrinkB=3,
                                                 patchA=None, patchB=None,
                                                 connectionstyle="arc3,rad=0.1"))
        
        # subplot 설정
        ax.set_title(f'P{participant_id} ({gender})', fontsize=12)
        ax.set_xlabel(f2_label, fontsize=10)
        ax.set_ylabel(f1_label, fontsize=10)
        ax.invert_xaxis()
        ax.invert_yaxis()
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.tick_params(labelsize=8)
    
    # 사용하지 않는 subplot 숨기기
    for idx in range(n_participants, len(axes)):
        axes[idx].set_visible(False)
    
    # 전체 figure에 대한 범례 생성 (첫 번째 subplot에만)
    if n_participants > 0:
        legend_elements = [
            mlines.Line2D([0], [0], marker='D', color='w', label='Model',
                          markerfacecolor='gray', markeredgecolor='k', markersize=8),
            mlines.Line2D([0], [0], marker='o', color='w', label='Participant',
                          markerfacecolor='gray', markersize=6)
        ]
        for vowel, color in vowel_color_map.items():
            legend_elements.append(mlines.Line2D([0], [0], color=color, lw=3, label=f'{vowel}'))
        
        # 범례를 figure 전체에 추가
        fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.95), 
                   ncol=len(legend_elements), fontsize=10)
    
    # subplot 간격 수동 조정 (tight_layout 대신 사용)
    plt.subplots_adjust(
        left=0.12,      # 왼쪽 여백 증가 (y축 라벨 공간)
        right=0.95,     # 오른쪽 여백
        top=0.88,       # 상단 여백 (범례 공간 확보)
        bottom=0.12,    # 하단 여백 증가 (x축 라벨 공간)
        hspace=0.6,     # 수직 간격 증가 (축 정보 겹침 방지)
        wspace=0.4      # 수평 간격 증가
    )
    
    # 이미지 저장
    output_filename = Path(save_dir) / f"formant_charts_all_participants_{n_participants}participants.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Image saved as: {output_filename}")
    plt.show()
    
    print(f"Generated subplot for {n_participants} participants in {n_rows}x{n_cols} grid")

def plot_participants_by_gender_subplot(model_data_path, participant_data_path, survey_data_path, 
                                       max_participants_per_row=5, figsize_per_subplot=(20, 20), save_dir=".", use_zscore=True):
    """
    성별로 구분하여 모든 참가자의 포먼트 차트를 subplot으로 그립니다.
    
    Args:
        model_data_path (str): 모델 데이터 엑셀 파일 경로
        participant_data_path (str): 참가자 데이터 엑셀 파일 경로
        survey_data_path (str): 설문조사 데이터 엑셀 파일 경로
        max_participants_per_row (int): 한 행에 표시할 최대 참가자 수 (기본값: 5)
        figsize_per_subplot (tuple): 각 subplot의 크기 (기본값: (4, 3))
        save_dir (str): 이미지 저장 디렉토리
        use_zscore (bool): True면 z-score 값 사용, False면 원본 Hz 값 사용
    """
    # 데이터 불러오기
    df_model = pd.read_excel(model_data_path)
    df_participant = pd.read_excel(participant_data_path)
    df_survey = pd.read_excel(survey_data_path)
    
    # 설문조사 데이터에서 참가자 정보 추출
    df_survey['participant_num'] = df_survey['1. 참가자 번호'].str.replace('LY', '').astype(int)
    
    # 성별별로 참가자 그룹화
    male_participants = []
    female_participants = []
    
    for participant_id in df_participant['participant_id'].unique():
        participant_info = df_survey[df_survey['participant_num'] == participant_id]
        if not participant_info.empty:
            gender = participant_info['Gender'].iloc[0]
            if gender.lower() == 'male':
                male_participants.append(participant_id)
            elif gender.lower() == 'female':
                female_participants.append(participant_id)
    
    male_participants = sorted(male_participants)
    female_participants = sorted(female_participants)
    
    # 사용할 데이터 컬럼 선택
    if use_zscore:
        model_f1_col = 'F1_mid_mean(z)'
        model_f2_col = 'F2_mid_mean(z)'
        participant_f1_col = 'F1_mid_point_zscore'
        participant_f2_col = 'F2_mid_point_zscore'
        f1_label = 'F1 (z-score)'
        f2_label = 'F2 (z-score)'
    else:
        model_f1_col = 'F1_mid_mean'
        model_f2_col = 'F2_mid_mean'
        participant_f1_col = 'F1_mid_point'
        participant_f2_col = 'F2_mid_point'
        f1_label = 'F1 (Hz)'
        f2_label = 'F2 (Hz)'
    
    # 각 성별에 대해 subplot 생성
    for gender, participants in [('Male', male_participants), ('Female', female_participants)]:
        if not participants:
            continue
            
        n_participants = len(participants)
        n_rows = int(np.ceil(n_participants / max_participants_per_row))
        n_cols = min(max_participants_per_row, n_participants)
        
        # 전체 figure 크기 계산 (여백을 고려하여 더 크게)
        fig_width = n_cols * figsize_per_subplot[0] + 2  # 여백 추가
        fig_height = n_rows * figsize_per_subplot[1] + 3  # 여백 추가
        
        # figure 생성
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height))
        fig.suptitle(f'Formant Charts - {gender} Participants', fontsize=18)
        
        # axes를 1차원 배열로 변환
        if n_participants == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes if isinstance(axes, list) else [axes]
        else:
            axes = axes.flatten()
        
        # 모음 종류 및 색상 설정
        vowels = sorted(df_model['vowel_label'].unique())
        colors = plt.cm.tab10(range(len(vowels)))
        vowel_color_map = {vowel: color for vowel, color in zip(vowels, colors)}
        
        # 각 참가자에 대해 subplot 생성
        for idx, participant_id in enumerate(participants):
            ax = axes[idx]
            
            # 특정 참가자 데이터 필터링
            df_participant_filtered = df_participant[df_participant['participant_id'] == participant_id].copy()
            
            # stage 순서 정렬을 위해 stage 번호 추출
            df_participant_filtered['stage_num'] = df_participant_filtered['stage'].str.replace('stage', '').astype(int)
            df_participant_filtered = df_participant_filtered.sort_values(by=['vowel_label', 'stage_num'])
            
            # 모델 데이터 플롯 (기준점)
            for _, row in df_model.iterrows():
                ax.scatter(row[model_f2_col], row[model_f1_col], c=[vowel_color_map[row['vowel_label']]], 
                            marker='D', s=40, edgecolor='k', linewidth=0.5, zorder=3)
                ax.text(row[model_f2_col] + 0.1, row[model_f1_col], row['vowel_label'], 
                         fontsize=9, ha='left', va='center', weight='bold')
            
            # 참가자 데이터 플롯 (경로)
            for vowel in vowels:
                vowel_data = df_participant_filtered[df_participant_filtered['vowel_label'] == vowel]
                if not vowel_data.empty:
                    points = vowel_data[[participant_f2_col, participant_f1_col]].values
                    
                    # Scatter plot
                    ax.scatter(points[:, 0], points[:, 1], c=[vowel_color_map[vowel]], 
                                s=15, zorder=2)
                    
                    # 화살표 그리기
                    for i in range(len(points) - 1):
                        ax.annotate("",
                                     xy=(points[i+1, 0], points[i+1, 1]), 
                                     xytext=(points[i, 0], points[i, 1]),
                                     arrowprops=dict(arrowstyle="->", color=vowel_color_map[vowel],
                                                     shrinkA=3, shrinkB=3,
                                                     patchA=None, patchB=None,
                                                     connectionstyle="arc3,rad=0.1"))
            
            # subplot 설정
            ax.set_title(f'P{participant_id}', fontsize=12)
            ax.set_xlabel(f2_label, fontsize=10)
            ax.set_ylabel(f1_label, fontsize=10)
            ax.invert_xaxis()
            ax.invert_yaxis()
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.tick_params(labelsize=8)
        
        # 사용하지 않는 subplot 숨기기
        for idx in range(n_participants, len(axes)):
            axes[idx].set_visible(False)
        
        # 범례 생성
        if n_participants > 0:
            legend_elements = [
                mlines.Line2D([0], [0], marker='D', color='w', label='Model',
                              markerfacecolor='gray', markeredgecolor='k', markersize=8),
                mlines.Line2D([0], [0], marker='o', color='w', label='Participant',
                              markerfacecolor='gray', markersize=6)
            ]
            for vowel, color in vowel_color_map.items():
                legend_elements.append(mlines.Line2D([0], [0], color=color, lw=3, label=f'{vowel}'))
            
            fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.95), 
                       ncol=len(legend_elements), fontsize=10)
        
        # subplot 간격 수동 조정 (tight_layout 대신 사용)
        plt.subplots_adjust(
            left=0.12,      # 왼쪽 여백 증가 (y축 라벨 공간)
            right=0.95,     # 오른쪽 여백
            top=0.88,       # 상단 여백 (범례 공간 확보)
            bottom=0.12,    # 하단 여백 증가 (x축 라벨 공간)
            hspace=0.6,     # 수직 간격 증가 (축 정보 겹침 방지)
            wspace=0.4      # 수평 간격 증가
        )
        
        # 이미지 저장
        output_filename = Path(save_dir) / f"formant_charts_{gender.lower()}_participants_{n_participants}participants.png"
        plt.savefig(output_filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Image saved as: {output_filename}")
        plt.show()
        
        print(f"Generated {gender} subplot for {n_participants} participants in {n_rows}x{n_cols} grid")

if __name__ == '__main__':
    # 파일 경로 설정
    model_file = Path.home() / 'Documents' / 'WorkSpace' / 'phoneticConvergence' / 'src' / 'analysis' / 'formant_results_all_vowels_model_standard.xlsx'
    participant_file = Path.home() / 'Documents' / 'WorkSpace' / 'phoneticConvergence' / 'src' / 'analysis' / 'formant_results_all_vowels_participant_stage_zscore.xlsx'
    survey_file = Path.home() / 'Documents' / 'WorkSpace' / 'phoneticConvergence' / 'data' / 'experiment_data' / 'survey-latest.xlsx'
    
    # 사용 가능한 참가자 ID 목록 확인
    df_participant_all = pd.read_excel(participant_file)
    participant_ids = df_participant_all['participant_id'].unique()
    print(f"Available participant IDs: {participant_ids}")
    print(f"Total participants: {len(participant_ids)}")
    
    # 사용자 선택
    print("\nChoose plotting option:")
    print("1. Single participant plot")
    print("2. All participants subplot")
    print("3. Participants by gender subplot")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    # 데이터 타입 선택
    data_option = input("Use z-score values? (y/n, default: y): ").strip().lower()
    use_zscore = data_option != 'n'
    data_type = "z-score" if use_zscore else "original Hz values"
    print(f"Using {data_type} for plotting")
    
    # 저장 경로 선택
    save_option = input("Save image? (y/n, default: y): ").strip().lower()
    save_image = save_option != 'n'
    
    if save_image:
        save_dir = input("Enter save directory (press Enter for current directory): ").strip()
        if not save_dir:
            save_dir = "."
        print(f"Images will be saved in: {save_dir}")
    
    if choice == '1':
        # 단일 참가자 플롯
        if len(participant_ids) > 0:
            participant_id = int(input(f"Enter participant ID (available: {list(participant_ids)}): "))
            if participant_id in participant_ids:
                plot_formant_chart(participant_id, model_file, participant_file, survey_file, save_dir, use_zscore)
            else:
                print("Invalid participant ID")
        else:
            print("No participant data found.")
    
    elif choice == '2':
        # 모든 참가자 subplot
        max_per_row = int(input("Enter max participants per row (default 4): ") or "4")
        plot_all_participants_subplot(model_file, participant_file, survey_file, 
                                     max_participants_per_row=max_per_row, save_dir=save_dir, use_zscore=use_zscore)
    
    elif choice == '3':
        # 성별별 참가자 subplot
        max_per_row = int(input("Enter max participants per row (default 4): ") or "4")
        plot_participants_by_gender_subplot(model_file, participant_file, survey_file, 
                                           max_participants_per_row=max_per_row, save_dir=save_dir, use_zscore=use_zscore)
    
    else:
        print("Invalid choice. Please run again and select 1, 2, or 3.")


# z-score norm 개인 내.