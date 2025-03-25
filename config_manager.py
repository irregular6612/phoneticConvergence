import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class ConfigManager:
    def __init__(self):
        self.config_file = 'config.json'
        self.config = self.load_config()
        
    def load_config(self):
        """config.json 파일에서 설정을 로드합니다."""
        try:
            if os.path.exists(self.config_file):
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
                self.save_config(default_config)
                return default_config
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
        
        # 버튼 프레임
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="저장", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
    def create_path_entry(self, parent, label_text, path_key, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky='e')
        
        var = tk.StringVar(value=self.config['paths'][path_key])
        entry = ttk.Entry(parent, textvariable=var, width=50)
        entry.grid(row=row, column=1, padx=5, pady=5)
        
        def browse():
            if path_key == 'word_file':
                path = filedialog.askopenfilename(filetypes=[('Excel files', '*.xlsx')])
            else:
                path = filedialog.askdirectory()
            if path:
                var.set(path)
                self.config['paths'][path_key] = path
                
        ttk.Button(parent, text="찾아보기", command=browse).grid(row=row, column=2, padx=5, pady=5)
        
    def save(self):
        self.config_manager.save_config(self.config)
        self.window.quit()
        
    def cancel(self):
        self.window.quit()
        
    def show(self):
        self.window.mainloop()
        self.window.destroy()
        return self.config 