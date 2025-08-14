
"""
TextGrid I/O Module

This module provides functions to read and write TextGrid files.

Author: Juhyeon Park
Date: 2025-08-14
"""

import os
import numpy as np
import pandas as pd
import parselmouth
from typing import Tuple, List, Optional, Dict, Union
import logging
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextGridReader:
    def __init__(self, textgrid_path, fix_boundary_integrity=False):
        self.textgrid_path = textgrid_path
        self.fix_boundary_integrity = fix_boundary_integrity
        self.tiers_data = {}
        self.file_info = {}
        self.read()
        # 무결점 검사 자동 실행
        self.check_boundary_integrity()
        
    def read(self):
        """
        TextGrid 파일을 읽어서 구조화된 데이터로 변환
        """
        if not os.path.exists(self.textgrid_path):
            raise FileNotFoundError(f"{self.textgrid_path} is not valid path. Please check the file path.")
        
        with open(self.textgrid_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # 파일 정보 읽기
            self._read_file_info(lines)
            
            # tier 정보 읽기
            self._read_tiers(lines)
            
        return self.tiers_data
    
    def _read_file_info(self, lines):
        """
        파일의 기본 정보 읽기
        """
        for line in lines:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                self.file_info[key] = value
    
    def _read_tiers(self, lines):
        """
        tier 정보 읽기
        """
        current_tier = None
        current_intervals = []
        reading_interval = False
        interval_data = {}
        interval_number = None
        
        for line in lines:
            line = line.strip()
            
            # tier 시작
            if 'name = "' in line:
                if current_tier is not None:
                    self.tiers_data[current_tier] = current_intervals
                current_tier = line.split('"')[1]
                current_intervals = []
                reading_interval = False
            
            # interval 시작 - 번호 추출
            elif 'intervals [' in line:
                reading_interval = True
                interval_data = {}
                # interval 번호 추출: "intervals [1]:" -> 1
                try:
                    interval_number = int(line.split('[')[1].split(']')[0])
                except (IndexError, ValueError):
                    interval_number = None
            
            # interval 데이터 읽기
            elif reading_interval and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                interval_data[key] = value
                
                # interval 완성
                if 'text' in interval_data:
                    start = float(interval_data['xmin'])
                    end = float(interval_data['xmax'])
                    text = interval_data['text']
                    # interval 번호를 포함하여 저장
                    current_intervals.append((start, end, text, interval_number))
                    reading_interval = False
        
        # 마지막 tier 추가
        if current_tier is not None:
            self.tiers_data[current_tier] = current_intervals
    
    def fix_boundary_integrity(self):
        """
        경계 무결성 수정
        각 tier별로 경계 불일치 문제를 자동으로 수정하고 파일에 저장
        """
        logger.info("🔄 경계 무결성 수정 시작...")
        
        # 원본 파일 백업
        backup_path = self.textgrid_path + '.backup'
        try:
            import shutil
            shutil.copy2(self.textgrid_path, backup_path)
            logger.info(f"원본 파일 백업 완료: {backup_path}")
        except Exception as e:
            logger.error(f"백업 실패: {e}")
            return False
        
        # 수정된 데이터 저장
        try:
            self._write_textgrid_file()
            logger.info("수정된 TextGrid 파일 저장 완료")
            
            # 수정 후 다시 검사
            logger.info("수정 결과 검증 중...")
            self.read()  # 파일 다시 읽기
            is_valid = self.check_boundary_integrity()
            
            if is_valid:
                logger.info("✅ 경계 무결성 수정 완료!")
                return True
            else:
                logger.error("❌ 수정 후에도 문제가 남아있습니다.")
                return False
                
        except Exception as e:
            logger.error(f"파일 저장 실패: {e}")
            # 백업에서 복원
            try:
                shutil.copy2(backup_path, self.textgrid_path)
                logger.info("백업에서 원본 복원 완료")
            except Exception as restore_error:
                logger.error(f"복원 실패: {restore_error}")
            return False
    
    def _write_textgrid_file(self):
        """
        수정된 데이터를 TextGrid 파일 형식으로 저장
        """
        try:
            with open(self.textgrid_path, 'w', encoding='utf-8') as f:
                # 파일 헤더 작성
                f.write('File type = "ooTextFile"\n')
                f.write('Object class = "TextGrid"\n\n')
                
                # 파일 정보 작성
                for key, value in self.file_info.items():
                    if key in ['xmin', 'xmax']:
                        f.write(f'{key} = {value}\n')
                    else:
                        f.write(f'{key} = "{value}"\n')
                
                f.write('\n')
                
                # tier 정보 작성
                for tier_name, intervals in self.tiers_data.items():
                    f.write(f'tiers [1] size = {len(intervals)}\n')
                    f.write(f'item [1]:\n')
                    f.write(f'\tclass = "IntervalTier"\n')
                    f.write(f'\tname = "{tier_name}"\n')
                    f.write(f'\txmin = {self.file_info.get("xmin", 0)}\n')
                    f.write(f'\txmax = {self.file_info.get("xmax", 0)}\n')
                    f.write(f'\tintervals: size = {len(intervals)}\n')
                    
                    # 수정된 interval 데이터 작성
                    for i, (start, end, text, interval_num) in enumerate(intervals, 1):
                        f.write(f'\tintervals [{i}]:\n')
                        f.write(f'\t\txmin = {start}\n')
                        f.write(f'\t\txmax = {end}\n')
                        f.write(f'\t\ttext = "{text}"\n')
            
            logger.info("수정된 TextGrid 파일 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"파일 저장 실패: {e}")
            return False
    
    def _fix_tier_boundaries(self, tier_name, intervals):
        """
        특정 tier의 경계 문제를 수정
        """
        if not intervals:
            return intervals
        
        fixed_intervals = []
        #sorted_intervals = sorted(intervals, key=lambda x: x[0])  # 시작 시간 기준 정렬
        sorted_intervals = intervals
        
        for i, (start, end, text, interval_num) in enumerate(sorted_intervals):
            if i == 0:
                # 첫 번째 interval은 그대로 유지
                fixed_intervals.append((start, end, text, interval_num))
            else:
                # 이전 interval의 end_time을 현재 interval의 start_time으로 설정
                prev_end = fixed_intervals[-1][1]
                fixed_intervals.append((prev_end, end, text, interval_num))
                logger.info(f"  수정: interval [{interval_num}] start_time을 {start:.3f}s에서 {prev_end:.3f}s로 조정")
        
        return fixed_intervals
    
    def check_boundary_integrity(self):
        """
        TextGrid 파일의 경계 무결점 검사
        각 tier별로 연속된 interval들의 경계가 일치하는지 확인
        """
        logger.info(f"TextGrid 무결점 검사 시작: {self.textgrid_path}")
        
        total_issues = 0
        
        for tier_name, intervals in self.tiers_data.items():
            if not intervals:
                logger.warning(f"Tier '{tier_name}'에 interval이 없습니다.")
                continue
                
            # interval들을 시작 시간 기준으로 정렬 -> 정렬 안하는게 맞음.
            #sorted_intervals = sorted(intervals, key=lambda x: x[0])
            sorted_intervals =intervals
            tier_issues = 0
            
            logger.info(f"\n=== Tier '{tier_name}' 검사 중 ===")
            logger.info(f"총 {len(sorted_intervals)}개의 interval 발견")
            
            for i in range(len(sorted_intervals) - 1):
                current_interval = sorted_intervals[i]
                next_interval = sorted_intervals[i + 1]
                
                current_start, current_end, current_text, current_num = current_interval
                next_start, next_end, next_text, next_num = next_interval
                
                # 경계 불일치 검사
                if current_end != next_start:
                    tier_issues += 1
                    total_issues += 1
                    
                    logger.error(f"\n🚨 경계 불일치 발견!")
                    logger.error(f"  위치: Tier '{tier_name}'")
                    logger.error(f"  현재 interval [{current_num}]: {current_start:.3f}s ~ {current_end:.3f}s (텍스트: '{current_text}')")
                    logger.error(f"  다음 interval [{next_num}]: {next_start:.3f}s ~ {next_end:.3f}s (텍스트: '{next_text}')")
                    logger.error(f"  간격: {abs(current_end - next_start):.3f}초")
                    
                    if current_end < next_start:
                        logger.error(f"  문제: {current_end:.3f}s와 {next_start:.3f}s 사이에 {next_start - current_end:.3f}초의 빈 공간이 있습니다.")
                    else:
                        logger.error(f"  문제: {current_end:.3f}s와 {next_start:.3f}s 사이에 {current_end - next_start:.3f}초의 겹침이 있습니다.")
            
            if tier_issues == 0:
                logger.info(f"✅ Tier '{tier_name}': 모든 경계가 정상입니다.")
            else:
                logger.warning(f"⚠️  Tier '{tier_name}': {tier_issues}개의 경계 문제 발견")
        
        # 전체 결과 요약
        logger.info(f"\n=== 무결점 검사 완료 ===")
        if total_issues == 0:
            logger.info("🎉 모든 tier의 경계가 정상입니다!")
        else:
            logger.error(f"❌ 총 {total_issues}개의 경계 문제가 발견되었습니다.")
            if self.fix_boundary_integrity:
                logger.info("🔄 경계 무결성 수정 중...")
                # 각 tier별로 경계 수정
                for tier_name, intervals in self.tiers_data.items():
                    if intervals:
                        fixed_intervals = self._fix_tier_boundaries(tier_name, intervals)
                        self.tiers_data[tier_name] = fixed_intervals
                
                # 수정된 데이터로 파일 저장
                success = self._write_textgrid_file()
                if success:
                    logger.info("✅ 경계 무결성 수정 완료!")
                    # 수정 후 다시 검사
                    self.read()
                    return self.check_boundary_integrity()
                else:
                    logger.error("❌ 경계 수정 실패")
                    return False
            else:
                raise ValueError(f"❌ 총 {total_issues}개의 경계 문제가 발견되었습니다.")
        
        return total_issues == 0
    
    def get_tier_names(self):
        """
        tier 이름 목록 반환
        """
        return list(self.tiers_data.keys())
    
    def get_intervals_by_tier(self, tier_name):
        """
        특정 tier의 interval 목록 반환
        """
        return self.tiers_data.get(tier_name, [])
    
    def get_total_duration(self):
        """
        전체 음성 길이 반환
        """
        return float(self.file_info.get('xmax', 0))