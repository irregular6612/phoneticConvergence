import librosa
import librosa.display
import librosa.effects as effects
import numpy as np
import matplotlib.pyplot as plt
import parselmouth
from parselmouth import praat
import os
import sounddevice as sd

def load_audio(file_path):
    """
    오디오 파일을 로드합니다.
    
    Args:
        file_path (str): 오디오 파일 경로
    
    Returns:
        tuple: (y, sr) 오디오 데이터와 샘플링 레이트
    """
    y, sr = librosa.load(file_path, sr=None)
    return y, sr

def create_mel_spectrogram(y, sr, n_mels=128):
    """
    Mel-spectrogram을 생성합니다.
    
    Args:
        y (np.ndarray): 오디오 데이터
        sr (int): 샘플링 레이트
        n_mels (int): Mel 필터뱅크 개수
    
    Returns:
        tuple: (mel_spec, times) Mel-spectrogram과 시간축
    """
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    times = librosa.times_like(mel_spec, sr=sr)
    return mel_spec_db, times

def analyze_formants(y, sr):
    """
    포먼트를 분석합니다.
    
    Args:
        y (np.ndarray): 오디오 데이터
        sr (int): 샘플링 레이트
    
    Returns:
        tuple: (f1, f2) F1과 F2 포먼트 값
    """
    # numpy 배열을 Praat Sound 객체로 변환
    sound = parselmouth.Sound(y, sr)
    
    # 포먼트 추출
    formants = sound.to_formant_burg(time_step=0.01, 
                                    max_number_of_formants=5.0,
                                    maximum_formant=5000.0, 
                                    window_length=0.025, 
                                    pre_emphasis_from=50.0)
    
    # 시간에 따른 F1, F2 값 추출
    duration = sound.get_total_duration()
    times = np.arange(0, duration, 0.01)
    f1_values = []
    f2_values = []
    
    for t in times:
        try:
            f1 = formants.get_value_at_time(1, t)
            f2 = formants.get_value_at_time(2, t)
            if f1 and f2:
                f1_values.append(f1)
                f2_values.append(f2)
        except:
            pass
    
    return f1_values, f2_values, times

def detect_phonemes(mel_spec, times, f1_values, f2_values, energy_threshold=0.3, min_duration=0.05):
    """
    자음과 모음을 감지합니다.
    
    Args:
        mel_spec (np.ndarray): Mel-spectrogram
        times (np.ndarray): 시간축
        f1_values (list): F1 포먼트 값
        f2_values (list): F2 포먼트 값
        energy_threshold (float): 에너지 임계값
        min_duration (float): 최소 음소 지속 시간 (초)
    
    Returns:
        list: [(시작 시간, 종료 시간, 음소 타입), ...]
    """
    # 에너지 계산
    energy = np.mean(mel_spec, axis=0)
    energy = (energy - np.min(energy)) / (np.max(energy) - np.min(energy))
    
    # 에너지 임계값을 기준으로 음소 구분
    phonemes = []
    current_start = None
    current_type = None
    current_end = None
    
    for i in range(len(times)):
        if energy[i] > energy_threshold:
            if current_start is None:
                current_start = times[i]
                # F1, F2 값이 있는 경우 모음으로 판단
                if i < len(f1_values) and f1_values[i] > 0 and f2_values[i] > 0:
                    current_type = 'vowel'
                else:
                    current_type = 'consonant'
            current_end = times[i]
        elif current_start is not None:
            # 최소 지속 시간 확인
            if current_end - current_start >= min_duration:
                phonemes.append((current_start, current_end, current_type))
            current_start = None
            current_type = None
            current_end = None
    
    # 마지막 음소 처리
    if current_start is not None and current_end - current_start >= min_duration:
        phonemes.append((current_start, current_end, current_type))
    
    # 너무 짧은 구간 병합
    merged_phonemes = []
    if phonemes:
        current_start, current_end, current_type = phonemes[0]
        for start, end, phoneme_type in phonemes[1:]:
            if phoneme_type == current_type and start - current_end < min_duration:
                current_end = end
            else:
                merged_phonemes.append((current_start, current_end, current_type))
                current_start, current_end, current_type = start, end, phoneme_type
        merged_phonemes.append((current_start, current_end, current_type))
    
    return merged_phonemes

def visualize_results(y, sr, mel_spec, times, phonemes):
    """
    분석 결과를 시각화합니다.
    
    Args:
        y (np.ndarray): 오디오 데이터
        sr (int): 샘플링 레이트
        mel_spec (np.ndarray): Mel-spectrogram
        times (np.ndarray): 시간축
        phonemes (list): 음소 구분 결과
    """
    plt.figure(figsize=(15, 10))
    
    # 파형
    plt.subplot(3, 1, 1)
    librosa.display.waveshow(y, sr=sr)
    plt.title('Waveform')
    
    # Mel-spectrogram
    plt.subplot(3, 1, 2)
    librosa.display.specshow(mel_spec, sr=sr, x_axis='time', y_axis='mel')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Mel-spectrogram')
    
    # 음소 구분 결과
    plt.subplot(3, 1, 3)
    for start, end, phoneme_type in phonemes:
        color = 'red' if phoneme_type == 'vowel' else 'blue'
        plt.axvspan(start, end, alpha=0.3, color=color)
    plt.plot(times, np.zeros_like(times), 'k-', alpha=0.3)
    plt.title('Phoneme Segmentation')
    plt.xlabel('Time (s)')
    
    plt.tight_layout()
    plt.show()

def play_audio_segment(y, sr, start_time, end_time):
    """
    오디오의 특정 구간을 재생합니다.
    
    Args:
        y (np.ndarray): 오디오 데이터
        sr (int): 샘플링 레이트
        start_time (float): 시작 시간 (초)
        end_time (float): 종료 시간 (초)
    """
    # 시작과 종료 샘플 인덱스 계산
    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)
    
    # 해당 구간 추출
    segment = y[start_sample:end_sample]
    
    # 재생
    print("재생 중...", end='', flush=True)
    sd.play(segment, sr)
    sd.wait()
    print(" 완료")
    return 0

def analyze_audio_file(file_path, phoneme_number=None):
    """
    오디오 파일을 분석하고 자음/모음을 구분합니다.
    
    Args:
        file_path (str): 오디오 파일 경로
        phoneme_number (int, optional): 재생할 음소 번호. None이면 모든 음소 정보만 반환
    """
    print(f"파일 분석 시작: {file_path}")
    
    # 오디오 로드
    y, sr = load_audio(file_path)
    print(f"오디오 로드 완료: 샘플링 레이트 {sr}Hz")
    
    # Mel-spectrogram 생성
    mel_spec, times = create_mel_spectrogram(y, sr)
    print(f"Mel-spectrogram 생성 완료: {len(times)} 프레임")
    
    # 포먼트 분석
    f1_values, f2_values, formant_times = analyze_formants(y, sr)
    print(f"포먼트 분석 완료: {len(f1_values)} 포인트")
    
    # 음소 구분
    phonemes = detect_phonemes(mel_spec, times, f1_values, f2_values)
    print(f"음소 구분 완료: {len(phonemes)} 개의 음소 발견")
    
    # 결과 시각화
    visualize_results(y, sr, mel_spec, times, phonemes)
    
    # 결과 출력
    print("\n음소 구분 결과:")
    for i, (start, end, phoneme_type) in enumerate(phonemes):
        print(f"{i+1}. {start:.2f}s - {end:.2f}s: {phoneme_type}")
    
    # 특정 음소 재생
    if phoneme_number is not None:
        try:
            idx = phoneme_number - 1
            if 0 <= idx < len(phonemes):
                start, end, phoneme_type = phonemes[idx]
                print(f"\n{phoneme_type} 재생 중...")
                play_audio_segment(y, sr, start, end)
            else:
                print(f"올바른 번호를 입력하세요. (1-{len(phonemes)})")
        except KeyboardInterrupt:
            print("\n재생이 중단되었습니다.")
    
    return phonemes, y, sr  # y와 sr도 함께 반환하도록 수정

def main():
    # 파일 경로 설정
    file_path = "../../../Desktop/results/participant_9999_20250331_0909/9999_stage3_20250331_0911.wav"
    
    if not os.path.exists(file_path):
        print("파일이 존재하지 않습니다.")
        return
    
    try:
        # 음소 분석만 수행
        phonemes, y, sr = analyze_audio_file(file_path)
        
        # 예시: 첫 번째 음소 재생
        if phonemes:
            analyze_audio_file(file_path, phoneme_number=1)
    except Exception as e:
        print(f"분석 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 