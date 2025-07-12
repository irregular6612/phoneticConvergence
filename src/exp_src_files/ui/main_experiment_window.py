import tkinter as tk
import os
from datetime import datetime
import time
from audio import AudioPlayer, AudioRecorder
import random
import pandas as pd
from data import DataManager, StageInstruction
from tkinter import messagebox
import sounddevice as sd

class MainExperimentWindow:
    def __init__(self, config):
        self.window = tk.Tk()
        self.window.title('단어 제시 실험')
        self.window.attributes('-fullscreen', True)
        
        # 창을 항상 최상위에 표시
        self.window.lift()
        self.window.attributes('-topmost', True)
        
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
        self.main_word_list_path = config['paths']['main_word_list']  # 본시행 단어 리스트
        self.practice_word_list_path = config['paths']['practice_word_list']  # 예비시행 단어 리스트
        
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
        if self.current_stage == 5:  # 5단계에서만 이미지 표시
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
        
        # 음성 재생 중에는 스페이스바 입력 무시
        if hasattr(self, 'player') and self.player.is_playing():
            return
            
        # 이미 스페이스바가 눌린 상태라면 무시
        if self.space_pressed:
            return
            
        self.space_pressed = True
        
        # 모든 단계에서 스페이스바 시간 기록
        if self.timing_data:
            self.timing_data[-1]['스페이스바_시간'] = current_time
            
        if self.current_stage in [1, 2, 6]:  # 1단계, 1단계 반복, 4단계
            self.show_next_word()
        elif self.current_stage in [3, 4, 5]:  # 2단계, 2단계 반복, 3단계
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
        
        # 녹음기 초기화 확인
        if not hasattr(self, 'recorder') or not self.recorder:
            self.recorder = AudioRecorder(self.selected_device, self.folder_path)
            
        # 모든 단계에서 녹음 시작
        self.recorder.start_recording(f"{self.participant_id}_stage{self.current_stage}")
        
        if self.current_stage in [1, 2]:  # 1단계와 1단계 반복
            self.main_label.config(text='단어를 소리내어 읽어주세요')
            self.instruction_label.config(text='스페이스바를 눌러 시작하세요')
            self.words = self.load_words()
            # 시간 기반 랜덤 시드 설정
            current_time = int(datetime.now().timestamp() * 1000)  # 밀리초 단위
            random.seed(current_time + stage_number)  # 단계별로 다른 시드 사용
            random.shuffle(self.words)
            self.current_word_index = 0
            
        elif self.current_stage in [3, 4, 5]:  # 2단계와 2단계 반복
            self.main_label.config(text='음성을 듣고 따라 읽어주세요')
            self.instruction_label.config(text='스페이스바를 눌러 시작하세요')
            self.load_audio_files()
            
        elif self.current_stage == 6:  # 4단계
            self.main_label.config(text='단어를 소리내어 읽어주세요')
            self.instruction_label.config(text='스페이스바를 눌러 시작하세요')
            # 시간 기반 랜덤 시드 설정
            current_time = int(datetime.now().timestamp() * 1000)  # 밀리초 단위
            random.seed(current_time + stage_number)  # 단계별로 다른 시드 사용
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

    def play_next_audio(self):
        if self.remaining_files:
            audio_file = self.remaining_files.pop()
            self.current_file = os.path.basename(audio_file)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            
            # 현재 재생 중인 오디오 파일의 리스트 정보 확인
            current_list = 'list1' if 'list1' in audio_file else 'list2'
            
            # 리스트에 따라 다른 메시지 표시 (5단계에서만)
            if self.current_stage == 5:  # 5단계
                if current_list == self.selected_lists:
                    message = "20대 한국인 남성"
                    self.show_speaker_image(is_ai=False)
                else:
                    message = "AI 아바타 GT-25"
                    self.show_speaker_image(is_ai=True)
            else:  # 2단계, 2단계 반복, 3단계
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
            
            # 2단계, 2단계 반복, 3단계가 끝날 때 녹음 중지
            if self.current_stage in [3, 4, 5]:
                if hasattr(self, 'recorder') and self.recorder:
                    self.recorder.stop_recording()
            
            if self.player:
                sd.stop()
            
            self.main_label.config(text='')
            self.instruction_label.config(text='')
            self.image_label.pack_forget()  # 이미지 숨기기
            self.window.update()
            
            next_stage = self.current_stage + 1
            if next_stage <= 6:  # 6단계까지 진행
                self.start_stage(next_stage)
            else:
                self.show_experiment_completion()

    def on_closing(self):
        sd.stop()  # 재생 중인 오디오 정지
        self.window.quit()

    def load_words(self):
        try:
            if self.current_stage == 1:
                df = pd.read_excel(self.practice_word_list_path)
                return df['단어'].tolist()
            elif self.current_stage == 2:
                df = pd.read_excel(self.main_word_list_path)
                return df['단어'].tolist()
            else:
                raise ValueError(f"현재 단계 {self.current_stage}에 대한 단어 목록을 불러오는 데 실패했습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"단어 목록을 불러오는데 실패했습니다: {str(e)}")
            return []

    def load_audio_files(self):
        """오디오 파일 목록을 로드합니다."""
        self.remaining_files = []
        
        # 3단계는 practice_audio_dir, 4단계는 audio_sample_dir 사용
        if self.current_stage == 3:
            audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.config['paths']['practice_audio_dir'])
        else:  # 4단계
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
