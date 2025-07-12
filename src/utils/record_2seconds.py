import sounddevice as sd
import soundfile as sf
import numpy as np
import time
from datetime import datetime

def record_audio(duration=1.5, sample_rate=44100):
    """
    1.5초 동안 오디오를 녹음하고 저장하는 함수
    
    Args:
        duration (float): 녹음 시간 (초)
        sample_rate (int): 샘플링 레이트
    """
    print(f"{duration}초 동안 녹음을 시작합니다...")
    
    # 녹음 시작
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    
    # 녹음이 완료될 때까지 대기
    sd.wait()
    
    # 현재 시간을 파일명에 포함
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}.wav"
    
    # 녹음된 오디오 저장
    sf.write(filename, recording, sample_rate)
    print(f"녹음이 완료되었습니다. 파일명: {filename}")

if __name__ == "__main__":
    try:
        record_audio()
    except KeyboardInterrupt:
        print("\n녹음이 중단되었습니다.")
    except Exception as e:
        print(f"오류 발생: {str(e)}") 