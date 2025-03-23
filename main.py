import parselmouth
from parselmouth import praat
import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정
# macOS에서 사용 가능한 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'  # macOS의 기본 한글 폰트
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 오디오 파일 경로
m4a_file_path = "./audio-sample/a.m4a"
wav_file_path = "./audio-sample/a_converted.wav"

# m4a 파일을 WAV로 변환 (ffmpeg 사용)
def convert_m4a_to_wav(m4a_path, wav_path):
    try:
        # ffmpeg를 사용하여 m4a를 wav로 변환
        subprocess.run(['ffmpeg', '-i', m4a_path, '-y', wav_path], 
                      check=True, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        print(f"변환 완료: {m4a_path} -> {wav_path}")
        return wav_path
    except subprocess.CalledProcessError as e:
        print(f"변환 실패: {e}")
        return None

# 변환된 WAV 파일이 없으면 변환 실행
if not os.path.exists(wav_file_path):
    convert_m4a_to_wav(m4a_file_path, wav_file_path)

# 변환된 WAV 파일 불러오기
sound = parselmouth.Sound(wav_file_path)

# 포먼트 추출 (Burg 방식 사용)
formants = sound.to_formant_burg(time_step=0.01, 
                                max_number_of_formants=5.0,
                                maximum_formant=5000.0, 
                                window_length=0.025, 
                                pre_emphasis_from=50.0)

# 특정 시간에서의 F1, F2 값 추출
time = 0.5  # 0.5초 지점에서의 포먼트 값 (예시)
f1 = formants.get_value_at_time(1, time)  # 제1 포먼트(F1)
f2 = formants.get_value_at_time(2, time)  # 제2 포먼트(F2)

print(f"시간 {time}초에서의 F1: {f1} Hz, F2: {f2} Hz")

# 전체 오디오에 대한 F1, F2 값 추출 및 시각화
duration = sound.get_total_duration()
times = np.arange(0, duration, 0.01)
f1_values = []
f2_values = []

for t in times:
    try:
        f1_val = formants.get_value_at_time(1, t)
        f2_val = formants.get_value_at_time(2, t)
        if f1_val and f2_val:  # None이 아닌 경우만 추가
            f1_values.append(f1_val)
            f2_values.append(f2_val)
    except:
        pass  # 일부 시간에서는 포먼트 값을 얻지 못할 수 있음

# F1-F2 공간에 모음 분포 시각화
plt.figure(figsize=(10, 8))
plt.scatter(f2_values, f1_values, alpha=0.5)
plt.xlabel('F2 (헤르츠)')
plt.ylabel('F1 (헤르츠)')
plt.title('F1-F2 모음 공간 분포도')
plt.gca().invert_xaxis()  # F2 축 반전 (언어학 관례)
plt.gca().invert_yaxis()  # F1 축 반전 (언어학 관례)
plt.grid(True)
plt.show() 