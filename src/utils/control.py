import parselmouth
from parselmouth import praat
from parselmouth.praat import call
import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import librosa
import librosa.display
import sounddevice as sd
from datetime import datetime
from tqdm import tqdm
import seaborn as sns
import matplotlib.patches as patches

filePath = "../audio-sample/short-version-phonetic/"
audio_list = os.listdir(filePath)
audio_list = [file for file in audio_list if file.endswith(".wav")]
audio_list.sort()

def plot_formant_distribution(audio_name, filePath, ax=None):    
    # 고정된 축 범위 설정
    F1_MIN, F1_MAX = 200, 1000    # F1 범위 (Hz)
    F2_MIN, F2_MAX = 500, 3000    # F2 범위 (Hz)
    
    # WAV 파일 불러오기
    sound = parselmouth.Sound(os.path.join(filePath, audio_name))
    time_points = np.arange(0, sound.duration, 0.01)
    f1_list = []
    f2_list = []
    
    # 포먼트 추출 (Burg 방식 사용)
    formants = sound.to_formant_burg(time_step=0.01, 
                                    max_number_of_formants=5.0,
                                    maximum_formant=5000.0, 
                                    window_length=0.025, 
                                    pre_emphasis_from=50.0)

    for time_point in time_points:
        # 특정 시간에서의 F1, F2 값 추출
        f1 = formants.get_value_at_time(1, time_point)
        f2 = formants.get_value_at_time(2, time_point)
        if (f1 and f2 and 
            np.isfinite(f1) and np.isfinite(f2) and
            F1_MIN <= f1 <= F1_MAX and 
            F2_MIN <= f2 <= F2_MAX and 
            (f2 - f1) >= 200):  # F2-F1 최소 차이
        f1_list.append(f1)
        f2_list.append(f2)

    formant_df = pd.DataFrame({"f1": f1_list, "f2": f2_list, "time": time_points[:len(f1_list)]})

    if len(formant_df) > 0:
    # 산점도 그리기
    scatter = sns.scatterplot(data=formant_df, 
                             x="f2",  # x축을 F2로 변경
                             y="f1",  # y축을 F1로 변경 
                         hue="time", 
                         palette="viridis", 
                         alpha=0.5, 
                         s=50,
                         ax=ax)

        # 축 범위 설정
        ax.set_xlim(F2_MAX, F2_MIN)  # F2 축 반전
        ax.set_ylim(F1_MAX, F1_MIN)  # F1 축 반전

    # 제목과 레이블 설정
    ax.set_title(f'포먼트 분포도: {audio_name}', fontsize=12, pad=10)
    ax.set_xlabel('F2 (Hz)', fontsize=10)
    ax.set_ylabel('F1 (Hz)', fontsize=10)

    # 컬러바 설정
    norm = plt.Normalize(formant_df['time'].min(), formant_df['time'].max())
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax).set_label('시간 (초)', fontsize=8)

    # 그리드 설정
    ax.grid(True, linestyle='--', alpha=0.7)
    
    return formant_df

# 메인 코드
# 기본 스타일 설정
sns.set_style("whitegrid")
# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.sans-serif'] = ['AppleGothic']  # macOS의 경우

# 서브플롯 개수 계산
n_plots = len(audio_list)
n_cols = 2  # 열 개수 지정
n_rows = (n_plots + 1) // 2  # 행 개수 계산 (올림)

# Figure 생성
fig = plt.figure(figsize=(15, 5*n_rows))

# 각 오디오 파일에 대해 서브플롯 생성
for idx, audio_name in enumerate(audio_list, 1):
    ax = fig.add_subplot(n_rows, n_cols, idx)
    formant_df = plot_formant_distribution(audio_name, filePath, ax)
    
    # 통계 정보를 타이틀 아래에 추가
    if len(formant_df) > 0:
    stats = formant_df.describe().round(2)
    ax.text(0.05, 0.95, 
            f'F1 평균: {stats["f1"]["mean"]:.0f}Hz\nF2 평균: {stats["f2"]["mean"]:.0f}Hz',
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment='top')

# 전체 레이아웃 조정
plt.tight_layout()
plt.show()