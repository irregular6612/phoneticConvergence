import parselmouth
from parselmouth import praat
import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def analyze_formants(wav_file_path, time_point=0.5, fig=None, subplot_position=None):
    """
    WAV 파일의 포먼트를 분석하고 시각화합니다.
    
    Args:
        wav_file_path (str): WAV 파일 경로
        time_point (float): 특정 시간 지점 (초 단위, 기본값: 0.5초)
        fig (matplotlib.figure.Figure, optional): 기존 figure 객체
        subplot_position (tuple, optional): (행, 열, 위치) 형태의 서브플롯 위치
    
    Returns:
        tuple: (figure 객체, F1, F2) 특정 시간 지점에서의 포먼트 값
    """
    # 한글 폰트 설정
    plt.rcParams['font.family'] = 'AppleGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    # WAV 파일 불러오기
    sound = parselmouth.Sound(wav_file_path)
    
    # 포먼트 추출 (Burg 방식 사용)
    formants = sound.to_formant_burg(time_step=0.01, 
                                    max_number_of_formants=5.0,
                                    maximum_formant=5000.0, 
                                    window_length=0.025, 
                                    pre_emphasis_from=50.0)
    
    # 특정 시간에서의 F1, F2 값 추출
    f1 = formants.get_value_at_time(1, time_point)
    f2 = formants.get_value_at_time(2, time_point)
    
    print(f"시간 {time_point}초에서의 F1: {f1} Hz, F2: {f2} Hz")
    
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
            pass
    
    # 새로운 figure 생성 또는 기존 figure 사용
    if fig is None:
        fig = plt.figure(figsize=(10, 8))
    
    # 서브플롯 위치 지정
    if subplot_position:
        ax = fig.add_subplot(*subplot_position)
    else:
        ax = fig.add_subplot(111)
    
    # F1-F2 공간에 모음 분포 시각화
    ax.scatter(f2_values, f1_values, alpha=0.5)
    ax.set_xlabel('F2 (헤르츠)')
    ax.set_ylabel('F1 (헤르츠)')
    ax.set_title('F1-F2 모음 공간 분포도')
    ax.invert_xaxis()  # F2 축 반전 (언어학 관례)
    ax.invert_yaxis()  # F1 축 반전 (언어학 관례)
    ax.grid(True)
    
    return fig, f1, f2

def convert_m4a_to_wav(m4a_path, wav_path):
    """
    M4A 파일을 WAV 형식으로 변환합니다.
    
    Args:
        m4a_path (str): M4A 파일 경로
        wav_path (str): 변환될 WAV 파일 경로
    
    Returns:
        str: 변환된 WAV 파일 경로
    """
    try:
        subprocess.run(['ffmpeg', '-i', m4a_path, '-y', wav_path], 
                      check=True, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        print(f"변환 완료: {m4a_path} -> {wav_path}")
        return wav_path
    except subprocess.CalledProcessError as e:
        print(f"변환 실패: {e}")
        return None

def main():
    # 파일 경로 입력 받기
    file_paths = input("분석할 오디오 파일 경로들을 쉼표로 구분하여 입력하세요: ").strip().split(',')
    file_paths = [path.strip() for path in file_paths]
    
    # 전체 그래프를 위한 figure 생성
    fig = plt.figure(figsize=(15 * len(file_paths), 8))
    
    for i, file_path in enumerate(file_paths):
        # 파일 확장자 확인
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.m4a':
            # M4A 파일인 경우 WAV로 변환
            wav_path = file_path.replace('.m4a', '.wav')
            wav_path = convert_m4a_to_wav(file_path, wav_path)
            if not wav_path:
                print(f"파일 변환 실패: {file_path}")
                continue
            file_path = wav_path
        elif file_ext != '.wav':
            print(f"지원하지 않는 파일 형식입니다: {file_path}")
            continue
        
        # 포먼트 분석 실행
        try:
            fig, f1, f2 = analyze_formants(file_path, fig=fig, subplot_position=(1, len(file_paths), i+1))
            print(f"\n{file_path} 분석 완료!")
        except Exception as e:
            print(f"분석 중 오류 발생 ({file_path}): {str(e)}")
    
    # 모든 그래프 표시
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main() 