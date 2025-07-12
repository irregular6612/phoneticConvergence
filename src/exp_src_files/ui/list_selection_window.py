import tkinter as tk
from tkinter import messagebox
import sys
import os
import pandas as pd
from config import ConfigManager
from tkinter import ttk

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
