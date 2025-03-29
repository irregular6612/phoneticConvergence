import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class ConfigManager:
    def __init__(self):
        self.config_file = self.find_config_file()
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
        """config.json 파일에서 설정을 로드합니다."""
        try:
            if self.config_file and os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 기본 설정
                default_config = {
                    "paths": {
                        "word_file": "filtered_df.xlsx",
                        "audio_sample_dir": "audio-sample",
                        "participant_data_dir": "participants"
                    },
                    "recording": {
                        "sample_rate": 44100,
                        "channels": 1
                    }
                }
                
                # config.json 저장 경로 선택
                messagebox.showinfo(
                    "설정 파일 생성",
                    "config.json 파일이 없습니다. 저장할 위치를 선택해주세요."
                )
                
                config_path = filedialog.asksaveasfilename(
                    title='config.json 저장 위치 선택',
                    defaultextension='.json',
                    initialfile='config.json',
                    filetypes=[('JSON files', '*.json')],
                    initialdir=os.getcwd()
                )
                
                if config_path:
                    self.config_file = config_path
                    self.save_config(default_config)
                    return default_config
                else:
                    messagebox.showerror("오류", "설정 파일 저장 위치가 선택되지 않았습니다.")
                    return None
                    
        except Exception as e:
            messagebox.showerror("설정 로드 오류", f"설정 파일을 로드하는 중 오류가 발생했습니다: {str(e)}")
            return None
            
    def save_config(self, config):
        """설정을 config.json 파일에 저장합니다."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.config = config
        except Exception as e:
            messagebox.showerror("설정 저장 오류", f"설정을 저장하는 중 오류가 발생했습니다: {str(e)}")
            
    def verify_paths(self):
        """모든 경로가 유효한지 확인합니다."""
        paths = self.config['paths']
        invalid_paths = []
        
        # 단어 파일 확인
        if not os.path.exists(paths['word_file']):
            invalid_paths.append(('word_file', '단어 파일'))
            
        # 오디오 샘플 디렉토리 확인
        if not os.path.exists(paths['audio_sample_dir']):
            invalid_paths.append(('audio_sample_dir', '오디오 샘플 디렉토리'))
            
        # 참가자 데이터 디렉토리 확인
        if not os.path.exists(paths['participant_data_dir']):
            try:
                os.makedirs(paths['participant_data_dir'])
            except:
                invalid_paths.append(('participant_data_dir', '참가자 데이터 디렉토리'))
                
        return invalid_paths

class ConfigWindow:
    def __init__(self, config_manager):
        self.window = tk.Tk()
        self.window.title('설정')
        self.window.geometry('600x400')
        
        self.config_manager = config_manager
        self.config = config_manager.config.copy()
        
        # 경로 설정 프레임
        path_frame = ttk.LabelFrame(self.window, text='경로 설정', padding=10)
        path_frame.pack(fill='x', padx=10, pady=5)
        
        # 단어 파일 경로
        self.create_path_entry(path_frame, '단어 파일:', 'word_file', 0)
        
        # 오디오 샘플 디렉토리
        self.create_path_entry(path_frame, '오디오 샘플 디렉토리:', 'audio_sample_dir', 1)
        
        # 참가자 데이터 디렉토리
        self.create_path_entry(path_frame, '참가자 데이터 디렉토리:', 'participant_data_dir', 2)
        
        # 상태 메시지 레이블
        self.status_label = ttk.Label(
            self.window,
            text='',
            font=('Arial', 10),
            foreground='gray'
        )
        self.status_label.pack(pady=5)
        
        # 버튼 프레임
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="저장", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
    def create_path_entry(self, parent, label_text, path_key, row):
        # 레이블
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky='e')
        
        # 경로 입력 필드
        var = tk.StringVar(value=self.config['paths'][path_key])
        entry = ttk.Entry(parent, textvariable=var, width=50)
        entry.grid(row=row, column=1, padx=5, pady=5)
        
        def browse():
            if path_key == 'word_file':
                path = filedialog.askopenfilename(
                    title='단어 파일 선택',
                    filetypes=[('Excel files', '*.xlsx')],
                    initialdir=os.path.dirname(var.get()) if var.get() else os.getcwd()
                )
            else:
                path = filedialog.askdirectory(
                    title='디렉토리 선택',
                    initialdir=var.get() if var.get() else os.getcwd()
                )
            if path:
                var.set(path)
                self.config['paths'][path_key] = path
                self.check_path_validity(path_key, path)
                
        def validate_path(*args):
            self.check_path_validity(path_key, var.get())
        
        # 경로 변경 시 자동 검증
        var.trace_add('write', validate_path)
        
        # 찾아보기 버튼
        ttk.Button(parent, text="찾아보기", command=browse).grid(row=row, column=2, padx=5, pady=5)
        
    def check_path_validity(self, path_key, path):
        if not path:
            self.status_label.config(
                text=f'{path_key} 경로를 입력해주세요.',
                foreground='red'
            )
            return False
            
        if path_key == 'word_file':
            if not os.path.exists(path):
                self.status_label.config(
                    text=f'단어 파일이 존재하지 않습니다: {path}',
                    foreground='red'
                )
                return False
            if not path.endswith('.xlsx'):
                self.status_label.config(
                    text='단어 파일은 .xlsx 형식이어야 합니다.',
                    foreground='red'
                )
                return False
        else:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                    self.status_label.config(
                        text=f'새 디렉토리가 생성되었습니다: {path}',
                        foreground='blue'
                    )
                except Exception as e:
                    self.status_label.config(
                        text=f'디렉토리 생성 실패: {str(e)}',
                        foreground='red'
                    )
                    return False
            else:
                # 디렉토리 쓰기 권한 확인
                try:
                    test_file = os.path.join(path, '.test')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    self.status_label.config(
                        text='경로가 유효합니다.',
                        foreground='green'
                    )
                except Exception as e:
                    self.status_label.config(
                        text=f'디렉토리에 대한 쓰기 권한이 없습니다: {str(e)}',
                        foreground='red'
                    )
                    return False
        
        return True
        
    def save(self):
        # 모든 경로 유효성 검사
        for path_key in self.config['paths']:
            if not self.check_path_validity(path_key, self.config['paths'][path_key]):
                messagebox.showerror("오류", "모든 경로가 유효하지 않습니다. 다시 확인해주세요.")
                return
                
        self.config_manager.save_config(self.config)
        self.window.quit()
        
    def cancel(self):
        self.window.quit()
        
    def show(self):
        self.window.mainloop()
        self.window.destroy()
        return self.config 