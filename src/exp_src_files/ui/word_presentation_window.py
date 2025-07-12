import tkinter as tk
import time
import os
import random
from datetime import datetime
from audio import AudioRecorder

class WordPresentationWindow:
    def __init__(self, participant_id, folder_path, stage):
        # 현재 시간을 기반으로 랜덤 시드 설정
        current_time = int(datetime.now().timestamp() * 1000)
        random.seed(current_time)
        
        self.window = tk.Tk()
        self.window.title(f'단어 제시 - {stage}단계')
        self.window.geometry('400x200')
        
        # 단어 표시 레이블
        self.word_label = tk.Label(self.window, text='', font=('Arial', 24))
        self.word_label.pack(expand=True)
        
        # 안내 메시지
        self.instruction_label = tk.Label(self.window, text='단어를 읽고, 스페이스바를 눌러 다음 단어로 넘어가세요', font=('Arial', 12))
        self.instruction_label.pack()
        
        # 데이터 저장용 변수들
        self.participant_id = participant_id
        self.folder_path = folder_path
        self.timing_data = []
        self.current_word = None
        self.start_time = None
        self.stage = stage
        
        # 남은 단어 리스트 초기화
        self.remaining_words = WORDS.copy()
        random.shuffle(self.remaining_words)
        
        # 타이밍 데이터에 랜덤 시드 정보 추가
        self.random_seed = current_time
        
        # 녹음기 초기화
        audio_file = os.path.join(folder_path, f'participant_{participant_id}_recording_{stage}단계.wav')
        self.recorder = AudioRecorder(self.selected_device)
        
        # 키 바인딩
        self.window.bind('<space>', self.next_word)
        self.window.bind('<Return>', self.close_window)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 첫 단어 표시 및 녹음 시작
        self.show_next_word()
        self.recorder.start_recording(f"{self.participant_id}_stage{self.stage}")

    def show_next_word(self):
        if self.current_word_index < len(self.words):
            word = self.words[self.current_word_index]
            self.main_label.config(text=word)
            self.instruction_label.config(text='단어를 소리내어 읽어주신 후 스페이스바를 눌러 다음 단어로 넘어가세요.')
            self.current_word_index += 1
            self.start_time = time.time()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            
            if self.current_stage in [1, 2, 6]:  # 1단계, 1단계 반복, 4단계
                self.recorder.start_recording(f"{self.participant_id}_stage{self.current_stage}")
                # 타이밍 데이터에 단어와 시작 시간 기록
                self.timing_data.append({
                    '단어': word,
                    '시작시간': current_time,
                    '단계': self.current_stage,
                    '참가자번호': self.participant_id,
                    '선택된_리스트': self.selected_lists
                })
        else:
            self.save_current_stage_data()
            
            if self.recorder:
                self.recorder.stop_recording()
            
            self.main_label.config(text='')
            self.instruction_label.config(text='')
            self.window.update()
            
            next_stage = self.current_stage + 1
            if next_stage <= 6:  # 6단계까지 진행
                self.start_stage(next_stage)
            else:
                self.show_experiment_completion()

    def next_word(self, event):
        end_time = time.time()
        duration = end_time - self.start_time
        
        # 타이밍 데이터 저장
        self.timing_data.append({
            '단어': self.current_word,
            '제시시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '지속시간(초)': round(duration, 3)
        })
        
        self.show_next_word()
    
    def close_window(self, event):
        if not self.remaining_words:  # 모든 단어를 다 보여준 후에만 동작
            self.on_closing()
        
    def on_closing(self):
        # 녹음 중지
        self.recorder.stop_recording()
        self.window.quit()
        
    def show(self):
        self.window.mainloop()
        return self.timing_data

    def show_experiment_completion(self):
        """실험 종료 화면을 표시하고 키 바인딩을 비활성화합니다."""
        # 키 바인딩 제거
        self.window.unbind('<space>')
        self.window.unbind('<Return>')
        
        # 기존 위젯들 제거
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # 새로운 레이블과 버튼 생성
        completion_label = tk.Label(
            self.window,
            text='실험이 모두 종료되었습니다.\n참여해 주셔서 감사합니다.',
            font=('Arial', 48)
        )
        completion_label.pack(pady=100)
        
        exit_button = tk.Button(
            self.window,
            text="종료",
            command=self.window.quit,
            font=('Arial', 18)
        )
        exit_button.pack(pady=40)
