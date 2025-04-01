import os
import soundfile as sf
import numpy as np
from tqdm import tqdm

def increase_volume(input_path, output_path, volume_factor=2.0):
    """
    오디오 파일의 볼륨을 증가시킵니다.
    
    Args:
        input_path (str): 입력 파일 경로
        output_path (str): 출력 파일 경로
        volume_factor (float): 볼륨 증가 배수 (기본값: 2.0)
    """
    try:
        # 오디오 파일 읽기
        data, samplerate = sf.read(input_path)
        
        # 데이터가 2차원 배열인 경우 1차원으로 변환
        if len(data.shape) > 1:
            data = data.flatten()
        
        # 볼륨 증가
        amplified_data = data * volume_factor
        
        # 클리핑 방지 (값이 -1 또는 1을 넘지 않도록)
        amplified_data = np.clip(amplified_data, -1.0, 1.0)
        
        # 새로운 파일로 저장
        sf.write(output_path, amplified_data, samplerate)
        return True
    except Exception as e:
        print(f"오류 발생 ({input_path}): {str(e)}")
        return False

def process_directory(input_dir, output_dir, volume_factor=3.0):
    """
    디렉토리 내의 모든 WAV 파일을 처리합니다.
    
    Args:
        input_dir (str): 입력 디렉토리 경로
        output_dir (str): 출력 디렉토리 경로
        volume_factor (float): 볼륨 증가 배수
    """
    # 출력 디렉토리가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # WAV 파일 목록 가져오기
    wav_files = [f for f in os.listdir(input_dir) if f.endswith('.wav')]
    
    if not wav_files:
        print(f"'{input_dir}' 디렉토리에 WAV 파일이 없습니다.")
        return
    
    print(f"총 {len(wav_files)}개의 WAV 파일을 처리합니다.")
    
    # 진행 상황 표시를 위한 tqdm 사용
    for wav_file in tqdm(wav_files, desc="파일 처리 중"):
        input_path = os.path.join(input_dir, wav_file)
        output_path = os.path.join(output_dir, wav_file)
        
        if increase_volume(input_path, output_path, volume_factor):
            print(f"성공: {wav_file}")
        else:
            print(f"실패: {wav_file}")

def main():
    # 사용자로부터 입력 받기
    input_dir = input("처리할 WAV 파일이 있는 디렉토리 경로를 입력하세요: ").strip()
    output_dir = input("증가된 볼륨의 파일을 저장할 디렉토리 경로를 입력하세요: ").strip()
    input_dir = "./audio-sample/new"
    output_dir = "./audio-sample/new/4x"
    
    try:
        volume_factor = float(input("볼륨을 몇 배로 증가시킬까요? (기본값: 2.0): ").strip() or "2.0")
    except ValueError:
        print("올바른 숫자를 입력하지 않았습니다. 기본값 2.0을 사용합니다.")
        volume_factor = 2.0
    
    # 입력 디렉토리 확인
    if not os.path.exists(input_dir):
        print(f"입력 디렉토리 '{input_dir}'가 존재하지 않습니다.")
        return
    
    # 처리 시작
    print("\n볼륨 증가 처리를 시작합니다...")
    process_directory(input_dir, output_dir, volume_factor)
    print("\n처리가 완료되었습니다!")

if __name__ == "__main__":
    main() 