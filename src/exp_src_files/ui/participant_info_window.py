import tkinter as tk
from tkinter import messagebox
import sys


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
