import sounddevice as sd
import numpy as np
import soundfile as sf
import os   
import sys
from audio import AudioConstants
from datetime import datetime

class AudioRecorder:
    def __init__(self, device_index, folder_path=None):
        self.device_index = device_index
        self.folder_path = folder_path
        self.recording = False
        self.stream = None
        self.frames = []
        
    def start_recording(self, filename):
        if self.recording:
            return
            
        self.frames = []
        # 현재 시간 정보를 포함한 파일 이름 생성
        current_time = datetime.now()
        time_str = current_time.strftime('%Y%m%d_%H%M')
        
        # 참가자 ID와 단계 정보 추출
        participant_id = filename.split('_')[0]
        stage = filename.split('stage')[1]
        
        # 새로운 파일 이름 생성
        new_filename = f"{participant_id}_stage{stage}_{time_str}"
        
        # 참가자 폴더 경로에 파일 저장
        if self.folder_path:
            self.filename = os.path.join(self.folder_path, new_filename + '.wav')
        else:
            self.filename = new_filename + '.wav'
            
        self.recording = True
        
        def callback(indata, frames, time, status):
            if status:
                print(f'Error: {status}')
            if self.recording:
                self.frames.append(indata.copy())
        
        self.stream = sd.InputStream(
            device=self.device_index,
            channels=1,
            samplerate=AudioConstants.SAMPLE_RATE,
            callback=callback
        )
        self.stream.start()
        
    def stop_recording(self):
        if not self.recording:
            return
            
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        if self.frames:
            data = np.concatenate(self.frames, axis=0)
            sf.write(self.filename, data, AudioConstants.SAMPLE_RATE)
            self.frames = []
