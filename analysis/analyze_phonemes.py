import os
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import parselmouth
from parselmouth import praat
import sounddevice as sd
from tqdm import tqdm

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def load_audio(file_path):
    """
    오디오 파일을 로드합니다.
    
    Args:
        file_path (str): 오디오 파일 경로
    
    Returns:
        tuple: (y, sr) 오디오 데이터와 샘플링 레이트
    """
    try:
        # librosa를 사용하여 오디오 로드
        y, sr = librosa.load(file_path, sr=None)
        return y, sr
    except Exception as e:
        print(f"오디오 로드 중 오류 발생: {str(e)}")
        # parselmouth를 사용하여 대체 로드 시도
        try:
            sound = parselmouth.Sound(file_path)
            y = sound.values
            sr = sound.sampling_frequency
            return y, sr
        except Exception as e2:
            print(f"대체 로드 중 오류 발생: {str(e2)}")
            raise

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
        tuple: (f1_values, f2_values, times) F1, F2 포먼트 값과 시간축
    """
    sound = parselmouth.Sound(y, sr)
    formants = sound.to_formant_burg(time_step=0.01, 
                                    max_number_of_formants=5.0,
                                    maximum_formant=5000.0, 
                                    window_length=0.025, 
                                    pre_emphasis_from=50.0)
    
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
    energy = np.mean(mel_spec, axis=0)
    energy = (energy - np.min(energy)) / (np.max(energy) - np.min(energy))
    
    phonemes = []
    current_start = None
    current_type = None
    current_end = None
    
    for i in range(len(times)):
        if energy[i] > energy_threshold:
            if current_start is None:
                current_start = times[i]
                if i < len(f1_values) and f1_values[i] > 0 and f2_values[i] > 0:
                    current_type = 'vowel'
                else:
                    current_type = 'consonant'
            current_end = times[i]
        elif current_start is not None:
            if current_end - current_start >= min_duration:
                phonemes.append((current_start, current_end, current_type))
            current_start = None
            current_type = None
            current_end = None
    
    if current_start is not None and current_end - current_start >= min_duration:
        phonemes.append((current_start, current_end, current_type))
    
    return phonemes

def play_audio_segment(y, sr, start_time, end_time):
    """
    오디오의 특정 구간을 재생합니다.
    
    Args:
        y (np.ndarray): 오디오 데이터
        sr (int): 샘플링 레이트
        start_time (float): 시작 시간 (초)
        end_time (float): 종료 시간 (초)
    """
    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)
    segment = y[start_sample:end_sample]
    
    print("재생 중...", end='', flush=True)
    sd.play(segment, sr)
    sd.wait()
    print(" 완료")

def analyze_audio_file(file_path):
    """
    오디오 파일을 분석하고 자음/모음을 구분합니다.
    
    Args:
        file_path (str): 오디오 파일 경로
    
    Returns:
        tuple: (phonemes, y, sr) 음소 분석 결과, 오디오 데이터, 샘플링 레이트
    """
    print(f"파일 분석 시작: {file_path}")
    
    y, sr = load_audio(file_path)
    print(f"오디오 로드 완료: 샘플링 레이트 {sr}Hz")
    
    mel_spec, times = create_mel_spectrogram(y, sr)
    print(f"Mel-spectrogram 생성 완료: {len(times)} 프레임")
    
    f1_values, f2_values, formant_times = analyze_formants(y, sr)
    print(f"포먼트 분석 완료: {len(f1_values)} 포인트")
    
    phonemes = detect_phonemes(mel_spec, times, f1_values, f2_values)
    print(f"음소 구분 완료: {len(phonemes)} 개의 음소 발견")
    
    return phonemes, y, sr

def save_results(file_path, phonemes):
    """
    분석 결과를 텍스트 파일로 저장합니다.
    
    Args:
        file_path (str): 원본 오디오 파일 경로
        phonemes (list): 음소 분석 결과
    """
    result_path = file_path.replace('.wav', '_analysis.txt')
    
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write("음소 분석 결과\n")
        f.write("=" * 50 + "\n")
        for i, (start, end, phoneme_type) in enumerate(phonemes):
            f.write(f"{i+1}. {start:.3f}s - {end:.3f}s: {phoneme_type}\n")
    
    print(f"분석 결과가 저장되었습니다: {result_path}")

def analyze_audio_directory(directory_path):
    """
    지정된 디렉토리 내의 모든 WAV 파일을 분석합니다.
    
    Args:
        directory_path (str): 분석할 디렉토리 경로
    """
    wav_files = [f for f in os.listdir(directory_path) if f.endswith('.wav')]
    
    print(f"총 {len(wav_files)}개의 WAV 파일을 찾았습니다.")
    
    for wav_file in tqdm(wav_files):
        file_path = os.path.join(directory_path, wav_file)
        print(f"\n분석 중: {wav_file}")
        
        try:
            phonemes, y, sr = analyze_audio_file(file_path)
            save_results(file_path, phonemes)
            
            for i, (start, end, phoneme_type) in enumerate(phonemes):
                print(f"\n{phoneme_type} {i+1} 재생 중...")
                play_audio_segment(y, sr, start, end)
                input("다음 음소로 넘어가려면 Enter를 누르세요...")   
                
        except Exception as e:
            print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    filePath = "../../../../Desktop/results/participant_1"
    analyze_audio_directory(filePath) 