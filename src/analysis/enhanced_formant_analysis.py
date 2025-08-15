
"""
Enhanced Formant Analysis Module

This module provides improved formant analysis functions using Parselmouth,
optimized for specific time intervals and vowel analysis from TextGrid files.

Author: Assistant
Date: 2025
"""

import os
import numpy as np
import pandas as pd
import parselmouth
from typing import Tuple, List, Optional, Dict, Union
import logging
from pathlib import Path
from tqdm import tqdm
from textgrid_io import TextGridReader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedFormantAnalyzer:
    """
    Enhanced Formant Analyzer with optimized time interval processing
    and automated vowel extraction from TextGrid files.
    """
    
    def __init__(self, 
                 wav_dir: str, 
                 annotation_dir: str, 
                 file_list: List[str],
                 allowed_vowels: Optional[List[str]] = None):
        """
        Initialize the Enhanced Formant Analyzer
        
        Args:
            wav_dir: Directory containing WAV files
            annotation_dir: Directory containing TextGrid files
            file_list: List of file names to process
            allowed_vowels: List of allowed vowel phonemes
        """
        self.wav_dir = wav_dir
        self.annotation_dir = annotation_dir
        self.file_list = file_list
        self.allowed_vowels = allowed_vowels or ['a', 'i', 'o', 'u', 'ae']
        self.target_tier = 'phone'
        
        # Formant analysis parameters
        self.default_params = {
            'time_step': 0.00625,
            'max_formants': 5,
            'window_length': 0.025,
            'pre_emphasis_from': 50.0,
            'male_max_formant': 5000,
            'female_max_formant': 5500
        }
        
        self.check_file_validity()
    
    def check_file_validity(self) -> None:
        """Check if corresponding WAV and TextGrid files exist"""
        missing_files = []
        
        for file_name in self.file_list:
            wav_file = os.path.join(self.wav_dir, file_name.replace('.TextGrid', '.wav'))
            textgrid_file = os.path.join(self.annotation_dir, file_name.replace('.wav', '.TextGrid'))
            
            if not os.path.exists(wav_file):
                missing_files.append(f"WAV: {wav_file}")
            if not os.path.exists(textgrid_file):
                missing_files.append(f"TextGrid: {textgrid_file}")
        
        if missing_files:
            raise FileNotFoundError(f"Missing files: {', '.join(missing_files)}")
        
        logger.info(f"All {len(self.file_list)} file pairs are valid")

    def _extract_vowel_intervals(self, textgrid_path: str) -> List[Tuple[float, float, str, str, int]]:
        """
        Extracts vowel intervals from the 'phone' tier of a TextGrid file with word information and interval number.

        Args:
            textgrid_path: Path to the TextGrid file.

        Returns:
            A list of tuples, where each tuple contains (start_time, end_time, vowel_label, word_label, interval_number).
        """
        if not os.path.exists(textgrid_path):
            logger.warning(f"TextGrid file not found: {textgrid_path}")
            return []

        try:
            # TextGridReader를 사용하여 TextGrid 파일 읽기
            reader = TextGridReader(textgrid_path)
            tiers_data = reader.read()
            
            # phone tier와 word tier에서 구간 추출
            phone_intervals = tiers_data.get(self.target_tier, [])
            word_intervals = tiers_data.get('word', [])
            vowel_intervals = []
            
            for start_time, end_time, vowel_label, interval_number in phone_intervals:
                if vowel_label.lower() in [v.lower() for v in self.allowed_vowels]:
                    # 해당 시간 구간에 포함되는 단어 찾기
                    word_label = self._find_word_for_time(start_time, end_time, word_intervals)
                    vowel_intervals.append((start_time, end_time, vowel_label, word_label, interval_number))
            
            logger.info(f"Found {len(vowel_intervals)} vowel intervals in {os.path.basename(textgrid_path)}")
            return vowel_intervals
        except Exception as e:
            logger.error(f"Error reading or processing TextGrid {textgrid_path}: {e}")
            return []
    
    def _find_word_for_time(self, start_time: float, end_time: float, word_intervals: List[Tuple[float, float, str, int]]) -> str:
        """
        Find the word that contains the given time interval.
        
        Args:
            start_time: Start time of the vowel interval
            end_time: End time of the vowel interval
            word_intervals: List of word intervals from TextGrid (start, end, text, interval_number)
            
        Returns:
            Word label that contains the vowel interval
        """
        # 모음 구간의 중간 시간을 기준으로 단어 찾기
        vowel_center = (start_time + end_time) / 2
        
        for word_start, word_end, word_label, _ in word_intervals:  # interval_number는 무시
            if word_start <= vowel_center <= word_end:
                return word_label
        
        # 단어를 찾지 못한 경우 빈 문자열 반환
        return ""

    def analyze_all_vowels_in_file(self, filename: str, gender: str = 'male') -> Dict[str, Dict]:
        """
        Analyzes all vowel intervals found in a file's corresponding TextGrid.

        Args:
            filename: Name of the file (e.g., 'example.wav').
            gender: 'male' or 'female' for formant frequency ceiling.

        Returns:
            A dictionary with unique vowel keys and their analysis results.
        """
        textgrid_filename = filename.replace('.wav', '.TextGrid')
        textgrid_path = os.path.join(self.annotation_dir, textgrid_filename)
        
        vowel_intervals = self._extract_vowel_intervals(textgrid_path)
        
        if not vowel_intervals:
            logger.warning(f"No vowel intervals found for {filename}, skipping analysis.")
            return {}
            
        return self.analyze_vowel_intervals(filename, vowel_intervals, gender)

    def extract_audio_segment(self, 
                            wav_path: str, 
                            start_time: float, 
                            end_time: float,
                            buffer_time: float = 0.0) -> parselmouth.Sound:
        """
        Extract a specific time segment from audio without buffer
        """
        try:
            sound = parselmouth.Sound(wav_path)
            # 버퍼 없이 정확한 시간 구간만 추출
            segment = sound.extract_part(from_time=start_time, to_time=end_time, preserve_times=True)
            logger.debug(f"Extracted segment: {start_time:.3f}s - {end_time:.3f}s")
            return segment
        except Exception as e:
            logger.error(f"Error extracting audio segment: {e}")
            raise
    
    def formant_analysis_optimized(self, 
                                 filename: str, 
                                 interval: Tuple[float, float],
                                 gender: str = 'male',
                                 method: str = 'burg',
                                 analysis_params: Optional[Dict] = None) -> Dict[str, Union[List[float], float, int]]:
        """
        Optimized formant analysis for specific time intervals.
        """
        wav_path = os.path.join(self.wav_dir, filename.replace('.TextGrid', '.wav'))
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"WAV file not found: {wav_path}")
        
        params = self.default_params.copy()
        if analysis_params:
            params.update(analysis_params)
        
        start_time, end_time = interval
        if start_time >= end_time:
            raise ValueError(f"Invalid time interval: start ({start_time}) >= end ({end_time})")
        
        try:
            audio_segment = self.extract_audio_segment(wav_path, start_time, end_time, buffer_time=0.0)
            max_formant = params['female_max_formant'] if gender.lower() == 'female' else params['male_max_formant']
            
            formant = audio_segment.to_formant_burg(
                time_step=params['time_step'],
                max_number_of_formants=params['max_formants'],
                maximum_formant=max_formant,
                window_length=params['window_length'],
                pre_emphasis_from=params['pre_emphasis_from']
            )
            
            time_points = np.arange(start_time, end_time, params['time_step'])
            formant_data = {f'F{i+1}': [] for i in range(params['max_formants'])}
            formant_data['time_points'] = []
            formant_data['valid_points'] = 0
            
            for t in time_points:
                formant_data['time_points'].append(t)
                valid_point = False
                for formant_num in range(1, params['max_formants'] + 1):
                    value = formant.get_value_at_time(formant_num, t)
                    if value is not None and np.isfinite(value) and value > 0:
                        formant_data[f'F{formant_num}'].append(value)
                        valid_point = True
                    else:
                        formant_data[f'F{formant_num}'].append(np.nan)
                if valid_point:
                    formant_data['valid_points'] += 1
            
            formant_data['total_points'] = len(time_points) if time_points.size > 0 else 0
            
            formant_data['statistics'] = {}
            for i in range(1, params['max_formants'] + 1):
                values = np.array(formant_data[f'F{i}'])
                valid_values = values[~np.isnan(values)]
                formant_data['statistics'][f'F{i}'] = {
                    'mean': np.mean(valid_values) if len(valid_values) > 0 else np.nan,
                    'median': np.median(valid_values) if len(valid_values) > 0 else np.nan,
                    'std': np.std(valid_values) if len(valid_values) > 0 else np.nan,
                    'min': np.min(valid_values) if len(valid_values) > 0 else np.nan,
                    'max': np.max(valid_values) if len(valid_values) > 0 else np.nan,
                    'count': len(valid_values)
                }
            
            formant_data['metadata'] = {
                'filename': filename,
                'interval': interval,
                'duration': end_time - start_time,
                'gender': gender,
                'method': method,
                'params': params,
                'success_rate': formant_data['valid_points'] / formant_data['total_points'] if formant_data['total_points'] > 0 else 0
            }
            
            logger.debug(f"Analysis of {filename} ({interval[0]:.3f}-{interval[1]:.3f}s) completed. "
                        f"Success rate: {formant_data['metadata']['success_rate']:.2%}")
            
            return formant_data
            
        except Exception as e:
            logger.error(f"Error in formant analysis for {filename} at interval {interval}: {e}")
            raise
    
    def analyze_vowel_intervals(self, 
                              filename: str, 
                              vowel_intervals: List[Tuple[float, float, str, str, int]],
                              gender: str = 'male') -> Dict[str, Dict]:
        """
        Analyze multiple vowel intervals from a single file.
        """
        results = {}
        for start_time, end_time, vowel_label, word_label, interval_number in vowel_intervals:
            try:
                analysis = self.formant_analysis_optimized(filename, (start_time, end_time), gender)
                analysis['vowel_label'] = vowel_label
                analysis['word_label'] = word_label
                analysis['interval_number'] = interval_number
                # Create a unique key for each interval
                results[f"{vowel_label}_{start_time:.4f}"] = analysis
                logger.info(f"Analyzed vowel '{vowel_label}' in word '{word_label}' (interval {interval_number}) at {start_time:.3f}-{end_time:.3f}s")
            except Exception as e:
                logger.warning(f"Failed to analyze vowel '{vowel_label}' in word '{word_label}' (interval {interval_number}) at {start_time:.3f}-{end_time:.3f}s: {e}")
        return results
    
    def batch_analyze_all_vowels(self, gender: str = 'male') -> Dict[str, Dict]:
        """
        Batch analyzes all vowels for all files in the file_list.

        Args:
            gender: 'male' or 'female' for formant frequency ceiling.

        Returns:
            A dictionary with filenames as keys and their vowel analysis results as values.
        """
        all_results = {}
        for filename in self.file_list:
            logger.info(f"Processing file: {filename}")
            file_results = self.analyze_all_vowels_in_file(filename, gender)
            if file_results:
                all_results[filename] = file_results
        return all_results

    def save_results_to_xlsx(self, 
                           results: Dict, 
                           output_path: str) -> None:
        """
        Save analysis results to an xlsx file.
        """
        rows = []
        
        for filename, file_results in results.items():
            # Extract participant ID from filename
            participant_id = self._extract_participant_id_from_filename(filename)
            
            for interval_key, result in file_results.items():
                if isinstance(result, dict) and 'statistics' in result:
                    self._extract_result_row(result, rows, interval_key, participant_id)
        
        if rows:
            df = pd.DataFrame(rows)
            # Reorder columns for clarity
            cols = ['participant_id', 'file_id', 'word_label', 'vowel_label', 'interval_number', 'start_time', 'end_time', 'duration', 'gender', 'success_rate']
            stats_cols = [f'F{i}_{stat}' for i in range(1, 6) for stat in ['mean', 'median', 'std', 'min', 'max', 'count']]
            ordered_cols = cols + [c for c in stats_cols if c in df.columns]
            remaining_cols = [c for c in df.columns if c not in ordered_cols]
            df = df[ordered_cols + remaining_cols]

            df.to_excel(output_path, index=False, engine='openpyxl')
            logger.info(f"Results for {len(rows)} vowels saved to {output_path}")
        else:
            logger.warning("No valid results to save")
    
    def _extract_result_row(self, result: Dict, rows: List, interval_key: str, participant_id: str = '') -> None:
        """Helper method to extract data from a single result dictionary"""
        row = {}
        metadata = result.get('metadata', {})
        
        row.update({
            'participant_id': participant_id,
            'file_id': metadata.get('filename', ''),
            'interval_key': interval_key,
            'start_time': metadata.get('interval', [0, 0])[0],
            'end_time': metadata.get('interval', [0, 0])[1],
            'duration': metadata.get('duration', 0),
            'gender': metadata.get('gender', ''),
            'success_rate': metadata.get('success_rate', 0)
        })
        
        if 'vowel_label' in result:
            row['vowel_label'] = result['vowel_label']
        
        if 'word_label' in result:
            row['word_label'] = result['word_label']
        
        if 'interval_number' in result:
            row['interval_number'] = result['interval_number']
        
        if 'statistics' in result:
            for formant, stats in result['statistics'].items():
                if isinstance(stats, dict):
                    for stat_name, value in stats.items():
                        row[f"{formant}_{stat_name}"] = value
        
        rows.append(row)
    
    def _extract_participant_id_from_filename(self, filename: str) -> str:
        """
        Extract participant ID from filename and format it as three-digit number.
        
        Args:
            filename: Full path to the WAV file (e.g., 'participant_LY044/LY044_stage4_20250509_1516.wav')
            
        Returns:
            Formatted participant ID as three-digit string (e.g., '044')
        """
        try:
            # Extract participant directory name from filename
            # filename format: 'participant_LY044/LY044_stage4_20250509_1516.wav'
            participant_dir = filename.split('/')[0]  # 'participant_LY044'
            
            # Extract LY number from participant directory
            if 'participant_LY' in participant_dir:
                ly_number = participant_dir.replace('participant_LY', '')
            elif 'participant_' in participant_dir:
                # Handle cases like 'participant_002' or 'participant_02'
                number_part = participant_dir.replace('participant_', '')
                # Remove any non-digit characters and get the number
                ly_number = ''.join(filter(str.isdigit, number_part))
            else:
                return '000'
            
            # Convert to three-digit format
            if ly_number.isdigit():
                return ly_number.zfill(3)  # '6' -> '006', '44' -> '044'
            else:
                return '000'
                
        except Exception as e:
            logger.warning(f"Could not extract participant ID from filename '{filename}': {e}")
            return '000'


def demo_usage():
    """
    Demonstration of the enhanced formant analyzer usage.
    This demo now automatically finds and analyzes all vowels in the specified files.
    """
    print("Enhanced Formant Analyzer Demo")
    print("=" * 40)
    
    # --- Configuration ---
    # Adjust these paths to your actual data directories
    proj_dir = Path.home() / "Documents" / "WorkSpace" / "phoneticConvergence"
    wav_dir = os.path.join(proj_dir,"data/experiment_data/results-KFA-reviewed")
    annotation_dir = os.path.join(proj_dir,"data/experiment_data/model_talker/KFA_annotation_edited")
    
    # Load gender information from survey
    survey_path = os.path.join(proj_dir, "data/experiment_data/survey-latest.xlsx")
    gender_info = {}
    
    try:
        import pandas as pd
        survey_df = pd.read_excel(survey_path)
        for _, row in survey_df.iterrows():
            participant = row['1. 참가자 번호']
            gender = row['Gender']
            if pd.notna(participant) and pd.notna(gender):
                gender_info[participant] = gender
        print(f"Loaded gender information for {len(gender_info)} participants")
    except Exception as e:
        print(f"Warning: Could not load gender information: {e}")
        gender_info = {}
    
    # Collect all WAV files from participant directories
    all_wav_files = []
    participant_gender_map = {}
    
    print("Collecting WAV files from participant directories...")
    participant_dirs = [d for d in os.listdir(wav_dir) if os.path.isdir(os.path.join(wav_dir, d)) and d.startswith('participant_')]
    
    for participant_dir in tqdm(participant_dirs, desc="Scanning participants"):
        participant_path = os.path.join(wav_dir, participant_dir)
        participant_id = participant_dir.replace('participant_', '')
        
        # Get gender for this participant
        gender = gender_info.get(participant_id, 'male')  # default to male if not found
        participant_gender_map[participant_id] = gender
        
        # Find WAV files in this participant's directory
        wav_files = [f for f in os.listdir(participant_path) if f.endswith('.wav')]
        for wav_file in wav_files:
            full_path = os.path.join(participant_dir, wav_file)
            all_wav_files.append((full_path, participant_id, gender, participant_path))
    
    print(f"Found {len(all_wav_files)} WAV files from {len(participant_gender_map)} participants")
    print(f"Participants: {list(participant_gender_map.keys())[:10]}{'...' if len(participant_gender_map) > 10 else ''}")
    
    # --- End Configuration ---

    if not os.path.exists(wav_dir):
        logger.error("Demo directory not found. Please adjust 'wav_dir' in demo_usage().")
        return

    try:
        all_results = {}
        
        # Process each WAV file with its corresponding gender
        print(f"\nStarting analysis of {len(all_wav_files)} WAV files...")
        for wav_file, participant_id, gender, participant_path in tqdm(all_wav_files, desc="Analyzing WAV files"):
            # Create analyzer instance for this file with participant-specific paths
            analyzer = EnhancedFormantAnalyzer(
                wav_dir=participant_path,
                annotation_dir=participant_path,
                file_list=[os.path.basename(wav_file)]
            )
            
            # Analyze vowels for this file
            file_results = analyzer.analyze_all_vowels_in_file(os.path.basename(wav_file), gender=gender)
            if file_results:
                all_results[wav_file] = file_results
        
        # Print a summary of the results
        print("\n--- Analysis Summary ---")
        total_vowels = 0
        for filename, results in tqdm(all_results.items(), desc="Generating summary"):
            vowel_count = len(results)
            total_vowels += vowel_count
            participant_id = next((pid for _, pid, _, __ in all_wav_files if filename in _), 'Unknown')
            gender = next((g for _, pid, g, __ in all_wav_files if filename in _ and pid == participant_id), 'Unknown')
            print(f"File: {filename} (Participant: {participant_id}, Gender: {gender}) - Found and analyzed {vowel_count} vowels.")

        print(f"\nTotal vowels analyzed: {total_vowels}")

        # Save the detailed results to an Excel file
        if all_results:
            output_excel_path = "formant_results_all_vowels.xlsx"
            print(f"\nSaving detailed results to {output_excel_path}...")
            
            # Create a temporary analyzer for saving
            temp_analyzer = EnhancedFormantAnalyzer(
                wav_dir=wav_dir,
                annotation_dir=annotation_dir,
                file_list=[]
            )
            temp_analyzer.save_results_to_xlsx(all_results, output_excel_path)
        else:
            print("\nNo results to save.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        print("Please ensure that the directories in the demo are correct.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    demo_usage()
