import pandas as pd
import os
from datetime import datetime
import sounddevice as sd

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
        
        # 참가자 폴더 경로 사용 (folder_path는 이미 올바른 경로를 포함)
        participant_folder = folder_path
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
        # 참가자 폴더 경로 사용 (folder_path는 이미 올바른 경로를 포함)
        participant_folder = folder_path
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
