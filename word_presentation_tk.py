import tkinter as tk
from tkinter import messagebox, ttk
import os
import pandas as pd
import time
from datetime import datetime
import random
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import threading
import glob
import soundfile as sf
from config_manager import ConfigManager, ConfigWindow

class AudioConstants:
    SAMPLE_RATE = 44100
    CHANNELS = 1

# 단어 리스트 (예시)
WORDS = ['사과', '바나나', '오렌지', '포도', '키위', '딸기', '수박', '참외']

class AudioDeviceWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('녹음 장치 선택')
        self.window.geometry('400x250')
        
        # 안내 메시지
        tk.Label(
            self.window,
            text='녹음에 사용할 오디오 입력 장치를 선택해주세요.',
            font=('Arial', 12),
            wraplength=350
        ).pack(pady=20)
        
        # 장치 목록 가져오기
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        # 장치 선택 콤보박스
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            self.window,
            textvariable=self.device_var,
            width=50
        )
        
        # 콤보박스에 장치 목록 설정
        self.device_list = [f"{d['name']} (입력 채널: {d['max_input_channels']})" for d in input_devices]
        self.device_indices = [devices.index(d) for d in input_devices]
        self.device_combo['values'] = self.device_list
        
        # 기본 장치 선택
        default_device = sd.query_devices(kind='input')
        default_index = devices.index(default_device)
        try:
            default_list_index = self.device_indices.index(default_index)
            self.device_combo.current(default_list_index)
        except ValueError:
            if self.device_list:
                self.device_combo.current(0)
        
        self.device_combo.pack(pady=20)
        
        # 테스트 버튼
        tk.Button(
            self.window,
            text="마이크 테스트",
            command=self.test_recording,
            font=('Arial', 11)
        ).pack(pady=10)
        
        # 확인 버튼
        tk.Button(
            self.window,
            text="선택",
            command=self.confirm,
            font=('Arial', 11)
        ).pack(pady=10)
        
        self.selected_device = None
        
    def test_recording(self):
        try:
            selected_index = self.device_combo.current()
            if selected_index >= 0:
                device_index = self.device_indices[selected_index]
                
                # 테스트 녹음 시작
                messagebox.showinfo("마이크 테스트", "3초간 테스트 녹음을 시작합니다.\n아무 말씀이나 해주세요.")
                
                # 3초 녹음
                recording = sd.rec(
                    int(3 * AudioConstants.SAMPLE_RATE),
                    samplerate=AudioConstants.SAMPLE_RATE,
                    channels=AudioConstants.CHANNELS,
                    device=device_index
                )
                sd.wait()
                
                # 녹음 재생
                messagebox.showinfo("마이크 테스트", "녹음된 소리를 재생합니다.")
                sd.play(recording, AudioConstants.SAMPLE_RATE)
                sd.wait()
                
        except Exception as e:
            messagebox.showerror("오류", f"마이크 테스트 중 오류가 발생했습니다:\n{str(e)}")
    
    def confirm(self):
        selected_index = self.device_combo.current()
        if selected_index >= 0:
            self.selected_device = self.device_indices[selected_index]
            self.window.quit()
        else:
            messagebox.showerror("오류", "녹음 장치를 선택해주세요.")
    
    def show(self):
        self.window.mainloop()
        self.window.destroy()
        return self.selected_device

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
        # 참가자 폴더 경로에 파일 저장
        if self.folder_path:
            self.filename = os.path.join(self.folder_path, filename + '.wav')
        else:
            self.filename = filename + '.wav'
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

class AudioPlayer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.playing = False
        self.stream = None
        self.data = None
        self.samplerate = None
        self.current_frame = 0
        
    def play_audio(self, audio_file):
        if self.playing:
            return 0
            
        try:
            self.data, self.samplerate = sf.read(audio_file)
            duration = len(self.data) / self.samplerate
            self.current_frame = 0
            
            def callback(outdata, frames, time, status):
                if status:
                    print(f'Error: {status}')
                if self.current_frame + frames > len(self.data):
                    # 남은 데이터가 프레임보다 적을 경우
                    remaining = len(self.data) - self.current_frame
                    outdata[:remaining, 0] = self.data[self.current_frame:len(self.data)]
                    outdata[remaining:, 0] = 0
                    self.playing = False
                    raise sd.CallbackStop()
                else:
                    outdata[:, 0] = self.data[self.current_frame:self.current_frame + frames]
                    self.current_frame += frames
            
            self.stream = sd.OutputStream(
                channels=1,
                samplerate=self.samplerate,
                callback=callback
            )
            self.stream.start()
            self.playing = True
            return duration
        except Exception as e:
            print(f"오디오 재생 오류: {str(e)}")
            return 0
            
    def is_playing(self):
        return self.playing

    def stop(self):
        self.playing = False
        if self.stream:
            self.stream.stop()
            self.stream = None

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
                    message = "사람이 발음했습니다."
                else:
                    message = "AI가 발음했습니다."
            else:  # 2단계
                message = "발음을 듣고 따라하세요"
                
            # 첫 번째 메시지 표시
            self.instruction_label.config(text=message)
            self.window.update()
            
            # 1초 대기
            time.sleep(1)
            
            # 오디오 재생
            duration = self.player.play_audio(audio_file)
            
            # 오디오 재생이 끝날 때까지 대기
            while self.player.is_playing():
                time.sleep(0.1)
            
            # 오디오 재생이 끝나면 두 번째 메시지 표시
            self.instruction_label.config(text='스페이스바를 눌러 다음으로 넘어가세요')
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

class ParticipantInfoWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('참가자 정보')
        self.window.geometry('300x200')
        
        # 참가자 정보 입력 필드
        tk.Label(self.window, text='참가자 정보 입력').pack(pady=10)
        
        # 참가자 번호
        frame1 = tk.Frame(self.window)
        frame1.pack(pady=5)
        tk.Label(frame1, text='참가자 번호:').pack(side=tk.LEFT)
        self.participant_entry = tk.Entry(frame1)
        self.participant_entry.pack(side=tk.LEFT)
        
        # 나이
        frame2 = tk.Frame(self.window)
        frame2.pack(pady=5)
        tk.Label(frame2, text='만 나이:').pack(side=tk.LEFT)
        self.age_entry = tk.Entry(frame2)
        self.age_entry.pack(side=tk.LEFT)
        
        # 성별
        frame3 = tk.Frame(self.window)
        frame3.pack(pady=5)
        self.gender_var = tk.StringVar(value='남성')
        tk.Radiobutton(frame3, text='남성', variable=self.gender_var, value='남성').pack(side=tk.LEFT)
        tk.Radiobutton(frame3, text='여성', variable=self.gender_var, value='여성').pack(side=tk.LEFT)
        
        # 버튼
        frame4 = tk.Frame(self.window)
        frame4.pack(pady=10)
        tk.Button(frame4, text='시작', command=self.start).pack(side=tk.LEFT, padx=10)
        tk.Button(frame4, text='취소', command=self.cancel).pack(side=tk.LEFT)
        
        self.result = None
        
    def start(self):
        self.result = {
            'participant_id': self.participant_entry.get(),
            'age': self.age_entry.get(),
            'gender': self.gender_var.get()
        }
        self.window.quit()
        
    def cancel(self):
        self.window.quit()
        
    def show(self):
        self.window.mainloop()
        self.window.destroy()
        return self.result

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
        self.instruction_label = tk.Label(self.window, text='스페이스바를 눌러 다음 단어로 넘어가세요', font=('Arial', 12))
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
        if self.remaining_words:
            self.current_word = self.remaining_words.pop()
            self.word_label.config(text=self.current_word)
            self.instruction_label.config(text='스페이스바를 눌러 다음 단어로 넘어가세요')
            self.start_time = time.time()
        else:
            self.save_current_stage_data()
            
            if self.recorder:
                self.recorder.stop_recording()
            
            self.word_label.config(text='')
            self.instruction_label.config(text='')
            self.window.update()
            
            next_stage = self.stage + 1
            if next_stage <= 3:
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

class StageInstruction:
    @staticmethod
    def get_instruction(stage_number, selected_lists):
        instructions = {
            1: "1단계: 단어 읽기\n\n" + 
               "이제부터 화면에 단어들이 하나씩 제시됩니다.\n" +
               "각 단어를 소리내어 읽어주세요.\n" +
               "단어를 다 읽으신 후에는 스페이스바를 눌러주세요.\n" +
               "모든 단어를 읽으면 자동으로 다음 단계로 넘어갑니다.",
            2: "2단계: 음성 듣기\n\n" +
               "이제부터 녹음된 음성이 하나씩 재생됩니다.\n" +
               "각 음성을 듣고 따라 읽어주세요.\n" +
               "따라 읽기가 끝나면 스페이스바를 눌러주세요.\n" +
               "모든 음성을 들으면 자동으로 다음 단계로 넘어갑니다.",
            3: "3단계: 음성 듣기\n\n" +
               "이제부터 녹음된 음성이 하나씩 재생됩니다.\n" +
               "각 음성을 듣고 따라 읽어주세요.\n" +
               "따라 읽기가 끝나면 스페이스바를 눌러주세요.\n" +
               "모든 음성을 들으면 자동으로 다음 단계로 넘어갑니다.",
            4: "4단계: 단어 읽기\n\n" +
               "마지막으로 단어들을 한 번 더 읽어주시면 됩니다.\n" +
               "각 단어를 소리내어 읽어주세요.\n" +
               "단어를 다 읽으신 후에는 스페이스바를 눌러주세요.\n" +
               "모든 단어를 읽으면 실험이 종료됩니다."
        }
        return instructions.get(stage_number, "")

class DataManager:
    @staticmethod
    def save_stage_data(timing_data, participant_id, folder_path, current_stage):
        """현재 단계의 타이밍 데이터를 Excel 파일로 저장합니다."""
        if not timing_data:
            return
            
        df = pd.DataFrame(timing_data)
        
        # 열 순서 정렬
        columns_order = [
            '참가자번호', '단계', '단어', '음성파일', 
            '시작시간', '스페이스바_시간'
        ]
        # 존재하는 열만 선택
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        # Excel 파일 경로
        excel_path = os.path.join(folder_path, f"{participant_id}_experiment_data.xlsx")
        
        # 기존 파일이 있는지 확인
        if os.path.exists(excel_path):
            # 기존 파일 읽기
            with pd.ExcelFile(excel_path) as xls:
                # Info 시트는 그대로 유지
                info_df = pd.read_excel(xls, sheet_name='Info')
                
                # 기존 데이터 시트들 읽기
                existing_sheets = {}
                for sheet_name in xls.sheet_names:
                    if sheet_name != 'Info':
                        existing_sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
                
                # 현재 단계 데이터 추가
                existing_sheets[f'Stage{current_stage}'] = df
                
                # 모든 데이터를 하나의 파일로 저장
                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    info_df.to_excel(writer, sheet_name='Info', index=False)
                    for sheet_name, sheet_data in existing_sheets.items():
                        sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # 새 파일 생성
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Info 시트 생성
                info_df = pd.DataFrame({
                    '참가자번호': [participant_id],
                    '실험일시': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                    '녹음장치': [sd.query_devices(selected_device)['name']],
                    '실험 리스트': [selected_lists]
                })
                info_df.to_excel(writer, sheet_name='Info', index=False)
                # 현재 단계 데이터 저장
                df.to_excel(writer, sheet_name=f'Stage{current_stage}', index=False)

    @staticmethod
    def save_participant_info(participant_id, folder_path, participant_info, selected_device, selected_lists):
        """참가자 정보를 Excel 파일의 Info 시트에 저장합니다."""
        info_df = pd.DataFrame({
            '참가자번호': [participant_id],
            '성별': participant_info['gender'],
            '나이': participant_info['age'],
            '실험일시': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            '녹음장치': [sd.query_devices(selected_device)['name']],
            '실험 리스트': [selected_lists]
        })
        
        excel_path = os.path.join(folder_path, f"{participant_id}_experiment_data.xlsx")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            info_df.to_excel(writer, sheet_name='Info', index=False)

class MainExperimentWindow:
    def __init__(self, config):
        self.window = tk.Tk()
        self.window.title('단어 제시 실험')
        self.window.attributes('-fullscreen', True)
        
        # config에서 경로 설정
        self.config = config
        self.word_path = config['paths']['word_file']
        
        # 중앙 정렬을 위한 프레임 생성
        self.center_frame = tk.Frame(self.window)
        self.center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        self.main_label = tk.Label(self.center_frame, text='', font=('Arial', 64))
        self.main_label.pack(pady=50)
        
        self.instruction_label = tk.Label(self.center_frame, text='', font=('Arial', 36))
        self.instruction_label.pack(pady=30)
        
        self.current_stage = 0
        self.timing_data = []
        
        # 이벤트 핸들러 바인딩
        self.window.bind('<space>', self.handle_space_press)
        self.window.bind('<Return>', self.handle_return_press)
        
        # 하위 창들을 위한 변수
        self.current_dialog = None

    def show_experiment_intro(self):
        """전체 실험 설명을 보여주는 창을 표시합니다."""
        if self.current_dialog:
            self.current_dialog.destroy()
            
        instruction_frame = tk.Frame(self.window)
        instruction_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        intro_text = """
[실험 안내]

안녕하세요. 본 실험에 참여해 주셔서 감사합니다.

1. 실험 목적
이 실험은 음성 학습 과정에서 발생하는 발음 변화를 연구하기 위한 것입니다.
참가자 여러분의 발음이 어떻게 변화하는지 관찰하고 분석하여, 
음성 학습의 특성과 패턴을 이해하는 것이 목적입니다.

2. 실험 구성
실험은 총 4단계로 구성되어 있습니다:

1단계: 단어 읽기
- 화면에 제시되는 단어들을 소리내어 읽어주세요.
- 각 단어를 읽은 후 스페이스바를 눌러 다음 단어로 넘어갑니다.

2단계: 음성 듣기
- 녹음된 음성을 듣고 따라 읽어주세요.
- 각 음성을 듣고 따라 읽은 후 스페이스바를 눌러 다음으로 넘어갑니다.

3단계: 음성 듣기
- 이전 단계에서 들은 음성들을 다시 한번 따라 읽어주세요.
- 각 음성을 듣고 따라 읽은 후 스페이스바를 눌러 다음으로 넘어갑니다.

4단계: 단어 읽기
- 마지막으로 단어들을 한 번 더 읽어주세요.
- 각 단어를 읽은 후 스페이스바를 눌러 다음 단어로 넘어갑니다.

3. 주의사항
- 모든 단계에서 마이크를 통해 음성이 녹음됩니다.
- 각 단계 시작 전에 마이크가 정상적으로 작동하는지 확인해주세요.
- 실험 중에는 조용한 환경에서 진행해주세요.
- 실험 중간에 중단이 필요한 경우 언제든 말씀해 주세요.

4. 실험 시간
- 전체 실험은 약 15-20분 정도 소요됩니다.
- 각 단계는 약 3-5분 정도 소요됩니다.

5. 보상
- 실험 완료 후 소정의 보상이 제공됩니다.

위 내용을 모두 읽고 이해하셨다면, '시작하기' 버튼을 눌러 실험을 시작해주세요.
"""
        
        instruction_text = tk.Label(
            instruction_frame,
            text=intro_text,
            font=('Arial', 24),
            justify=tk.CENTER,
            wraplength=800
        )
        instruction_text.pack(expand=True, padx=20, pady=20)
        
        start_button = tk.Button(
            instruction_frame,
            text="시작하기",
            command=lambda: self.start_stage_after_intro(instruction_frame),
            font=('Arial', 24)
        )
        start_button.pack(pady=40)
        
        self.current_dialog = instruction_frame

    def start_stage_after_intro(self, instruction_frame):
        """전체 실험 설명 창을 닫고 1단계를 시작합니다."""
        instruction_frame.destroy()
        self.current_dialog = None
        self.start_stage(1)

    def start_experiment(self, participant_id, folder_path, selected_device, selected_lists, participant_info):
        """실험을 시작합니다."""
        self.participant_id = participant_id
        self.folder_path = folder_path
        self.selected_device = selected_device
        self.selected_lists = selected_lists
        
        # 참가자 정보 저장
        DataManager.save_participant_info(
            participant_id, 
            folder_path, 
            participant_info, 
            selected_device, 
            selected_lists
        )
        
        self.player = AudioPlayer(self.folder_path)
        self.recorder = AudioRecorder(selected_device, folder_path)
        
        # 전체 실험 설명 표시
        self.show_experiment_intro()

    def save_current_stage_data(self):
        """현재 단계의 데이터를 저장합니다."""
        DataManager.save_stage_data(
            self.timing_data,
            self.participant_id,
            self.folder_path,
            self.current_stage
        )

    def show_stage_instruction(self, stage_number):
        """각 단계별 안내 창을 표시합니다."""
        if self.current_dialog:
            self.current_dialog.destroy()
            
        instruction_frame = tk.Frame(self.window)
        instruction_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        instruction_text = tk.Label(
            instruction_frame,
            text=StageInstruction.get_instruction(stage_number, self.selected_lists),
            font=('Arial', 36),
            justify=tk.CENTER,
            wraplength=800
        )
        instruction_text.pack(expand=True, padx=20, pady=20)
        
        start_button = tk.Button(
            instruction_frame,
            text="시작하기",
            command=lambda: self.start_stage_after_instruction(instruction_frame, stage_number),
            font=('Arial', 24)
        )
        start_button.pack(pady=40)
        
        self.current_dialog = instruction_frame

    def handle_space_press(self, event):
        """스페이스바 이벤트 핸들러"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        if self.current_stage in [1, 4]:
            if self.timing_data:
                self.timing_data[-1]['스페이스바_시간'] = current_time
            self.show_next_word()
        elif self.current_stage in [2, 3]:
            if hasattr(self, 'player') and not self.player.is_playing():
                if self.timing_data:
                    self.timing_data[-1]['스페이스바_시간'] = current_time
                self.play_next_audio()

    def handle_return_press(self, event):
        """엔터키 이벤트 핸들러"""
        if not self.remaining_files:
            self.on_closing()

    def start_stage_after_instruction(self, instruction_frame, stage_number):
        """안내 창을 닫고 단계를 시작합니다."""
        instruction_frame.destroy()
        self.current_dialog = None
        self.initialize_stage(stage_number)

    def initialize_stage(self, stage_number):
        """실제 단계 초기화를 수행합니다."""
        self.current_stage = stage_number
        self.timing_data = []
        
        if self.current_stage == 1:
            self.main_label.config(text='단어를 소리내어 읽어주세요')
            self.instruction_label.config(text='스페이스바를 눌러 시작하세요')
            self.words = self.load_words()
            random.seed(42)
            random.shuffle(self.words)
            self.current_word_index = 0
            
        elif self.current_stage == 2 or self.current_stage == 3:
            self.main_label.config(text='음성을 듣고 따라 읽어주세요')
            self.instruction_label.config(text='스페이스바를 눌러 시작하세요')
            self.load_audio_files()
            # 녹음기 초기화 확인
            if not hasattr(self, 'recorder') or not self.recorder:
                self.recorder = AudioRecorder(self.selected_device, self.folder_path)
            # 2단계나 3단계 시작 시 연속 녹음 시작
            self.recorder.start_recording(f"{self.participant_id}_stage{self.current_stage}")
            
        elif self.current_stage == 4:
            self.main_label.config(text='단어를 소리내어 읽어주세요')
            self.instruction_label.config(text='스페이스바를 눌러 시작하세요')
            random.seed(44)  # 4단계는 다른 시드 사용
            random.shuffle(self.words)
            self.current_word_index = 0

    def start_stage(self, stage_number):
        self.show_stage_instruction(stage_number)

    def show_experiment_completion(self):
        """실험 종료 화면을 표시하고 키 바인딩을 비활성화합니다."""
        # 키 바인딩 제거
        self.window.unbind('<space>')
        self.window.unbind('<Return>')
        
        # 기존 위젯들 제거
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # 새로운 프레임 생성 (중앙 정렬)
        completion_frame = tk.Frame(self.window)
        completion_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # 새로운 레이블과 버튼 생성
        completion_label = tk.Label(
            completion_frame,
            text='실험이 모두 종료되었습니다.\n참여해 주셔서 감사합니다.',
            font=('Arial', 64),
            justify=tk.CENTER
        )
        completion_label.pack(pady=50)
        
        exit_button = tk.Button(
            completion_frame,
            text="종료",
            command=self.window.quit,
            font=('Arial', 36)
        )
        exit_button.pack(pady=40)

    def show_next_word(self):
        if self.current_word_index < len(self.words):
            word = self.words[self.current_word_index]
            self.main_label.config(text=word)
            self.instruction_label.config(text='스페이스바를 눌러 다음 단어로 넘어가세요')
            self.current_word_index += 1
            self.start_time = time.time()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            
            if self.current_stage in [1, 4]:
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
            if next_stage <= 4:
                self.start_stage(next_stage)
            else:
                self.show_experiment_completion()

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
                    message = "사람이 발음했습니다."
                else:
                    message = "AI가 발음했습니다."
            else:  # 2단계
                message = "발음을 듣고 따라하세요"
                
            # 첫 번째 메시지 표시
            self.main_label.config(text=message)
            self.instruction_label.config(text='')
            self.window.update()
            
            # 1초 대기
            time.sleep(1)
            
            # 오디오 재생
            duration = self.player.play_audio(audio_file)
            
            # 오디오 재생이 끝날 때까지 대기
            while self.player.is_playing():
                time.sleep(0.1)
            
            # 오디오 재생이 끝나면 두 번째 메시지 표시
            self.instruction_label.config(text='스페이스바를 눌러 다음으로 넘어가세요')
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
            
            self.main_label.config(text='')
            self.instruction_label.config(text='')
            self.window.update()
            
            next_stage = self.current_stage + 1
            if next_stage <= 4:
                self.start_stage(next_stage)
            else:
                self.show_experiment_completion()

    def on_closing(self):
        sd.stop()  # 재생 중인 오디오 정지
        self.window.quit()

    def load_words(self):
        try:
            df = pd.read_excel(self.word_path)
            return df['단어'].tolist()
        except Exception as e:
            messagebox.showerror("오류", f"단어 목록을 불러오는데 실패했습니다: {str(e)}")
            return []

    def load_audio_files(self):
        """오디오 파일 목록을 로드합니다."""
        self.remaining_files = []
        audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio-sample')
        
        if os.path.exists(audio_dir):
            # 원본 오디오 파일 목록 가져오기
            audio_files = [os.path.join(audio_dir, f) for f in os.listdir(audio_dir) 
                         if f.endswith('.wav') and not f.startswith('._')]
            
            # 3개의 리스트 생성
            list1 = audio_files.copy()
            list2 = audio_files.copy()
            list3 = audio_files.copy()
            
            # 각 리스트마다 다른 랜덤 시드 설정
            current_time = datetime.now()
            seed1 = int(current_time.timestamp() * 1000)  # 밀리초 단위
            seed2 = int(current_time.timestamp() * 1000) + 1000  # 1초 후
            seed3 = int(current_time.timestamp() * 1000) + 2000  # 2초 후
            
            # 각 리스트를 개별적으로 셔플
            random.seed(seed1)
            random.shuffle(list1)
            random.seed(seed2)
            random.shuffle(list2)
            random.seed(seed3)
            random.shuffle(list3)
            
            # 3개의 리스트를 순서대로 합치기
            self.remaining_files = list1 + list2 + list3
            
            print(f"발견된 오디오 파일 수: {len(audio_files)}")  # 원본 파일 수
            print(f"복제 후 총 파일 수: {len(self.remaining_files)}")  # 복제 후 파일 수
            print(f"사용된 랜덤 시드: {seed1}, {seed2}, {seed3}")  # 디버깅용
        else:
            print(f"디렉토리를 찾을 수 없음: {audio_dir}")  # 디버깅용
            messagebox.showerror("오류", "오디오 파일을 찾을 수 없습니다.")

    def show(self):
        """메인 윈도우를 표시하고 이벤트 루프를 시작합니다."""
        self.window.mainloop()

def check_existing_data(participant_id):
    """기존 데이터가 있는지 확인합니다."""
    folder_path = f'participant_{participant_id}'
    if os.path.exists(folder_path):
        return messagebox.askyesno('확인', '기존 데이터가 있습니다. 덮어쓰시겠습니까?')
    return True

def create_participant_folder(participant_id, base_dir):
    """참가자 데이터 폴더를 생성합니다."""
    folder_path = os.path.join(base_dir, f'participant_{participant_id}')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

class PathSettingWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('실험 파일 저장 경로 설정')
        self.window.geometry('600x300')
        
        # 안내 메시지
        tk.Label(
            self.window,
            text='실험 파일이 저장될 경로를 설정해주세요.',
            font=('Arial', 12),
            wraplength=550
        ).pack(pady=20)
        
        # 경로 표시 프레임
        path_frame = tk.Frame(self.window)
        path_frame.pack(fill='x', padx=20, pady=10)
        
        self.path_var = tk.StringVar(value=os.path.abspath(os.path.join(os.getcwd(), 'experiment_data')))
        self.path_entry = tk.Entry(
            path_frame,
            textvariable=self.path_var,
            width=50,
            font=('Arial', 11)
        )
        self.path_entry.pack(side=tk.LEFT, padx=5)
        
        # 경로 선택 버튼
        tk.Button(
            path_frame,
            text="경로 선택",
            command=self.select_path,
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=5)
        
        # 경로 생성 상태 표시
        self.status_label = tk.Label(
            self.window,
            text='',
            font=('Arial', 11),
            fg='gray'
        )
        self.status_label.pack(pady=10)
        
        # 버튼 프레임
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        
        # 확인 버튼
        tk.Button(
            button_frame,
            text="확인",
            command=self.confirm,
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=10)
        
        # 취소 버튼
        tk.Button(
            button_frame,
            text="취소",
            command=self.cancel,
            font=('Arial', 11)
        ).pack(side=tk.LEFT)
        
        self.selected_path = None
        
    def select_path(self):
        path = tk.filedialog.askdirectory(
            initialdir=self.path_var.get(),
            title='실험 파일 저장 경로 선택'
        )
        if path:
            self.path_var.set(path)
            self.check_path()
    
    def check_path(self):
        path = self.path_var.get()
        if not path:
            self.status_label.config(
                text='경로를 입력해주세요.',
                fg='red'
            )
            return
            
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                self.status_label.config(
                    text=f'새 경로가 생성되었습니다: {path}',
                    fg='blue'
                )
            except Exception as e:
                self.status_label.config(
                    text=f'경로 생성 실패: {str(e)}',
                    fg='red'
                )
        else:
            # 경로가 존재하는 경우, 쓰기 권한 확인
            try:
                test_file = os.path.join(path, '.test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                self.status_label.config(
                    text='경로가 유효합니다. 이 경로를 사용할 수 있습니다.',
                    fg='green'
                )
            except Exception as e:
                self.status_label.config(
                    text=f'경로에 대한 쓰기 권한이 없습니다: {str(e)}',
                    fg='red'
                )
    
    def confirm(self):
        path = self.path_var.get()
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except Exception as e:
                messagebox.showerror("오류", f"경로를 생성할 수 없습니다:\n{str(e)}")
                return
        
        self.selected_path = path
        self.window.quit()
    
    def cancel(self):
        self.window.quit()
    
    def show(self):
        self.window.mainloop()
        self.window.destroy()
        return self.selected_path

class ListSelectionWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('리스트 선택')
        self.window.geometry('400x250')
        
        # 안내 메시지
        tk.Label(
            self.window,
            text='실험에 사용할 리스트를 선택해주세요.',
            font=('Arial', 12),
            wraplength=350
        ).pack(pady=20)
        
        # 리스트 선택
        tk.Label(
            self.window,
            text='리스트:',
            font=('Arial', 11)
        ).pack(pady=5)
        
        self.list_combo = ttk.Combobox(
            self.window,
            width=40
        )
        self.list_combo['values'] = ['list1', 'list2']  # 리스트 1, 2만 표시
        self.list_combo.current(0)
        self.list_combo.pack(pady=5)
        
        # 현재 선택된 리스트 표시
        self.selection_label = tk.Label(
            self.window,
            text='',
            font=('Arial', 11),
            wraplength=350
        )
        self.selection_label.pack(pady=10)
        
        # 확인 버튼
        self.confirm_button = tk.Button(
            self.window,
            text="선택",
            command=self.confirm,
            font=('Arial', 11)
        )
        self.confirm_button.pack(pady=20)
        
        self.selected_lists = None
        
    def confirm(self):
        selected = self.list_combo.get()
        self.selected_lists = selected
        
        # 선택된 리스트 정보를 참가자의 info 파일에 저장
        config_manager = ConfigManager()
        folder_path = config_manager.config['paths']['participant_data_dir']
        
        # 참가자 ID 가져오기
        participant_id = None
        for file in os.listdir(folder_path):
            if file.startswith('participant_') and file.endswith('_info.xlsx'):
                participant_id = file.split('_')[1]
                break
        
        if participant_id:
            info_file = os.path.join(folder_path, f'participant_{participant_id}_info.xlsx')
            if os.path.exists(info_file):
                # 기존 파일 읽기
                df = pd.read_excel(info_file)
                # 실험 리스트 열만 추가
                df['실험 리스트'] = selected
                # 파일 다시 저장
                df.to_excel(info_file, index=False)
         
        self.window.quit()
    
    def show(self):
        self.window.mainloop()
        self.window.destroy()
        return self.selected_lists

def main():
    # 경로 설정 창 표시
    path_window = PathSettingWindow()
    save_path = path_window.show()
    
    if not save_path:  # 취소를 누른 경우
        return
    
    # 설정 관리자 초기화
    config_manager = ConfigManager()
    
    # 설정된 경로를 config에 저장
    config_manager.config['paths']['participant_data_dir'] = save_path
    config_manager.save_config(config_manager.config)
    
    # 경로 유효성 검사
    invalid_paths = config_manager.verify_paths()
    
    # 유효하지 않은 경로가 있으면 설정 창 표시
    if invalid_paths:
        message = "다음 경로들이 올바르지 않습니다:\n\n"
        for _, path_name in invalid_paths:
            message += f"- {path_name}\n"
        message += "\n설정을 수정하시겠습니까?"
        
        if messagebox.askyesno("경로 오류", message):
            config_window = ConfigWindow(config_manager)
            config_window.show()
        else:
            return
    
    # 참가자 정보 입력
    info_window = ParticipantInfoWindow()
    participant_info = info_window.show()
    
    if not participant_info:
        return
        
    participant_id = participant_info['participant_id']
    
    # 기존 데이터 확인
    if not check_existing_data(participant_id):
        return
    
    # 리스트 선택
    list_window = ListSelectionWindow()
    selected_lists = list_window.show()
    
    if not selected_lists:
        return
    
    # 녹음 장치 선택
    device_window = AudioDeviceWindow()
    selected_device = device_window.show()
    
    if selected_device is None:
        return
        
    # 폴더 생성
    folder_path = create_participant_folder(participant_id, config_manager.config['paths']['participant_data_dir'])
    
    # 메인 실험 창 실행
    main_window = MainExperimentWindow(config_manager.config)
    main_window.start_experiment(
        participant_id=participant_id,
        folder_path=folder_path,
        selected_device=selected_device,
        selected_lists=selected_lists,
        participant_info=participant_info
    )
    main_window.show()

if __name__ == '__main__':
    main() 