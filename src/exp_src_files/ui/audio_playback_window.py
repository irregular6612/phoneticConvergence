import tkinter as tk
import time
import os
from datetime import datetime
from audio import AudioPlayer
import sounddevice as sd


class AudioPlaybackWindow:
    def __init__(self, participant_id, folder_path):
        self.window = tk.Tk()
        self.window.title('음성 청취 - 2단계')
        self.window.geometry('400x200')
        
        # 안내 메시지
        self.instruction_label = tk.Label(self.window, text='스페이스바를 눌러 다음 음성을 들으세요', font=('Arial', 12))
        self.instruction_label.pack(expand=True)
        
        # 데이터 저장용 변수들
        self.participant_id = participant_id
        self.folder_path = folder_path
        self.timing_data = []
        self.start_time = None
        
        # 오디오 플레이어 초기화
        self.player = AudioPlayer(folder_path)
        self.remaining_files = self.player.audio_files.copy()
        
        # 키 바인딩
        self.window.bind('<space>', self.next_audio)
        self.window.bind('<Return>', self.close_window)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 첫 음성 재생
        self.play_next_audio()
        
    def play_next_audio(self):
        if self.remaining_files:
            audio_file = self.remaining_files.pop()
            self.current_file = os.path.basename(audio_file)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            
            # 현재 재생 중인 오디오 파일의 리스트 정보 확인
            current_list = 'list1' if 'list1' in audio_file else 'list2'
            
            # 리스트에 따라 다른 메시지 표시 (3단계에서만)
            if self.current_stage == 3:
                if current_list == self.selected_lists:
                    message = "20대 한국인 남성"
                    self.show_speaker_image(is_ai=False)
                else:
                    message = "AI 아바타 GT-25"
                    self.show_speaker_image(is_ai=True)
            else:  # 2단계
                message = "발음을 잘 들어주세요."
                self.show_speaker_image(is_ai=None)
                
            # 첫 번째 메시지 표시
            self.instruction_label.config(text=message)
            self.window.update()
            
            # 오디오 재생
            duration = self.player.play_audio(audio_file)
            
            # 오디오 재생이 끝날 때까지 대기
            while self.player.is_playing():
                time.sleep(0.1)
            
            # 오디오 재생이 끝나면 두 번째 메시지 표시
            self.instruction_label.config(text='소리내어 따라하신 후, 스페이스바를 눌러 다음으로 넘어가세요.')
            self.window.update()
            
            # 타이밍 데이터에 음성 파일과 시작 시간 기록
            self.timing_data.append({
                '음성파일': self.current_file,
                '시작시간': current_time,
                '단계': self.current_stage,
                '참가자번호': self.participant_id,
                '선택된_리스트': current_list
            })
        else:
            self.save_current_stage_data()
            
            # 2단계나 3단계가 끝날 때 녹음 중지
            if self.current_stage in [2, 3]:
                if hasattr(self, 'recorder') and self.recorder:
                    self.recorder.stop_recording()
            
            if self.player:
                sd.stop()
            
            self.instruction_label.config(text='')
            self.window.update()
            
            next_stage = self.current_stage + 1
            if next_stage <= 4:
                self.start_stage(next_stage)
            else:
                self.show_experiment_completion()

    def close_window(self, event):
        if not self.remaining_files:
            self.on_closing()
        
    def on_closing(self):
        sd.stop()  # 재생 중인 오디오 정지
        self.window.quit()
        
    def show(self):
        self.window.mainloop()
        return self.timing_data
