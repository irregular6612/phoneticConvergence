import tkinter as tk
from tkinter import messagebox, ttk, filedialog
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
from config import ConfigManager, ConfigWindow
from audio import AudioConstants, AudioRecorder, AudioDeviceWindow, AudioPlayer
from ui import ParticipantInfoWindow, AudioPlaybackWindow, MainExperimentWindow, ListSelectionWindow, WordPresentationWindow
from data import DataManager, StageInstruction
import sys
import shutil

# 단어 리스트 (예시)
WORDS = ['사과', '바나나', '오렌지', '포도', '키위', '딸기', '수박', '참외']

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

def main():
    while True:  # 참가자 정보 입력을 반복할 수 있도록 루프 추가
        # 경로 설정 창 표시
        config_window = ConfigWindow()
        selected_paths = config_window.show()
        
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
        
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        # 설정된 경로들을 config에 저장
        config_manager.config['paths'].update(selected_paths)
        config_manager.save_config(config_manager.config)
        
        # 경로 유효성 검사
        if not config_manager.verify_paths():
            messagebox.showwarning("경로 검증", 
                                 "일부 경로가 올바르지 않습니다.\n"
                                 "설정을 확인해주세요.")
            if messagebox.askyesno("설정 수정", "설정을 수정하시겠습니까?"):
                config_window = ConfigWindow()
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