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
import sys
import shutil

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
        
        # 화면 중앙에 위치하도록 설정
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        self.window.geometry(f'400x250+{x}+{y}')
        
        # 안내 메시지
        tk.Label(
            self.window,
            text='녹음에 사용할 오디오 입력 장치를 선택해주세요.',
            font=('Arial', 12),
            wraplength=500
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
                messagebox.showinfo("마이크 테스트", "3초간 테스트 녹음을 시작합니다.\n\n"
                                                "1. '확인' 버튼을 누르면 녹음이 시작됩니다.\n"
                                                "2. 마이크에 대고 '테스트'라고 말씀해주세요.\n"
                                                "3. 녹음이 끝나면 자동으로 재생됩니다.")
                
                # 3초 녹음
                recording = sd.rec(
                    int(3 * AudioConstants.SAMPLE_RATE),
                    samplerate=AudioConstants.SAMPLE_RATE,
                    channels=AudioConstants.CHANNELS,
                    device=device_index
                )
                sd.wait()
                
                # 녹음된 데이터가 2차원 배열인 경우 1차원으로 변환
                if len(recording.shape) > 1:
                    recording = recording.flatten()
                
                # 볼륨 레벨 확인
                volume_level = np.abs(recording).mean()
                if volume_level < 0.01:  # 볼륨이 매우 낮은 경우
                    messagebox.showwarning("마이크 볼륨 경고", 
                                         "마이크 입력이 매우 낮습니다.\n"
                                         "1. 마이크가 올바르게 연결되어 있는지 확인해주세요.\n"
                                         "2. 시스템 설정에서 마이크 입력 레벨을 확인해주세요.\n"
                                         "3. 다른 마이크를 선택하거나 다시 테스트해보세요.")
                    return
                
                # 임시 파일로 저장
                temp_file = "temp_test_recording.wav"
                sf.write(temp_file, recording, AudioConstants.SAMPLE_RATE)
                
                # 녹음 재생
                messagebox.showinfo("마이크 테스트", "녹음된 소리를 재생합니다.\n\n"
                                                "1. 소리가 잘 들리는지 확인해주세요.\n"
                                                "2. 소리가 너무 작거나 들리지 않는다면 '취소'를 눌러 다른 마이크를 선택해주세요.")
                data, samplerate = sf.read(temp_file)
                sd.play(data, samplerate)
                sd.wait()
                
                # 임시 파일 삭제
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
        except Exception as e:
            messagebox.showerror("오류", f"마이크 테스트 중 오류가 발생했습니다:\n\n{str(e)}\n\n"
                                     "1. 마이크가 올바르게 연결되어 있는지 확인해주세요.\n"
                                     "2. 다른 마이크를 선택해보세요.\n"
                                     "3. 시스템 설정에서 마이크 권한을 확인해주세요.")
    
    def confirm(self):
        selected_index = self.device_combo.current()
        if selected_index >= 0:
            self.selected_device = self.device_indices[selected_index]
            self.window.quit()
        else:
            messagebox.showerror("오류", "녹음 장치를 선택해주세요.")
    
    def cancel(self):
        if messagebox.askyesno("종료 확인", "실험을 종료하시겠습니까?"):
            self.selected_device = None
            self.window.quit()
            sys.exit()  # 프로그램 완전 종료
    
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
                    message = "사람"
                    self.show_speaker_image(is_ai=False)
                else:
                    message = "AI"
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

class ParticipantInfoWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('참가자 정보')
        self.window.geometry('300x200')
        
        # 화면 중앙에 위치하도록 설정
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 200) // 2
        self.window.geometry(f'300x200+{x}+{y}')
        
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
        if messagebox.askyesno("종료 확인", "실험을 종료하시겠습니까?"):
            self.result = None
            self.window.quit()
            sys.exit()  # 프로그램 완전 종료
        
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
        if self.remaining_words:
            self.current_word = self.remaining_words.pop()
            self.word_label.config(text=self.current_word)
            self.instruction_label.config(text='단어를 읽고, 스페이스바를 눌러 다음 단어로 넘어가세요')
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
               "이제부터 화면에 단어들이 하나씩 제시됩니다.\n\n" +
               "각 단어를 소리내어 읽어주세요.\n\n" +
               "단어를 다 읽으신 후에는 스페이스바를 눌러주세요.\n\n" +
               "모든 단어를 읽으면 다음 단계의 안내가 제시됩니다.",
            2: "2단계: 음성 듣고 따라하기\n\n" +
               "이제부터 녹음된 음성이 하나씩 재생됩니다.\n\n" +
               "각 음성을 잘 들어주세요.\n\n" +
               "각 음원의 재생이 끝나면 나오는 지시문의 안내에 따라\n\n" +
               "소리내어 따라해주신 후, 스페이스바를 눌러주세요.\n\n" +
               "반드시, 음원의 재생이 종료된 이후에 따라 말해주세요.\n\n" +
               "모든 음성을 들으면 다음 단계의 안내가 제시됩니다.",
            4: "4단계: 단어 읽기\n\n" +
               "마지막으로 단어들을 한 번 더 읽어주시면 됩니다.\n\n" +
               "각 단어를 소리내어 읽어주세요.\n\n" +
               "단어를 다 읽으신 후에는 스페이스바를 눌러주세요.\n\n"
        }

        if selected_lists == "list1":
            instructions[3] = ("3단계: AI가 생성한 음성 듣고 따라하기\n\n" +
            "방금 들었던 음성은 AI로 만들어진 아바타가 생성한 것입니다. \n\n" +
            "이 음성을 한 번 더 듣고 따라해주세요.\n\n" +
            "이번에는 음성을 생성한 AI 아바타의 이미지도 함께 제시됩니다.\n\n" +
            "각 음원의 재생이 끝나면 나오는 지시문의 안내에 따라\n\n" +
            "소리내어 따라해주신 후, 스페이스바를 눌러주세요.\n\n" +
            "반드시, 음원의 재생이 종료된 이후에 따라 말해주세요.\n\n" +
            "모든 음성을 들으면 다음 단계의 안내가 제시됩니다.")
        else:
            instructions[3] = ("3단계: 표준 성인 발음 듣고 따라하기\n\n" 
            + "방금 들었던 음성은 20대 성인 남성이 녹음한 발음입니다. \n\n" 
            + "이 음성을 한 번 더 듣고 따라해주세요.\n\n" 
            + "이번에는 음성을 녹음한 사람의 이미지도 함께 제시됩니다.\n\n" 
            + "각 음원의 재생이 끝나면 나오는 지시문의 안내에 따라\n\n" 
            + "소리내어 따라해주신 후, 스페이스바를 눌러주세요.\n\n" 
            + "반드시, 음원의 재생이 종료된 이후에 따라 말해주세요.\n\n" 
            + "모든 음성을 들으면 다음 단계의 안내가 제시됩니다.")
        
        return instructions.get(stage_number, "")

class DataManager:
    @staticmethod
    def save_stage_data(timing_data, participant_id, folder_path, current_stage, selected_device, selected_lists):
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
        
        # config에서 저장 경로 가져오기
        config_manager = ConfigManager()
        save_dir = config_manager.config['paths']['participant_data_dir']
        
        # 참가자 폴더 경로 생성
        participant_folder = os.path.join(save_dir, f'participant_{participant_id}')
        if not os.path.exists(participant_folder):
            os.makedirs(participant_folder)
            
        # Excel 파일 경로
        excel_path = os.path.join(participant_folder, f"{participant_id}_experiment_data.xlsx")
        
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
        # config에서 저장 경로 가져오기
        config_manager = ConfigManager()
        save_dir = config_manager.config['paths']['participant_data_dir']
        
        # 참가자 폴더 경로 생성
        participant_folder = os.path.join(save_dir, f'participant_{participant_id}')
        if not os.path.exists(participant_folder):
            os.makedirs(participant_folder)
            
        info_df = pd.DataFrame({
            '참가자번호': [participant_id],
            '성별': participant_info['gender'],
            '나이': participant_info['age'],
            '실험일시': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            '녹음장치': [sd.query_devices(selected_device)['name']],
            '실험 리스트': [selected_lists]
        })
        
        excel_path = os.path.join(participant_folder, f"{participant_id}_experiment_data.xlsx")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            info_df.to_excel(writer, sheet_name='Info', index=False)

class MainExperimentWindow:
    def __init__(self, config):
        self.window = tk.Tk()
        self.window.title('단어 제시 실험')
        self.window.attributes('-fullscreen', True)
        
        # 화면 크기 가져오기
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 기본 폰트 크기 계산 (화면 크기에 비례)
        self.base_font_size = int(min(screen_height / 30, screen_width / 50))  # 더 작은 값으로 조정
        self.large_font_size = int(self.base_font_size * 1.8)  # 비율 조정
        self.small_font_size = int(self.base_font_size * 0.8)
        
        # 창 크기 설정 (화면 크기의 70%로 조정하고 여백 추가)
        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.7)
        
        # 창을 화면 중앙에 위치
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # wraplength 계산 (창 너비의 90%로 조정)
        self.wrap_length = int(window_width * 0.9)
        
        # config에서 경로 설정
        self.config = config
        self.word_path = config['paths']['word_file']
        
        # 이미지 경로 설정
        self.image_dir = config['paths']['images_dir']
        self.ai_image_path = os.path.join(self.image_dir, 'ai.png')
        self.human_image_path = os.path.join(self.image_dir, 'human.png')
        
        # 이미지 로드
        self.ai_image = None
        self.human_image = None
        self.current_image = None
        self.load_images()
        
        # 중앙 정렬을 위한 프레임 생성
        self.center_frame = tk.Frame(self.window)
        self.center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # 이미지 표시 레이블 (가장 위에 배치)
        self.image_label = tk.Label(self.center_frame)
        self.image_label.pack(pady=(0, 50))  # 아래쪽 여백 증가
        
        # 메인 텍스트 레이블
        self.main_label = tk.Label(self.center_frame, text='', font=('Arial', self.large_font_size))
        self.main_label.pack(pady=30)  # 여백 증가
        
        # 안내 텍스트 레이블
        self.instruction_label = tk.Label(self.center_frame, text='', font=('Arial', self.small_font_size))
        self.instruction_label.pack(pady=30)  # 여백 증가
        
        self.current_stage = 0
        self.timing_data = []
        
        # 스페이스바 입력 상태 추적을 위한 변수 추가
        self.space_pressed = False
        
        # 이벤트 핸들러 바인딩
        self.window.bind('<space>', self.handle_space_press)
        self.window.bind('<Return>', self.handle_return_press)
        
        # 창 크기 변경 시 폰트 크기 조절
        self.window.bind('<Configure>', self.on_window_resize)
        
        # 하위 창들을 위한 변수
        self.current_dialog = None

    def on_window_resize(self, event):
        """창 크기가 변경될 때 폰트 크기와 wraplength 조절"""
        if event.widget == self.window:
            # 새로운 기본 폰트 크기 계산
            new_base_size = int(min(event.height / 30, event.width / 50))  # 더 작은 값으로 조정
            new_large_size = int(new_base_size * 1.8)  # 비율 조정
            new_wrap_length = int(event.width * 0.9)  # wraplength를 창 너비의 90%로 설정
            
            # 모든 레이블 업데이트
            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Label):
                    current_font = widget['font']
                    if isinstance(current_font, tuple):
                        font_family = current_font[0]
                        # 큰 폰트인지 작은 폰트인지 확인
                        if float(current_font[1]) > self.base_font_size:
                            new_size = new_large_size
                        else:
                            new_size = new_base_size
                        widget.configure(font=(font_family, new_size))
                        widget.configure(wraplength=new_wrap_length)
            
            # 현재 값 업데이트
            self.base_font_size = new_base_size
            self.large_font_size = new_large_size
            self.wrap_length = new_wrap_length

    def load_images(self):
        """이미지 파일들을 로드합니다."""
        try:
            if os.path.exists(self.ai_image_path):
                self.ai_image = tk.PhotoImage(file=self.ai_image_path)
                # 이미지 크기 조정 (예: 200x200)
                self.ai_image = self.ai_image.subsample(2, 2)
            else:
                print(f"AI 이미지를 찾을 수 없음: {self.ai_image_path}")
                
            if os.path.exists(self.human_image_path):
                self.human_image = tk.PhotoImage(file=self.human_image_path)
                # 이미지 크기 조정 (예: 200x200)
                self.human_image = self.human_image.subsample(2, 2)
            else:
                print(f"사람 이미지를 찾을 수 없음: {self.human_image_path}")
        except Exception as e:
            print(f"이미지 로드 중 오류 발생: {str(e)}")

    def show_speaker_image(self, is_ai):
        """발음자 이미지를 표시합니다."""
        if self.current_stage == 3:  # 3단계에서만 이미지 표시
            if is_ai and self.ai_image:
                self.current_image = self.ai_image
                self.image_label.config(image=self.current_image)
                self.image_label.pack(pady=20)
            elif not is_ai and self.human_image:
                self.current_image = self.human_image
                self.image_label.config(image=self.current_image)
                self.image_label.pack(pady=20)
            else:
                self.current_image = None
                self.image_label.pack_forget()
        else:
            self.current_image = None
            self.image_label.pack_forget()

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
각 단계별 안내는 단계별 시작 전 제공될 예정이며,
청각, 시각적 자극을 바탕으로 따라 말하는 과제입니다.

3. 주의사항
- 모든 단계에서 마이크를 통해 음성이 녹음됩니다.
- 각 단계 시작 전에 마이크가 정상적으로 작동하는지 확인해주세요.
- 실험 중에는 조용한 환경에서 진행해주세요.
- 실험 중간에 중단이 필요한 경우 언제든 말씀해 주세요.

4. 실험 시간
- 전체 실험은 약 15-20분 정도 소요됩니다.
- 각 단계는 약 3-5분 정도 소요됩니다.

위 내용을 모두 읽고 이해하셨다면, '시작하기' 버튼을 눌러 실험을 시작해주세요.
"""
        
        instruction_text = tk.Label(
            instruction_frame,
            text=intro_text,
            font=('Arial', 24),
            justify=tk.CENTER,
            wraplength=self.wrap_length
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
            self.current_stage,
            self.selected_device,
            self.selected_lists
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
            wraplength=self.wrap_length
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
            # 음성 재생 중에만 스페이스바 입력 무시
            if hasattr(self, 'player') and self.player.is_playing():
                return
                
            # 음성이 재생 중이 아닐 때만 처리
            if hasattr(self, 'player') and not self.player.is_playing():
                # 이미 스페이스바가 눌린 상태라면 무시
                if self.space_pressed:
                    return
                    
                self.space_pressed = True
                if self.timing_data:
                    self.timing_data[-1]['스페이스바_시간'] = current_time
                self.play_next_audio()
                
                # 0.5초 후에 스페이스바 상태 초기화
                self.window.after(500, self.reset_space_pressed)

    def reset_space_pressed(self):
        """스페이스바 입력 상태를 초기화합니다."""
        self.space_pressed = False

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
            self.instruction_label.config(text='단어를 소리내어 읽어주신 후 스페이스바를 눌러 다음 단어로 넘어가세요.')
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
                    message = "20대 한국인 남성"
                    self.show_speaker_image(is_ai=False)
                else:
                    message = "AI 아바타 GT-25"
                    self.show_speaker_image(is_ai=True)
            else:  # 2단계
                message = "발음을 잘 들어주세요."
                self.show_speaker_image(is_ai=None)
                
            # 첫 번째 메시지 표시
            self.main_label.config(text=message)
            self.instruction_label.config(text='')
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
            
            self.main_label.config(text='')
            self.instruction_label.config(text='')
            self.image_label.pack_forget()  # 이미지 숨기기
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
        audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config['paths']['audio_sample_dir'])
        
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

def check_existing_data(participant_id, base_dir, selected_device=None, selected_lists=None, participant_info=None):
    """기존 데이터가 있는지 확인하고, 있는 경우 새로운 파일 이름을 생성합니다."""
    # config에서 저장 경로 가져오기
    config_manager = ConfigManager()
    save_dir = config_manager.config['paths']['participant_data_dir']
    
    # base_dir이 config의 경로와 다른 경우, config의 경로도 확인
    if base_dir != save_dir:
        config_folder_path = os.path.join(save_dir, f'participant_{participant_id}')
        if os.path.exists(config_folder_path):
            excel_path = os.path.join(config_folder_path, f"{participant_id}_experiment_data.xlsx")
            if os.path.exists(excel_path):
                try:
                    # 기존 데이터 읽기
                    with pd.ExcelFile(excel_path) as xls:
                        # 완료된 단계 확인
                        completed_stages = []
                        for sheet_name in xls.sheet_names:
                            if sheet_name.startswith('Stage'):
                                completed_stages.append(int(sheet_name[5:]))
                        
                        if completed_stages:
                            message = f"참가자 {participant_id}의 기존 데이터가 있습니다.\n"
                            message += f"완료된 단계: {', '.join(map(str, sorted(completed_stages)))}\n\n"
                            message += "기존 데이터를 덮어쓰시겠습니까?"
                        else:
                            message = f"참가자 {participant_id}의 기존 데이터가 있습니다.\n"
                            message += "아직 완료된 단계가 없습니다.\n\n"
                            message += "기존 데이터를 덮어쓰시겠습니까?"
                            
                        if messagebox.askyesno('확인', message):
                            # 현재 날짜와 시간 정보를 포함한 새로운 파일 이름 생성
                            current_time = datetime.now()
                            time_str = current_time.strftime('%Y%m%d_%H%M')
                            new_folder_path = os.path.join(save_dir, f'participant_{participant_id}_{time_str}')
                            
                            # 새 폴더 생성
                            if not os.path.exists(new_folder_path):
                                os.makedirs(new_folder_path)
                            
                            # 새로운 Excel 파일 생성
                            new_excel_path = os.path.join(new_folder_path, f"{participant_id}_experiment_data.xlsx")
                            with pd.ExcelWriter(new_excel_path, engine='openpyxl') as writer:
                                # Info 시트 생성
                                info_df = pd.DataFrame({
                                    '참가자번호': [participant_id],
                                    '성별': [participant_info['gender'] if participant_info else ''],
                                    '나이': [participant_info['age'] if participant_info else ''],
                                    '실험일시': [current_time.strftime('%Y-%m-%d %H:%M:%S')],
                                    '녹음장치': [sd.query_devices(selected_device)['name'] if selected_device else ''],
                                    '실험 리스트': [selected_lists if selected_lists else '']
                                })
                                info_df.to_excel(writer, sheet_name='Info', index=False)
                            
                            return new_folder_path
                        else:
                            # 덮어쓰기를 거절한 경우
                            messagebox.showinfo("알림", "다른 참가자 번호를 입력해주세요.")
                            return None
                except Exception as e:
                    messagebox.showerror("오류", f"기존 데이터 확인 중 오류가 발생했습니다:\n{str(e)}")
                    return None
    
    # base_dir 경로 확인
    folder_path = os.path.join(base_dir, f'participant_{participant_id}')
    if os.path.exists(folder_path):
        # 실험 데이터 파일 확인
        excel_path = os.path.join(folder_path, f"{participant_id}_experiment_data.xlsx")
        if os.path.exists(excel_path):
            try:
                # 기존 데이터 읽기
                with pd.ExcelFile(excel_path) as xls:
                    # 완료된 단계 확인
                    completed_stages = []
                    for sheet_name in xls.sheet_names:
                        if sheet_name.startswith('Stage'):
                            completed_stages.append(int(sheet_name[5:]))
                    
                    if completed_stages:
                        message = f"참가자 {participant_id}의 기존 데이터가 있습니다.\n"
                        message += f"완료된 단계: {', '.join(map(str, sorted(completed_stages)))}\n\n"
                        message += "기존 데이터를 덮어쓰시겠습니까?"
                    else:
                        message = f"참가자 {participant_id}의 기존 데이터가 있습니다.\n"
                        message += "아직 완료된 단계가 없습니다.\n\n"
                        message += "기존 데이터를 덮어쓰시겠습니까?"
                        
                    if messagebox.askyesno('확인', message):
                        # 현재 날짜와 시간 정보를 포함한 새로운 파일 이름 생성
                        current_time = datetime.now()
                        time_str = current_time.strftime('%Y%m%d_%H%M')
                        new_folder_path = os.path.join(base_dir, f'participant_{participant_id}_{time_str}')
                        
                        # 새 폴더 생성
                        if not os.path.exists(new_folder_path):
                            os.makedirs(new_folder_path)
                        
                        # 새로운 Excel 파일 생성
                        new_excel_path = os.path.join(new_folder_path, f"{participant_id}_experiment_data.xlsx")
                        with pd.ExcelWriter(new_excel_path, engine='openpyxl') as writer:
                            # Info 시트 생성
                            info_df = pd.DataFrame({
                                '참가자번호': [participant_id],
                                '성별': [participant_info['gender'] if participant_info else ''],
                                '나이': [participant_info['age'] if participant_info else ''],
                                '실험일시': [current_time.strftime('%Y-%m-%d %H:%M:%S')],
                                '녹음장치': [sd.query_devices(selected_device)['name'] if selected_device else ''],
                                '실험 리스트': [selected_lists if selected_lists else '']
                            })
                            info_df.to_excel(writer, sheet_name='Info', index=False)
                        
                        return new_folder_path
                    else:
                        # 덮어쓰기를 거절한 경우
                        messagebox.showinfo("알림", "다른 참가자 번호를 입력해주세요.")
                        return None
            except Exception as e:
                messagebox.showerror("오류", f"기존 데이터 확인 중 오류가 발생했습니다:\n{str(e)}")
                return None
    return folder_path

def create_participant_folder(participant_id, base_dir, selected_device=None, selected_lists=None, participant_info=None):
    """참가자 데이터 폴더를 생성합니다."""
    folder_path = check_existing_data(participant_id, base_dir, selected_device, selected_lists, participant_info)
    if folder_path:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return folder_path
    return None

class PathSettingWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('실험 파일 저장 경로 설정')
        self.window.geometry('600x400')  # 높이 증가
        
        # 화면 중앙에 위치하도록 설정
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 400) // 2
        self.window.geometry(f'600x400+{x}+{y}')
        
        # config 파일에서 경로 확인
        config_manager = ConfigManager()
        config_data_path = config_manager.config['paths'].get('participant_data_dir', '')
        config_image_path = config_manager.config['paths'].get('images_dir', '')
        
        # 실험 데이터 경로 유효성 검사
        if config_data_path and os.path.exists(config_data_path):
            self.data_path_var = tk.StringVar(value=config_data_path)
        else:
            self.data_path_var = tk.StringVar(value=os.path.abspath(os.path.join(os.getcwd(), 'experiment_data')))
        
        # 이미지 경로 유효성 검사
        if config_image_path and os.path.exists(config_image_path):
            # 필수 이미지 파일 확인
            ai_image_path = os.path.join(config_image_path, 'ai.png')
            human_image_path = os.path.join(config_image_path, 'human.png')
            
            if os.path.exists(ai_image_path) and os.path.exists(human_image_path):
                # 이미지 파일이 모두 존재하는 경우
                self.image_path_var = tk.StringVar(value=config_image_path)
            else:
                # 이미지 파일이 없는 경우
                missing_files = []
                if not os.path.exists(ai_image_path):
                    missing_files.append('ai.png')
                if not os.path.exists(human_image_path):
                    missing_files.append('human.png')
                messagebox.showwarning("이미지 파일 누락", 
                                     f"설정된 이미지 경로에 다음 파일이 없습니다:\n{', '.join(missing_files)}\n\n"
                                     "올바른 이미지 경로를 선택해주세요.")
                self.image_path_var = tk.StringVar(value=os.path.abspath(os.path.join(os.getcwd(), 'images')))
        else:
            # config에 이미지 경로가 없거나 경로가 존재하지 않는 경우
            self.image_path_var = tk.StringVar(value=os.path.abspath(os.path.join(os.getcwd(), 'images')))
        
        # 안내 메시지
        tk.Label(
            self.window,
            text='실험 파일이 저장될 경로와 이미지 디렉토리 경로를 설정해주세요.',
            font=('Arial', 12),
            wraplength=800
        ).pack(pady=20)
        
        # 실험 데이터 경로 설정
        tk.Label(
            self.window,
            text='실험 데이터 저장 경로:',
            font=('Arial', 11)
        ).pack(pady=(10, 5))
        
        # 실험 데이터 경로 표시 프레임
        data_path_frame = tk.Frame(self.window)
        data_path_frame.pack(fill='x', padx=20, pady=5)
        
        self.data_path_entry = tk.Entry(
            data_path_frame,
            textvariable=self.data_path_var,
            width=50,
            font=('Arial', 11)
        )
        self.data_path_entry.pack(side=tk.LEFT, padx=5)
        
        # 실험 데이터 경로 선택 버튼
        tk.Button(
            data_path_frame,
            text="경로 선택",
            command=lambda: self.select_path(self.data_path_var),
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=5)
        
        # 이미지 디렉토리 경로 설정
        tk.Label(
            self.window,
            text='이미지 디렉토리 경로:',
            font=('Arial', 11)
        ).pack(pady=(20, 5))
        
        # 이미지 경로 표시 프레임
        image_path_frame = tk.Frame(self.window)
        image_path_frame.pack(fill='x', padx=20, pady=5)
        
        self.image_path_entry = tk.Entry(
            image_path_frame,
            textvariable=self.image_path_var,
            width=50,
            font=('Arial', 11)
        )
        self.image_path_entry.pack(side=tk.LEFT, padx=5)
        
        # 이미지 경로 선택 버튼
        tk.Button(
            image_path_frame,
            text="경로 선택",
            command=lambda: self.select_path(self.image_path_var),
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
        
        self.selected_paths = None
        
    def select_path(self, path_var):
        path = tk.filedialog.askdirectory(
            initialdir=path_var.get(),
            title='디렉토리 선택'
        )
        if path:
            path_var.set(path)
            self.check_paths()
    
    def check_paths(self):
        data_path = self.data_path_var.get()
        image_path = self.image_path_var.get()
        
        if not data_path or not image_path:
            self.status_label.config(
                text='모든 경로를 입력해주세요.',
                fg='red'
            )
            return
            
        # 실험 데이터 경로 확인
        if not os.path.exists(data_path):
            try:
                os.makedirs(data_path)
            except Exception as e:
                self.status_label.config(
                    text=f'실험 데이터 경로 생성 실패: {str(e)}',
                    fg='red'
                )
                return
                
        # 이미지 경로 확인
        if not os.path.exists(image_path):
            try:
                os.makedirs(image_path)
            except Exception as e:
                self.status_label.config(
                    text=f'이미지 경로 생성 실패: {str(e)}',
                    fg='red'
                )
                return
                
        # 필수 이미지 파일 확인
        ai_image_path = os.path.join(image_path, 'ai.png')
        human_image_path = os.path.join(image_path, 'human.png')
        
        if not os.path.exists(ai_image_path) or not os.path.exists(human_image_path):
            missing_files = []
            if not os.path.exists(ai_image_path):
                missing_files.append('ai.png')
            if not os.path.exists(human_image_path):
                missing_files.append('human.png')
            self.status_label.config(
                text=f'필수 이미지 파일이 없습니다: {", ".join(missing_files)}',
                fg='red'
            )
            return
                
        # 쓰기 권한 확인
        try:
            test_file = os.path.join(data_path, '.test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            test_file = os.path.join(image_path, '.test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            self.status_label.config(
                text='모든 경로와 이미지 파일이 유효합니다.',
                fg='green'
            )
        except Exception as e:
            self.status_label.config(
                text=f'경로에 대한 쓰기 권한이 없습니다: {str(e)}',
                fg='red'
            )
    
    def confirm(self):
        data_path = self.data_path_var.get()
        image_path = self.image_path_var.get()
        
        if not os.path.exists(data_path):
            try:
                os.makedirs(data_path)
            except Exception as e:
                messagebox.showerror("오류", f"실험 데이터 경로를 생성할 수 없습니다:\n{str(e)}")
                return
                
        if not os.path.exists(image_path):
            try:
                os.makedirs(image_path)
            except Exception as e:
                messagebox.showerror("오류", f"이미지 경로를 생성할 수 없습니다:\n{str(e)}")
                return
        
        # config 파일 업데이트
        config_manager = ConfigManager()
        config_manager.config['paths'].update({
            'participant_data_dir': data_path,
            'images_dir': image_path
        })
        config_manager.save_config(config_manager.config)
        
        self.selected_paths = {
            'participant_data_dir': data_path,
            'images_dir': image_path
        }
        self.window.quit()
    
    def cancel(self):
        if messagebox.askyesno("종료 확인", "실험을 종료하시겠습니까?"):
            self.selected_paths = None
            self.window.quit()
            sys.exit()  # 프로그램 완전 종료
    
    def show(self):
        self.window.mainloop()
        self.window.destroy()
        return self.selected_paths

class ListSelectionWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('리스트 선택')
        self.window.geometry('400x250')
        
        # 화면 중앙에 위치하도록 설정
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        self.window.geometry(f'400x250+{x}+{y}')
        
        # 안내 메시지
        tk.Label(
            self.window,
            text='실험에 사용할 리스트를 선택해주세요.',
            font=('Arial', 12),
            wraplength=500
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
        
        # 버튼 프레임
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        
        # 확인 버튼
        tk.Button(
            button_frame,
            text="선택",
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
                if selected == "list1":
                    df['음성 정체성'] = "사람"
                elif selected == "list2":
                    df['음성 정체성'] = "AI"
                # 파일 다시 저장
                df.to_excel(info_file, index=False)
         
        self.window.quit()
        
    def cancel(self):
        if messagebox.askyesno("종료 확인", "실험을 종료하시겠습니까?"):
            self.selected_lists = None
            self.window.quit()
            sys.exit()  # 프로그램 완전 종료
    
    def show(self):
        self.window.mainloop()
        self.window.destroy()
        return self.selected_lists

def main():
    while True:  # 참가자 정보 입력을 반복할 수 있도록 루프 추가
        # 경로 설정 창 표시
        path_window = PathSettingWindow()
        selected_paths = path_window.show()
        
        if not selected_paths:  # 취소를 누른 경우
            return
            
        # 경로 유효성 검사
        for path_name, path in selected_paths.items():
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except Exception as e:
                    messagebox.showerror("오류", f"{path_name} 경로를 생성할 수 없습니다:\n{str(e)}")
                    return
                    
            # 경로에 대한 쓰기 권한 확인
            try:
                test_file = os.path.join(path, '.test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                messagebox.showerror("오류", f"경로에 대한 쓰기 권한이 없습니다:\n{str(e)}")
                return
        
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        # 설정된 경로들을 config에 저장
        config_manager.config['paths'].update(selected_paths)
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
                if messagebox.askyesno("종료 확인", "실험을 종료하시겠습니까?"):
                    sys.exit()
                return
        
        # 참가자 정보 입력
        info_window = ParticipantInfoWindow()
        participant_info = info_window.show()
        
        if not participant_info:
            return
            
        participant_id = participant_info['participant_id']
        
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
        folder_path = create_participant_folder(participant_id, config_manager.config['paths']['participant_data_dir'], selected_device, selected_lists, participant_info)
        
        if not folder_path:
            continue  # 참가자 정보 입력 창으로 돌아가기
        
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
        break  # 실험이 완료되면 루프 종료

if __name__ == '__main__':
    main() 