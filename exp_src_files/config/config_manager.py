import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import sys

class ConfigManager:
    def __init__(self):
        # config.json 파일 경로 설정
        self.config_file = os.path.abspath(os.path.join(os.getcwd(), 'config.json'))
        self.default_config = {
            'paths': {
                'participant_data_dir': os.path.abspath(os.path.join(os.getcwd(), 'experiment_data')),
                'images_dir': os.path.abspath(os.path.join(os.getcwd(), 'images')),
                'audio_sample_dir': os.path.abspath(os.path.join(os.getcwd(), 'audio_samples')),
                'main_word_list': os.path.abspath(os.path.join(os.getcwd(), 'main_words.xlsx')),
                'practice_word_list': os.path.abspath(os.path.join(os.getcwd(), 'practice_words.xlsx')),
                'practice_audio_dir': os.path.abspath(os.path.join(os.getcwd(), 'practice_audio'))
            }
        }
        self.config = self.load_config()
        
    def find_config_file(self):
        """config.json 파일을 찾습니다."""
        # 현재 디렉토리에서 config.json 찾기
        if os.path.exists('config.json'):
            return 'config.json'
            
        # 상위 디렉토리에서 config.json 찾기
        parent_dir = os.path.dirname(os.path.abspath(os.getcwd()))
        parent_config = os.path.join(parent_dir, 'config.json')
        if os.path.exists(parent_config):
            return parent_config
            
        # 사용자의 홈 디렉토리에서 config.json 찾기
        home_dir = os.path.expanduser('~')
        home_config = os.path.join(home_dir, 'config.json')
        if os.path.exists(home_config):
            return home_config
            
        # config.json을 찾을 수 없는 경우 사용자에게 선택권 제공
        response = messagebox.askyesno(
            "설정 파일 찾기",
            "config.json 파일을 찾을 수 없습니다.\n\n"
            "기존 설정 파일을 찾으시겠습니까?\n"
            "아니오를 선택하면 새 파일을 생성합니다."
        )
        
        if response:
            # 기존 파일 찾기
            config_path = filedialog.askopenfilename(
                title='config.json 파일 찾기',
                filetypes=[('JSON files', '*.json')],
                initialdir=os.getcwd()
            )
            if config_path:
                return config_path
            else:
                # 파일 선택을 취소한 경우 새 파일 생성 여부 확인
                if messagebox.askyesno(
                    "설정 파일 생성",
                    "파일을 선택하지 않았습니다.\n"
                    "새로운 config.json 파일을 생성하시겠습니까?"
                ):
                    return self.create_new_config()
                return None
        else:
            # 새 파일 생성
            return self.create_new_config()
            
    def create_new_config(self):
        """새로운 config.json 파일을 생성합니다."""
        config_path = filedialog.asksaveasfilename(
            title='새 config.json 파일 생성',
            defaultextension='.json',
            initialfile='config.json',
            filetypes=[('JSON files', '*.json')],
            initialdir=os.getcwd()
        )
        return config_path if config_path else None
        
    def load_config(self):
        """설정 파일을 로드합니다."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 기존 설정과 기본 설정 병합
                if 'paths' not in config:
                    config['paths'] = {}
                    
                # 기본 경로 설정
                for key, value in self.default_config['paths'].items():
                    if key not in config['paths'] or not config['paths'][key]:
                        config['paths'][key] = value
                        
                return config
            else:
                # 기본 설정으로 새 파일 생성
                config = self.default_config.copy()
                self.save_config(config)
                return config
        except Exception as e:
            print(f"설정 파일 로드 중 오류 발생: {str(e)}")
            return self.default_config.copy()
            
    def save_config(self, config):
        """설정을 파일에 저장합니다."""
        try:
            # 설정 디렉토리 생성
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 설정 저장
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            print("설정이 성공적으로 저장되었습니다.")
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {str(e)}")
            raise
            
    def verify_paths(self):
        """설정된 경로들의 유효성을 검증합니다."""
        paths = self.config.get('paths', {})
        missing_paths = []
        
        # 필수 경로 확인
        required_paths = [
            'participant_data_dir',
            'images_dir',
            'audio_sample_dir',
            'main_word_list',
            'practice_word_list',
            'practice_audio_dir'
        ]
        
        for path_key in required_paths:
            path = paths.get(path_key)
            if not path or not os.path.exists(path):
                missing_paths.append(path_key)
                
        if missing_paths:
            print(f"다음 경로가 설정되지 않았거나 존재하지 않습니다: {', '.join(missing_paths)}")
            return False
            
        # 이미지 파일 확인
        image_dir = paths['images_dir']
        required_images = ['ai.png', 'human.png']
        missing_images = []
        
        for image in required_images:
            if not os.path.exists(os.path.join(image_dir, image)):
                missing_images.append(image)
                
        if missing_images:
            print(f"다음 이미지 파일이 없습니다: {', '.join(missing_images)}")
            return False
            
        # 오디오 파일 확인
        audio_dir = paths['audio_sample_dir']
        audio_files = [f for f in os.listdir(audio_dir) 
                      if f.endswith('.wav') and not f.startswith('._')]
        if not audio_files:
            print("오디오 샘플 디렉토리에 WAV 파일이 없습니다.")
            return False
            
        # 예비 연습 단어 파일 확인
        practice_word_file = paths['practice_word_list']
        try:
            df = pd.read_excel(practice_word_file)
            if '단어' not in df.columns:
                print("예비 연습 단어 파일에 '단어' 열이 없습니다.")
                return False
        except Exception as e:
            print(f"예비 연습 단어 파일을 읽을 수 없습니다: {str(e)}")
            return False
            
        # 예비 연습 오디오 파일 확인
        practice_audio_dir = paths['practice_audio_dir']
        practice_audio_files = [f for f in os.listdir(practice_audio_dir) 
                              if f.endswith('.wav') and not f.startswith('._')]
        if not practice_audio_files:
            print("예비 연습 오디오 디렉토리에 WAV 파일이 없습니다.")
            return False
            
        return True

class ConfigWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('실험 파일 저장 경로 설정')
        self.window.geometry('600x600')
        
        # 화면 중앙에 위치하도록 설정
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 600) // 2
        self.window.geometry(f'600x600+{x}+{y}')
        
        # config 매니저 초기화
        self.config_manager = ConfigManager()
        
        # 안내 메시지
        tk.Label(
            self.window,
            text='실험 파일이 저장될 경로와 이미지, 오디오 디렉토리 경로를 설정해주세요.',
            font=('Arial', 12),
            wraplength=800
        ).pack(pady=20)
        
        # 경로 설정 프레임
        path_frame = ttk.LabelFrame(self.window, text='경로 설정', padding=10)
        path_frame.pack(fill='x', padx=10, pady=5)
        
        # 실험 데이터 경로
        ttk.Label(path_frame, text='실험 데이터 저장 경로:').pack(anchor='w')
        data_path_frame = ttk.Frame(path_frame)
        data_path_frame.pack(fill='x', pady=5)
        self.data_path_var = tk.StringVar(value=self.config_manager.config['paths']['participant_data_dir'])
        ttk.Entry(data_path_frame, textvariable=self.data_path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(data_path_frame, text='찾아보기', command=lambda: self.select_path('participant_data_dir')).pack(side='left', padx=5)
        
        # 이미지 경로
        ttk.Label(path_frame, text='이미지 디렉토리 경로:').pack(anchor='w')
        image_path_frame = ttk.Frame(path_frame)
        image_path_frame.pack(fill='x', pady=5)
        self.image_path_var = tk.StringVar(value=self.config_manager.config['paths']['images_dir'])
        ttk.Entry(image_path_frame, textvariable=self.image_path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(image_path_frame, text='찾아보기', command=lambda: self.select_path('images_dir')).pack(side='left', padx=5)
        
        # 오디오 샘플 경로
        ttk.Label(path_frame, text='오디오 샘플 디렉토리 경로:').pack(anchor='w')
        audio_path_frame = ttk.Frame(path_frame)
        audio_path_frame.pack(fill='x', pady=5)
        self.audio_path_var = tk.StringVar(value=self.config_manager.config['paths']['audio_sample_dir'])
        ttk.Entry(audio_path_frame, textvariable=self.audio_path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(audio_path_frame, text='찾아보기', command=lambda: self.select_path('audio_sample_dir')).pack(side='left', padx=5)
        
        # 예비 연습 단어 파일
        ttk.Label(path_frame, text='예비 연습 단어 파일:').pack(anchor='w')
        practice_word_path_frame = ttk.Frame(path_frame)
        practice_word_path_frame.pack(fill='x', pady=5)
        self.practice_word_path_var = tk.StringVar(value=self.config_manager.config['paths']['practice_word_list'])
        ttk.Entry(practice_word_path_frame, textvariable=self.practice_word_path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(practice_word_path_frame, text='찾아보기', command=lambda: self.select_file('practice_word_list')).pack(side='left', padx=5)
        
        # 본시행 단어 파일
        ttk.Label(path_frame, text='본시행 단어 파일:').pack(anchor='w')
        main_word_path_frame = ttk.Frame(path_frame)
        main_word_path_frame.pack(fill='x', pady=5)
        self.main_word_path_var = tk.StringVar(value=self.config_manager.config['paths']['main_word_list'])
        ttk.Entry(main_word_path_frame, textvariable=self.main_word_path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(main_word_path_frame, text='찾아보기', command=lambda: self.select_file('main_word_list')).pack(side='left', padx=5)
        
        # 예비 연습 오디오 경로
        ttk.Label(path_frame, text='예비 연습 오디오 디렉토리 경로:').pack(anchor='w')
        practice_audio_path_frame = ttk.Frame(path_frame)
        practice_audio_path_frame.pack(fill='x', pady=5)
        self.practice_audio_path_var = tk.StringVar(value=self.config_manager.config['paths']['practice_audio_dir'])
        ttk.Entry(practice_audio_path_frame, textvariable=self.practice_audio_path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(practice_audio_path_frame, text='찾아보기', command=lambda: self.select_path('practice_audio_dir')).pack(side='left', padx=5)
        
        # 경로 생성 상태 표시
        self.status_label = tk.Label(
            self.window,
            text='',
            font=('Arial', 11),
            fg='gray'
        )
        self.status_label.pack(pady=10)
        
        # 버튼 프레임
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=20)
        
        # 확인 버튼
        ttk.Button(button_frame, text='확인', command=self.confirm).pack(side='left', padx=10)
        
        # 취소 버튼
        ttk.Button(button_frame, text='취소', command=self.cancel).pack(side='left')
        
        self.selected_paths = None

    def select_path(self, path_key):
        """디렉토리 경로를 선택합니다."""
        path = filedialog.askdirectory(
            initialdir=self.config_manager.config['paths'][path_key],
            title='디렉토리 선택'
        )
        if path:
            if path_key == 'participant_data_dir':
                self.data_path_var.set(path)
            elif path_key == 'images_dir':
                self.image_path_var.set(path)
            elif path_key == 'audio_sample_dir':
                self.audio_path_var.set(path)
            elif path_key == 'practice_audio_dir':
                self.practice_audio_path_var.set(path)
            self.check_paths()

    def select_file(self, path_key):
        """파일을 선택합니다."""
        file = filedialog.askopenfilename(
            initialdir=os.path.dirname(self.config_manager.config['paths'][path_key]),
            title='파일 선택',
            filetypes=[('Excel files', '*.xlsx')]
        )
        if file:
            try:
                # Excel 파일 읽기 테스트
                df = pd.read_excel(file)
                if '단어' not in df.columns:
                    messagebox.showerror("단어 파일 형식 오류", 
                                       "선택된 Excel 파일에 '단어' 열이 없습니다.\n"
                                       "올바른 형식의 파일을 선택해주세요.")
                    return
                
                # path_key에 따라 올바른 변수 업데이트
                if path_key == 'practice_word_list':
                    self.practice_word_path_var.set(file)
                elif path_key == 'main_word_list':
                    self.main_word_path_var.set(file)
                    
                self.check_paths()
            except Exception as e:
                messagebox.showerror("파일 읽기 오류", 
                                   f"Excel 파일을 읽는 중 오류가 발생했습니다:\n{str(e)}\n\n"
                                   "올바른 Excel 파일을 선택해주세요.")

    def check_paths(self):
        """경로 유효성을 검사합니다."""
        data_path = self.data_path_var.get()
        image_path = self.image_path_var.get()
        audio_path = self.audio_path_var.get()
        practice_word_path = self.practice_word_path_var.get()
        main_word_path = self.main_word_path_var.get()
        practice_audio_path = self.practice_audio_path_var.get()
        
        if not all([data_path, image_path, audio_path, practice_word_path, main_word_path, practice_audio_path]):
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
            
        # 오디오 경로 확인
        if not os.path.exists(audio_path):
            try:
                os.makedirs(audio_path)
            except Exception as e:
                self.status_label.config(
                    text=f'오디오 경로 생성 실패: {str(e)}',
                    fg='red'
                )
                return
                
        # 오디오 파일 확인
        audio_files = [f for f in os.listdir(audio_path) 
                      if f.endswith('.wav') and not f.startswith('._')]
        if not audio_files:
            self.status_label.config(
                text='오디오 경로에 WAV 파일이 없습니다.',
                fg='red'
            )
            return
            
        # 예비 연습 단어 파일 확인
        if not os.path.exists(practice_word_path):
            self.status_label.config(
                text='예비 연습 단어 파일이 없습니다.',
                fg='red'
            )
            return
            
        try:
            # 예비 연습 단어 파일 읽기 테스트
            df = pd.read_excel(practice_word_path)
            if '단어' not in df.columns:
                self.status_label.config(
                    text='예비 연습 단어 파일에 "단어" 열이 없습니다.',
                    fg='red'
                )
                return
        except Exception as e:
            self.status_label.config(
                text=f'예비 연습 단어 파일을 읽을 수 없습니다: {str(e)}',
                fg='red'
            )
            return
            
        # 본시행 단어 파일 확인
        if not os.path.exists(main_word_path):
            self.status_label.config(
                text='본시행 단어 파일이 없습니다.',
                fg='red'
            )
            return
            
        try:
            # 본시행 단어 파일 읽기 테스트
            df = pd.read_excel(main_word_path)
            if '단어' not in df.columns:
                self.status_label.config(
                    text='본시행 단어 파일에 "단어" 열이 없습니다.',
                    fg='red'
                )
                return
        except Exception as e:
            self.status_label.config(
                text=f'본시행 단어 파일을 읽을 수 없습니다: {str(e)}',
                fg='red'
            )
            return
            
        # 예비 연습 오디오 경로 확인
        if not os.path.exists(practice_audio_path):
            try:
                os.makedirs(practice_audio_path)
            except Exception as e:
                self.status_label.config(
                    text=f'예비 연습 오디오 경로 생성 실패: {str(e)}',
                    fg='red'
                )
                return
                
        # 예비 연습 오디오 파일 확인
        practice_audio_files = [f for f in os.listdir(practice_audio_path) 
                              if f.endswith('.wav') and not f.startswith('._')]
        if not practice_audio_files:
            self.status_label.config(
                text='예비 연습 오디오 경로에 WAV 파일이 없습니다.',
                fg='red'
            )
            return
                
        self.status_label.config(
            text='모든 경로와 파일이 유효합니다.',
            fg='green'
        )

    def confirm(self):
        """설정을 확인하고 저장합니다."""
        data_path = self.data_path_var.get()
        image_path = self.image_path_var.get()
        audio_path = self.audio_path_var.get()
        practice_word_path = self.practice_word_path_var.get()
        main_word_path = self.main_word_path_var.get()
        practice_audio_path = self.practice_audio_path_var.get()
        
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
                
        if not os.path.exists(audio_path):
            try:
                os.makedirs(audio_path)
            except Exception as e:
                messagebox.showerror("오류", f"오디오 경로를 생성할 수 없습니다:\n{str(e)}")
                return
                
        if not os.path.exists(practice_audio_path):
            try:
                os.makedirs(practice_audio_path)
            except Exception as e:
                messagebox.showerror("오류", f"예비 연습 오디오 경로를 생성할 수 없습니다:\n{str(e)}")
                return
        
        # config 파일 업데이트
        self.config_manager.config['paths'].update({
            'participant_data_dir': data_path,
            'images_dir': image_path,
            'audio_sample_dir': audio_path,
            'main_word_list': main_word_path,
            'practice_word_list': practice_word_path,
            'practice_audio_dir': practice_audio_path
        })
        self.config_manager.save_config(self.config_manager.config)
        
        self.selected_paths = {
            'participant_data_dir': data_path,
            'images_dir': image_path,
            'audio_sample_dir': audio_path,
            'main_word_list': main_word_path,
            'practice_word_list': practice_word_path,
            'practice_audio_dir': practice_audio_path
        }
        self.window.quit()
    
    def cancel(self):
        if messagebox.askyesno("종료 확인", "실험을 종료하시겠습니까?"):
            self.selected_paths = None
            self.window.quit()
            sys.exit()  # 프로그램 완전 종료
    
    def show(self):
        """설정 창을 표시합니다."""
        self.window.mainloop()
        self.window.destroy()
        return self.selected_paths

    def get_config(self):
        """현재 설정을 반환합니다."""
        return self.config_manager.config 