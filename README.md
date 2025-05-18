# 음성 수렴 실험 프로젝트

이 프로젝트는 음성 수렴(Phonetic Convergence) 현상을 연구하기 위한 실험 및 분석 도구를 제공합니다. 음성 데이터 수집, 포먼트 분석, 시각화 등의 기능을 포함합니다.

## 프로젝트 구조

### 1. 실험 데이터
- `experiment_data/`: 실험 데이터 저장
- `audio_samples/`: 오디오 샘플 파일
- `main_words.xlsx/`: 주요 단어 목록
- `practice_words.xlsx/`: 연습 단어 목록

### 2. 분석 도구
- `analysis/`: 데이터 분석 스크립트
- `control.py`: 실험 제어 스크립트
- `formant_analysis.log`: 포먼트 분석 로그

### 3. 시각화
- `sample-stage2:3.png`: 단계별 분석 결과
- `formant_control.png`: 포먼트 제어 결과
- `sample.png`: 샘플 시각화

### 4. 설정
- `config.json`: 실험 설정 파일
- `requirements.txt`: 필요한 패키지 목록

## 필요 조건

- Python 3.8 이상
- librosa
- numpy
- pandas
- matplotlib
- scipy

## 설치 방법

1. 저장소를 클론합니다:
```bash
git clone [repository-url]
```

2. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

## 사용 방법

### 실험 제어
```bash
python control.py
```

### 데이터 분석
```bash
cd analysis
python analyze.py
```

## 주요 기능

1. **음성 데이터 수집**
   - 오디오 녹음
   - 데이터 전처리
   - 품질 검사

2. **포먼트 분석**
   - 포먼트 추출
   - 시계열 분석
   - 통계 처리

3. **시각화**
   - 포먼트 트래젝토리
   - 스펙트로그램
   - 비교 분석

4. **데이터 관리**
   - 실험 데이터 저장
   - 메타데이터 관리
   - 결과 추출

## 실험 프로토콜

1. **준비 단계**
   - 단어 목록 준비
   - 녹음 환경 설정
   - 참가자 안내

2. **수집 단계**
   - 연습 녹음
   - 본 실험 녹음
   - 품질 검사

3. **분석 단계**
   - 포먼트 추출
   - 데이터 정규화
   - 통계 분석

4. **평가 단계**
   - 결과 시각화
   - 통계 검정
   - 보고서 작성

## 데이터 형식

### 오디오 파일
- 형식: WAV
- 샘플링 레이트: 44.1kHz
- 비트 깊이: 16bit

### 메타데이터
```json
{
    "participant_id": "P001",
    "session": "practice",
    "word": "example",
    "timestamp": "2024-03-29T10:00:00",
    "quality_check": "passed"
}
```

## 참고 자료

- [librosa 문서](https://librosa.org/doc/latest/index.html)
- [음성학 연구 방법론](https://www.linguisticsociety.org/resource/phonetics)
- [포먼트 분석 가이드](https://www.phon.ucl.ac.uk/courses/spsci/acoustics/) 