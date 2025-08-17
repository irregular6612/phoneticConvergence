
"""
TextGrid I/O Module (통합 버전)

TextGrid 파일을 읽고, 수정하고, 저장할 수 있는 통합 모듈입니다.
- parse: TextGrid 파일 파싱
- find_interval: 특정 tier_name과 text로 interval 찾기
- boundary_fix: 전체 boundary 수정
- validate_boundaries: boundary 무결성 검사

Author: Juhyeon Park
Date: 2025-08-14
"""

import os
import numpy as np
import pandas as pd
import parselmouth
from typing import Tuple, List, Optional, Dict, Union, Any
import logging
from pathlib import Path
from tqdm import tqdm
from dataclasses import dataclass
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Interval:
    """Interval 정보를 담는 데이터 클래스"""
    xmin: float
    xmax: float
    text: str
    interval_number: int

@dataclass
class Tier:
    """Tier 정보를 담는 데이터 클래스"""
    name: str
    xmin: float
    xmax: float
    intervals: List[Interval]

@dataclass
class TextGridData:
    """TextGrid 전체 데이터를 담는 데이터 클래스"""
    xmin: float
    xmax: float
    tiers: Dict[str, Tier]

class TextGridReader:
    """
    TextGrid 파일을 읽고, 수정하고, 저장할 수 있는 통합 클래스
    """
    
    def __init__(self, textgrid_path: str, fix_boundary_integrity: bool = False, verbose: bool = False):
        """
        TextGridReader 초기화
        
        Args:
            textgrid_path (str): TextGrid 파일 경로
            fix_boundary_integrity (bool): 초기화 시 boundary 무결성 자동 수정 여부
        """
        self.textgrid_path = textgrid_path
        self.fix_boundary_integrity = fix_boundary_integrity
        self.textgrid_data = None
        self.file_info = {}
        self.verbose = verbose
        
        # Logging 설정
        if not verbose:
            logging.disable(logging.CRITICAL)
        
        # 파일이 존재하면 자동으로 읽기
        if os.path.exists(textgrid_path):
            self.read()
            # 무결점 검사 자동 실행
            if fix_boundary_integrity:
                self.check_boundary_integrity()
    
    def read(self) -> TextGridData:
        """
        TextGrid 파일을 읽어서 구조화된 데이터로 변환
        
        Returns:
            TextGridData: 파싱된 TextGrid 데이터
        """
        if not os.path.exists(self.textgrid_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.textgrid_path}")
        
        if self.verbose:
            logger.info(f"TextGrid 파일 파싱 시작: {self.textgrid_path}")
        
        with open(self.textgrid_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 파일 정보 파싱
        self.file_info = {}
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('item') and not line.startswith('intervals'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                self.file_info[key] = value
        
        xmin = float(self.file_info.get('xmin', 0))
        xmax = float(self.file_info.get('xmax', 0))
        
        # Tier 정보 파싱
        tiers = {}
        current_tier = None
        current_intervals = []
        reading_interval = False
        interval_data = {}
        interval_number = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Tier 시작 - "item [1]:" 다음에 "class = "IntervalTier""와 "name = "xxx""가 있는지 확인
            if line.startswith('item [') and i + 2 < len(lines):
                # 다음 두 줄을 확인
                next_line = lines[i + 1].strip()
                next_next_line = lines[i + 2].strip()
                
                if ('class = "IntervalTier"' in next_line and 'name = "' in next_next_line):
                    # 이전 tier 저장
                    if current_tier is not None:
                        tiers[current_tier] = Tier(
                            name=current_tier,
                            xmin=xmin,
                            xmax=xmax,
                            intervals=current_intervals
                        )
                    
                    # 새 tier 시작
                    current_tier = next_next_line.split('"')[1]
                    current_intervals = []
                    reading_interval = False
                    logger.debug(f"새 tier 발견: {current_tier}")
            
            # Interval 시작
            elif 'intervals [' in line:
                reading_interval = True
                interval_data = {}
                try:
                    interval_number = int(line.split('[')[1].split(']')[0])
                except (IndexError, ValueError):
                    interval_number = None
            
            # Interval 데이터 읽기
            elif reading_interval and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                interval_data[key] = value
                
                # Interval 완성 (xmin, xmax, text 모두 있으면)
                if 'xmin' in interval_data and 'xmax' in interval_data and 'text' in interval_data:
                    start = float(interval_data['xmin'])
                    end = float(interval_data['xmax'])
                    text = interval_data['text']
                    
                    current_intervals.append(Interval(
                        xmin=start,
                        xmax=end,
                        text=text,
                        interval_number=interval_number
                    ))
                    reading_interval = False
                    interval_data = {}
            
            i += 1
        
        # 마지막 tier 추가
        if current_tier is not None:
            tiers[current_tier] = Tier(
                name=current_tier,
                xmin=xmin,
                xmax=xmax,
                intervals=current_intervals
            )
        
        self.textgrid_data = TextGridData(xmin=xmin, xmax=xmax, tiers=tiers)
        
        if self.verbose:
            logger.info(f"파싱 완료: {len(tiers)}개 tier, 총 {sum(len(t.intervals) for t in tiers.values())}개 interval")
        
        return self.textgrid_data
    
    def find_interval(self, tier_name: str, text: str) -> Optional[Interval]:
        """
        특정 tier_name과 text로 해당 interval을 찾습니다.
        
        Args:
            tier_name (str): 찾을 tier 이름
            text (str): 찾을 텍스트
            
        Returns:
            Optional[Interval]: 찾은 interval 또는 None
        """
        if not self.textgrid_data:
            logger.error("TextGrid 데이터가 로드되지 않았습니다. read() 메서드를 먼저 호출하세요.")
            return None
        
        if tier_name not in self.textgrid_data.tiers:
            logger.warning(f"Tier '{tier_name}'을 찾을 수 없습니다.")
            return None
        
        tier = self.textgrid_data.tiers[tier_name]
        
        for interval in tier.intervals:
            if interval.text == text:
                logger.info(f"Interval 찾음: tier='{tier_name}', text='{text}', "
                           f"xmin={interval.xmin:.3f}, xmax={interval.xmax:.3f}, "
                           f"interval_number={interval.interval_number}")
                return interval
        
        logger.warning(f"Tier '{tier_name}'에서 text '{text}'를 찾을 수 없습니다.")
        return None
    
    def find_intervals_by_text(self, tier_name: str, text: str) -> List[Interval]:
        """
        특정 tier_name과 text로 해당하는 모든 interval을 찾습니다.
        
        Args:
            tier_name (str): 찾을 tier 이름
            text (str): 찾을 텍스트
            
        Returns:
            List[Interval]: 찾은 interval들의 리스트
        """
        if not self.textgrid_data:
            logger.error("TextGrid 데이터가 로드되지 않았습니다. read() 메서드를 먼저 호출하세요.")
            return []
        
        if tier_name not in self.textgrid_data.tiers:
            logger.warning(f"Tier '{tier_name}'을 찾을 수 없습니다.")
            return []
        
        tier = self.textgrid_data.tiers[tier_name]
        found_intervals = []
        
        for interval in tier.intervals:
            if interval.text == text:
                found_intervals.append(interval)
        
        logger.info(f"Tier '{tier_name}'에서 text '{text}'를 가진 {len(found_intervals)}개 interval을 찾았습니다.")
        return found_intervals
    
    def write(self, output_path: Optional[str] = None) -> bool:
        """
        TextGrid 데이터를 파일로 저장합니다.
        
        Args:
            output_path (Optional[str]): 출력 파일 경로 (None이면 원본 파일에 저장)
            
        Returns:
            bool: 저장 성공 여부
        """
        if not self.textgrid_data:
            logger.error("TextGrid 데이터가 로드되지 않았습니다. read() 메서드를 먼저 호출하세요.")
            return False
        
        if output_path is None:
            output_path = self.textgrid_path
        
        try:
            # 전체 파일의 xmin, xmax 계산 (모든 tier의 최소/최대값)
            all_xmins = []
            all_xmaxs = []
            for tier in self.textgrid_data.tiers.values():
                if tier.intervals:
                    sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
                    all_xmins.append(sorted_intervals[0].xmin)
                    all_xmaxs.append(sorted_intervals[-1].xmax)
            
            if all_xmins and all_xmaxs:
                file_xmin = min(all_xmins)
                file_xmax = max(all_xmaxs)
            else:
                file_xmin = self.textgrid_data.xmin
                file_xmax = self.textgrid_data.xmax
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # 파일 헤더
                f.write('File type = "ooTextFile"\n')
                f.write('Object class = "TextGrid"\n\n')
                
                # 파일 정보
                f.write(f'xmin = {file_xmin}\n')
                f.write(f'xmax = {file_xmax}\n')
                f.write('tiers? <exists>\n')
                f.write(f'size = {len(self.textgrid_data.tiers)}\n')
                f.write('item []:\n')
                
                # Tier 정보
                for tier_idx, (tier_name, tier) in enumerate(self.textgrid_data.tiers.items(), 1):
                    # 각 tier의 xmin, xmax 계산 (해당 tier의 첫 번째/마지막 interval 기준)
                    if tier.intervals:
                        sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
                        tier_xmin = sorted_intervals[0].xmin
                        tier_xmax = sorted_intervals[-1].xmax
                    else:
                        tier_xmin = tier.xmin
                        tier_xmax = tier.xmax
                    
                    f.write(f'    item [{tier_idx}]:\n')
                    f.write('        class = "IntervalTier"\n')
                    f.write(f'        name = "{tier.name}"\n')
                    f.write(f'        xmin = {tier_xmin}\n')
                    f.write(f'        xmax = {tier_xmax}\n')
                    f.write(f'        intervals: size = {len(tier.intervals)}\n')
                    
                    # Interval 정보
                    for interval_idx, interval in enumerate(tier.intervals, 1):
                        f.write(f'        intervals [{interval_idx}]:\n')
                        f.write(f'            xmin = {interval.xmin}\n')
                        f.write(f'            xmax = {interval.xmax}\n')
                        f.write(f'            text = "{interval.text}"\n')
            
            if self.verbose:
                logger.info(f"TextGrid 파일 저장 완료: {output_path}")
                logger.info(f"파일 범위: {file_xmin:.3f} ~ {file_xmax:.3f}")
            return True
            
        except Exception as e:
            if self.verbose:
                logger.error(f"파일 저장 실패: {e}")
            return False
    
    def boundary_fix(self, output_path: Optional[str] = None, 
                    backup: bool = True, inplace: bool = False) -> bool:
        """
        TextGrid 파일의 boundary 문제를 수정합니다.
        
        Args:
            output_path (Optional[str]): 출력 파일 경로 (None이면 자동 생성)
            backup (bool): 백업 파일 생성 여부
            inplace (bool): 원본 파일에 덮어쓰기 여부
            
        Returns:
            bool: 수정 성공 여부
        """
        if not self.textgrid_data:
            logger.error("TextGrid 데이터가 로드되지 않았습니다. read() 메서드를 먼저 호출하세요.")
            return False
        
        if self.verbose:
            logger.info(f"Boundary 수정 시작: {self.textgrid_path}")
        
        # 백업 생성
        if backup and not inplace:
            backup_path = self.textgrid_path + '.backup'
            try:
                shutil.copy2(self.textgrid_path, backup_path)
                if self.verbose:
                    logger.info(f"백업 파일 생성: {backup_path}")
            except Exception as e:
                if self.verbose:
                    logger.error(f"백업 생성 실패: {e}")
                return False
        
        # 각 tier별로 boundary 수정
        total_fixes = 0
        for tier_name, tier in self.textgrid_data.tiers.items():
            if not tier.intervals:
                continue
            
            if self.verbose:
                logger.info(f"Tier '{tier_name}' boundary 수정 중...")
            tier_fixes = 0
            
            # Interval들을 시작 시간 기준으로 정렬
            sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
            
            for i in range(len(sorted_intervals) - 1):
                current = sorted_intervals[i]
                next_interval = sorted_intervals[i + 1]
                
                # 경계 불일치 검사 및 수정
                if current.xmax != next_interval.xmin:
                    old_current_xmax = current.xmax
                    old_next_xmin = next_interval.xmin
                    
                    #redefine boundary
                    allowed_vowels = ['a', 'i', 'u', 'ae', 'o']
                    # 우선 순위: 모음 > 자음 > sp
                    if current.text in allowed_vowels:
                        new_boundary = current.xmax
                    elif next_interval.text in allowed_vowels:
                        new_boundary = next_interval.xmin
                    elif current.text == 'sp':
                        new_boundary = next_interval.xmin
                    elif next_interval.text == 'sp':
                        new_boundary = current.xmax
                    else: # 자음 + 자음이겠지.
                        new_boundary = (current.xmax + next_interval.xmin) / 2.0
                        
                    current.xmax = new_boundary
                    next_interval.xmin = new_boundary
                    
                    if self.verbose:
                        logger.info(f"  Boundary 수정: interval {current.interval_number} ~ {next_interval.interval_number}")
                        logger.info(f"    {old_current_xmax:.3f} ~ {old_next_xmin:.3f} -> {new_boundary:.3f}")
                    tier_fixes += 1
            
            # 수정 후 tier의 xmin, xmax 자동 업데이트
            if tier.intervals:
                old_tier_xmin, old_tier_xmax = tier.xmin, tier.xmax
                tier.xmin = sorted_intervals[0].xmin
                tier.xmax = sorted_intervals[-1].xmax
                
                if old_tier_xmin != tier.xmin or old_tier_xmax != tier.xmax:
                    if self.verbose:
                        logger.info(f"  Tier '{tier_name}' 범위 자동 업데이트:")
                        logger.info(f"    xmin: {old_tier_xmin:.3f} -> {tier.xmin:.3f}")
                        logger.info(f"    xmax: {old_tier_xmax:.3f} -> {tier.xmax:.3f}")
            
            total_fixes += tier_fixes
            if self.verbose:
                logger.info(f"Tier '{tier_name}': {tier_fixes}개 boundary 수정 완료")
        
        # 전체 파일의 xmin, xmax 자동 업데이트
        all_xmins = []
        all_xmaxs = []
        for tier in self.textgrid_data.tiers.values():
            if tier.intervals:
                sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
                all_xmins.append(sorted_intervals[0].xmin)
                all_xmaxs.append(sorted_intervals[-1].xmax)
        
        if all_xmins and all_xmaxs:
            old_file_xmin, old_file_xmax = self.textgrid_data.xmin, self.textgrid_data.xmax
            self.textgrid_data.xmin = min(all_xmins)
            self.textgrid_data.xmax = max(all_xmaxs)
            
            if old_file_xmin != self.textgrid_data.xmin or old_file_xmax != self.textgrid_data.xmax:
                if self.verbose:
                    logger.info(f"파일 전체 범위 자동 업데이트:")
                    logger.info(f"  xmin: {old_file_xmin:.3f} -> {self.textgrid_data.xmin:.3f}")
                    logger.info(f"  xmax: {old_file_xmax:.3f} -> {self.textgrid_data.xmax:.3f}")
        
        # 출력 파일 경로 결정
        if inplace:
            final_output_path = self.textgrid_path
        elif output_path:
            final_output_path = output_path
        else:
            base_name = os.path.splitext(self.textgrid_path)[0]
            final_output_path = f"{base_name}.TextGrid"
        
        # 수정된 파일 저장
        success = self.write(final_output_path)
        
        if success:
            if self.verbose:
                logger.info(f"Boundary 수정 완료: {total_fixes}개 수정, 출력: {final_output_path}")
        else:
            if self.verbose:
                logger.error("Boundary 수정 실패")
        
        return success
    
    def validate_boundaries(self, tolerance: float = None) -> Dict[str, List[Tuple[int, float, float]]]:
        """
        TextGrid 데이터의 boundary 무결성을 검사합니다.
        
        Args:
            tolerance (float): 허용 오차 (None이면 허용치 않음.)
            
        Returns:
            Dict[str, List[Tuple[int, float, float]]]: 각 tier별 문제점들
        """
        if not self.textgrid_data:
            logger.error("TextGrid 데이터가 로드되지 않았습니다. read() 메서드를 먼저 호출하세요.")
            return {}
        
        issues = {}
        
        for tier_name, tier in self.textgrid_data.tiers.items():
            if not tier.intervals:
                continue
            
            tier_issues = []
            sorted_intervals = sorted(tier.intervals, key=lambda x: x.xmin)
            
            for i in range(len(sorted_intervals) - 1):
                current = sorted_intervals[i]
                next_interval = sorted_intervals[i + 1]


                if tolerance: 
                    if abs(current.xmax - next_interval.xmin) > tolerance:
                        tier_issues.append((
                            current.interval_number,
                            current.xmax,
                            next_interval.xmin
                        ))
                else:              
                    if current.xmax != next_interval.xmin: # 조건을 strict로 수정.
                        tier_issues.append((
                            current.interval_number,
                            current.xmax,
                            next_interval.xmin
                        ))
            
            if tier_issues:
                issues[tier_name] = tier_issues
        
        return issues
    
    def check_boundary_integrity(self) -> bool:
        """
        TextGrid 파일의 경계 무결점 검사 (기존 호환성을 위한 메서드)
        
        Returns:
            bool: 무결성 검사 통과 여부
        """
        if not self.textgrid_data:
            logger.error("TextGrid 데이터가 로드되지 않았습니다. read() 메서드를 먼저 호출하세요.")
            return False
        
        if self.verbose:
            logger.info(f"TextGrid 무결점 검사 시작: {self.textgrid_path}")
        
        issues = self.validate_boundaries()
        total_issues = sum(len(issues_list) for issues_list in issues.values())
        
        for tier_name, tier_issues in issues.items():
            logger.warning(f"Tier '{tier_name}': {len(tier_issues)}개 boundary 문제 발견")
            for interval_num, xmax, next_xmin in tier_issues[:3]:  # 처음 3개만 표시
                logger.error(f"  interval {interval_num}: {xmax:.3f} vs {next_xmin:.3f}")
        
        if total_issues == 0:
            if self.verbose:
                logger.info("🎉 모든 tier의 경계가 정상입니다!")
            return True
        else:
            if self.verbose:
                logger.error(f"❌ 총 {total_issues}개의 경계 문제가 발견되었습니다.")
            if self.fix_boundary_integrity:
                if self.verbose:
                    logger.info("🔄 경계 무결성 수정 중...")
                return self.boundary_fix()
            else:
                return False
    
    def get_tier_names(self) -> List[str]:
        """
        tier 이름 목록 반환
        """
        if not self.textgrid_data:
            return []
        return list(self.textgrid_data.tiers.keys())
    
    def get_intervals_by_tier(self, tier_name: str) -> List[Interval]:
        """
        특정 tier의 interval 목록 반환
        """
        if not self.textgrid_data:
            return []
        tier = self.textgrid_data.tiers.get(tier_name)
        return tier.intervals if tier else []
    
    def get_total_duration(self) -> float:
        """
        전체 음성 길이 반환
        """
        if not self.textgrid_data:
            return 0.0
        return self.textgrid_data.xmax
