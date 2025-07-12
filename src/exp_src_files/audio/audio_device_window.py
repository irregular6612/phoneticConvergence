import tkinter as tk
from tkinter import messagebox, ttk
import tkinter.ttk as ttk
import sounddevice as sd
import numpy as np
import soundfile as sf
import os
import sys
from audio import AudioConstants


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
