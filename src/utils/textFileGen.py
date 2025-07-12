import os 
import numpy as np
import pandas as pd
import librosa

resultPath = "/Users/bagjuhyeon/Desktop/results"
participant_list = [file for file in os.listdir(resultPath) if "participant" in file]
participant_list.sort()
participant_list


def create_textgrid(filename, duration, intervals):
    """
    TextGrid 파일을 생성하는 함수
    
    Parameters:
    - filename: 저장할 파일 경로
    - duration: 음원 길이 (초)
    - intervals: [(시작시간, 종료시간, 전사내용), ...] 형식의 리스트
    """
    with open(filename, 'w', encoding='utf-8') as f:
        # 헤더 작성
        f.write('File type = "ooTextFile"\n')
        f.write('Object class = "TextGrid"\n\n')
        
        # 시간 정보
        f.write(f'xmin = 0\n')
        f.write(f'xmax = {duration}\n')
        f.write('tiers? <exists>\n')
        f.write('size = 1\n')
        
        # IntervalTier 정보
        f.write('item []:\n')
        f.write('    item [1]:\n')
        f.write('        class = "IntervalTier"\n')
        f.write('        name = "transcription"\n')
        f.write(f'        xmin = 0\n')
        f.write(f'        xmax = {duration}\n')
        f.write(f'        intervals: size = {len(intervals)}\n')
        
        # 각 구간 정보 작성
        for i, (start, end, text) in enumerate(intervals, 1):
            f.write(f'        intervals [{i}]:\n')
            f.write(f'            xmin = {start}\n')
            f.write(f'            xmax = {end}\n')
            f.write(f'            text = "{text}"\n')



def get_wav_duration(wav_path):
    """
    WAV 파일의 길이를 초 단위로 반환
    """
    duration = librosa.get_duration(path=wav_path)
    return duration

class TextGridReader:
    def __init__(self, textgrid_path):
        self.textgrid_path = textgrid_path
        self.tiers_data = {}
        self.file_info = {}
        
    def read(self):
        """
        TextGrid 파일을 읽어서 구조화된 데이터로 변환
        """
        with open(self.textgrid_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # 파일 정보 읽기
            self._read_file_info(lines)
            
            # tier 정보 읽기
            self._read_tiers(lines)
            
        return self.tiers_data
    
    def _read_file_info(self, lines):
        """
        파일의 기본 정보 읽기
        """
        for line in lines:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                self.file_info[key] = value
    
    def _read_tiers(self, lines):
        """
        tier 정보 읽기
        """
        current_tier = None
        current_intervals = []
        reading_interval = False
        interval_data = {}
        
        for line in lines:
            line = line.strip()
            
            # tier 시작
            if 'name = "' in line:
                if current_tier is not None:
                    self.tiers_data[current_tier] = current_intervals
                current_tier = line.split('"')[1]
                current_intervals = []
                reading_interval = False
            
            # interval 시작
            elif 'intervals [' in line:
                reading_interval = True
                interval_data = {}
            
            # interval 데이터 읽기
            elif reading_interval and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                interval_data[key] = value
                
                # interval 완성
                if 'text' in interval_data:
                    start = float(interval_data['xmin'])
                    end = float(interval_data['xmax'])
                    text = interval_data['text']
                    current_intervals.append((start, end, text))
                    reading_interval = False
        
        # 마지막 tier 추가
        if current_tier is not None:
            self.tiers_data[current_tier] = current_intervals
    
    def get_tier_names(self):
        """
        tier 이름 목록 반환
        """
        return list(self.tiers_data.keys())
    
    def get_intervals_by_tier(self, tier_name):
        """
        특정 tier의 interval 목록 반환
        """
        return self.tiers_data.get(tier_name, [])
    
    def get_total_duration(self):
        """
        전체 음성 길이 반환
        """
        return float(self.file_info.get('xmax', 0))

import parselmouth
import numpy as np

def get_average_formants(wav_path, start_time, end_time, time_step=0.01):
    """
    특정 구간의 평균 포먼트 값 계산
    
    Parameters:
    - wav_path: WAV 파일 경로
    - start_time: 시작 시간 (초)
    - end_time: 종료 시간 (초)
    - time_step: 시간 간격 (초)
    
    Returns:
    - avg_f1, avg_f2: 평균 F1, F2 값 (Hz)
    """
    # 음성 파일 로드
    snd = parselmouth.Sound(wav_path)

    # Formant 객체 생성 (Praat의 Formant settings와 동일한 파라미터 사용)
    formant = snd.to_formant_burg(
        max_number_of_formants=5,  # Praat 기본값: 5
        maximum_formant=5500,      # Praat 기본값: 5500 Hz (여성)
        window_length=0.025,       # Praat 기본값: 0.025초
        pre_emphasis_from=50,      # Praat 기본값: 50 Hz
        time_step=0.025/4 # 시간 간격
    )
    
    # 시간 포인트 생성
    time_points = np.arange(start_time, end_time, time_step)
    
    # 각 시간 포인트에서의 F1, F2 값 수집
    f1_values = []
    f2_values = []
    
    for time in time_points:
        f1 = formant.get_value_at_time(1, time)
        f2 = formant.get_value_at_time(2, time)
        
        # 유효한 값만 수집 (NaN이 아닌 경우)
        if not np.isnan(f1):
            f1_values.append(f1)
        if not np.isnan(f2):
            f2_values.append(f2)
    
    # 평균값 계산
    avg_f1 = np.mean(f1_values) if f1_values else None
    avg_f2 = np.mean(f2_values) if f2_values else None
    
    return avg_f1, avg_f2

def detect_formants(participant_path, textGrid_name):
    if not os.path.exists(participant_path):
        raise ValueError(f"없는 디렉토리: {participant_path}")

    textgrid_path = os.path.join(participant_path, "output-new", textGrid_name)
    reader = TextGridReader(textgrid_path)
    try:
        # TextGrid 파일 읽기
        tiers_data = reader.read()
        
        # 파일 정보 출력
        print("파일 정보:")
        print(f"전체 길이: {reader.get_total_duration():.3f}초")
        print(f"Tier 목록: {reader.get_tier_names()}")
        print("\n" + "="*50)
        
        # 각 tier의 내용 출력
        phoneme_cnt = 0
        phonemes = []
        f1_values = []
        f2_values = []
        for tier_name in reader.get_tier_names():
            # 단어를 분석하는게 아니라, 모음만 포먼트 딸거니까,,
            if tier_name == "words":
                continue

            print(f"\nTier: {tier_name}")
            print("-"*30)
            
            intervals = reader.get_intervals_by_tier(tier_name)
            print(type(intervals))
            for start, end, text in intervals:
                if text == "":
                    continue
            
                if text == "spn":
                    phoneme_cnt+=2
                    print(f"구간 {start:.2f}-{end:.2f}초의 평균 포먼트 값:")
                    print("detection failed.")
                    print(f"F1: None")
                    print(f"F2: None")
                    phonemes.append(None)
                    phonemes.append(None)
                    f1_values.append(None)
                    f1_values.append(None)
                    f2_values.append(None)
                    f2_values.append(None)
                    continue


                elif text not in ["ɐ","ɐː", "ɛ", "ɛː", "i", "iː", "o", "oː", "u", "uː"]:
                    continue
                print(f"phoneme: {text}")
                phoneme_cnt+=1
                wav_file_name = textGrid_name.replace(".TextGrid", ".wav")
                avg_f1, avg_f2 = get_average_formants(os.path.join(participant_path, wav_file_name), start, end)
    
                if avg_f1 is not None and avg_f2 is not None:
                    print(f"구간 {start:.2f}-{end:.2f}초의 평균 포먼트 값:")
                    print(f"F1: {avg_f1:.2f} Hz")
                    print(f"F2: {avg_f2:.2f} Hz")
                    phonemes.append(text)
                    f1_values.append(avg_f1)
                    f2_values.append(avg_f2)
                else:
                    print("유효한 포먼트 값을 찾을 수 없습니다.")
                    phonemes.append(None)
                    f1_values.append(None)
                    f2_values.append(None)
                
                print("-"*20)
        print(f"total detected phonemes: {phoneme_cnt}")
        pandas_data = pd.DataFrame({
            "phoneme": phonemes,
            "f1": f1_values,
            "f2": f2_values
        })
        pandas_data.to_csv(os.path.join(participant_path, textGrid_name.replace(".TextGrid", ".csv")), index=False)
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")


from pathlib import Path
expPath = os.path.join(Path.home(), "Desktop", "results")
participant_list = [file for file in os.listdir(expPath) if "participant_LY" in file]
participant_list.sort()

# 개선: 병렬 처리 적용
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def process_participant(participant):
    participant_path = os.path.join(expPath, participant)
    file_list = os.listdir(participant_path)
    
    if len(file_list) == 0:
        print(ValueError(f"No files found in {participant_path}"))
        return
    
    if any(csv_file.endswith(".csv") for csv_file in file_list):
        print(f"{participant} already analyzed.")
        return
    textgrids_path = os.path.join(participant_path, "output-new")
    
    textgrids_list = os.listdir(textgrids_path)
    textgrids_list = [file for file in textgrids_list if file.endswith(".TextGrid")]
    textgrids_list.sort()
    for textgrid in textgrids_list:
        detect_formants(participant_path, textgrid)
    return 0

def main():
    # CPU 코어 수에 맞춰 병렬 처리
    with ProcessPoolExecutor(max_workers=int(0.4*multiprocessing.cpu_count())) as executor:
        results = list(executor.map(process_participant, participant_list))

if __name__ == "__main__":
    # Windows에서 실행할 경우 필요
    multiprocessing.freeze_support()
    main()