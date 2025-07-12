import os
from datetime import datetime

def calculate_time_difference(file1, file2):
    """
    두 파일의 시간 차이를 계산합니다.
    
    Args:
        file1 (str): 첫 번째 파일명
        file2 (str): 두 번째 파일명
    
    Returns:
        timedelta: 시간 차이
    """
    # 파일명에서 시간 정보 추출
    time1 = file1.split('_')[-1].replace('.wav', '')
    time2 = file2.split('_')[-1].replace('.wav', '')
    
    # datetime 객체로 변환
    dt1 = datetime.strptime(time1, '%Y%m%d%H%M')
    dt2 = datetime.strptime(time2, '%Y%m%d%H%M')
    
    # 시간 차이 계산
    time_diff = abs(dt2 - dt1)
    
    return time_diff

def analyze_time_differences(directory_path):
    """
    모든 파일 간의 시간 차이를 분석합니다.
    
    Args:
        directory_path (str): 파일이 있는 디렉토리 경로
    """
    # 모든 WAV 파일 목록 가져오기
    wav_files = [f for f in os.listdir(directory_path) if f.endswith('.wav')]
    wav_files.sort()  # 파일명 기준 정렬
    
    # 시간 차이 분석
    time_diffs = []
    for i in range(len(wav_files)-1):
        file1 = wav_files[i]
        file2 = wav_files[i+1]
        
        # 같은 참가자의 파일인지 확인
        if file1.split('_')[0] == file2.split('_')[0]:
            time_diff = calculate_time_difference(file1, file2)
            time_diffs.append({
                'file1': file1,
                'file2': file2,
                'time_diff': time_diff
            })
    
    # 결과 출력
    print("\n시간 차이 분석 결과:")
    for diff in time_diffs:
        print(f"\n{diff['file1']} -> {diff['file2']}")
        print(f"시간 차이: {diff['time_diff']}")
    
    return time_diffs

def calculate_datetime_difference(time1_str, time2_str):
    """
    datetime 형식의 시간 문자열 간 차이를 계산합니다.
    
    Args:
        time1_str (str): 첫 번째 시간 문자열 (예: "2025-04-02 18:59:55.660093")
        time2_str (str): 두 번째 시간 문자열 (예: "2025-04-02 18:59:58.231983")
    
    Returns:
        timedelta: 시간 차이
    """
    # datetime 객체로 변환
    dt1 = datetime.strptime(time1_str, '%Y-%m-%d %H:%M:%S.%f')
    dt2 = datetime.strptime(time2_str, '%Y-%m-%d %H:%M:%S.%f')
    
    # 시간 차이 계산
    time_diff = abs(dt2 - dt1)
    
    return time_diff

def analyze_datetime_differences(times):
    """
    여러 시간 정보 간의 차이를 분석합니다.
    
    Args:
        times (list): 시간 문자열 리스트
    """
    time_diffs = []
    for i in range(len(times)-1):
        time1 = times[i]
        time2 = times[i+1]
        
        time_diff = calculate_datetime_difference(time1, time2)
        time_diffs.append({
            'time1': time1,
            'time2': time2,
            'time_diff': time_diff
        })
    
    # 결과 출력
    print("\n시간 차이 분석 결과:")
    for diff in time_diffs:
        print(f"\n{diff['time1']} -> {diff['time2']}")
        print(f"시간 차이: {diff['time_diff']}")
    
    return time_diffs

def main():
    # 파일 경로 설정
    directory_path = "../../../../Desktop/results"
    
    # 시간 차이 분석 실행
    time_diffs = analyze_time_differences(directory_path)

    # 예시 시간 데이터
    times = [
        "2025-04-02 18:59:55.660093",
        "2025-04-02 18:59:58.231983",
        "2025-04-02 19:00:00.068018",
        "2025-04-02 19:00:01.696563"
    ]
    
    # 시간 차이 분석 실행
    time_diffs_datetime = analyze_datetime_differences(times)

if __name__ == "__main__":
    main() 