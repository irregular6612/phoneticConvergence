# TextGrid I/O 통합 모듈 사용 가이드

이 모듈은 TextGrid 파일을 읽고, 수정하고, 저장할 수 있는 통합 기능을 제공합니다.

## 주요 기능

1. **TextGridReader 클래스**: TextGrid 파일을 읽고, 수정하고, 저장할 수 있는 통합 클래스
2. **parse_textgrid()**: TextGrid 파일을 파싱하여 구조화된 데이터로 변환
3. **find_interval()**: 특정 tier_name과 text로 해당 interval을 찾기
4. **find_intervals_by_text()**: 특정 tier_name과 text로 해당하는 모든 interval을 찾기
5. **modify_interval_boundaries()**: 특정 interval의 xmin, xmax 값을 수정 (overwrite 방식)
6. **boundary_fix()**: 전체 boundary를 수정하는 함수
7. **validate_boundaries()**: TextGrid 데이터의 boundary 무결성을 검사

## 기본 사용법

### 1. TextGridReader 클래스 사용 (권장)

```python
from textgrid_io import TextGridReader

# TextGrid 파일 로드
reader = TextGridReader("path/to/file.TextGrid")
print(f"총 {len(reader.get_tier_names())}개 tier")

# 특정 interval 찾기
interval = reader.find_interval("phone", "a")
if interval:
    print(f"찾은 interval: xmin={interval.xmin}, xmax={interval.xmax}")

# interval 수정
reader.modify_interval_boundaries("phone", "a", new_xmin=1.5, new_xmax=2.0)

# 파일 저장
reader.write("modified_file.TextGrid")
```

### 2. 함수 기반 사용법 (기존 호환성)

```python
from textgrid_io import parse_textgrid, find_interval, modify_interval_boundaries

# TextGrid 파일 파싱
textgrid_data = parse_textgrid("path/to/file.TextGrid")

# 특정 interval 찾기
interval = find_interval(textgrid_data, "phone", "a")

# interval 수정
modify_interval_boundaries(textgrid_data, "phone", "a", new_xmin=1.5, new_xmax=2.0)
```

## 클래스 기반 사용법 (권장)

### TextGridReader 클래스

```python
from textgrid_io import TextGridReader

# 초기화 (자동으로 파일 읽기)
reader = TextGridReader("file.TextGrid")

# 또는 나중에 파일 읽기
reader = TextGridReader("file.TextGrid")
reader.read()
```

### 주요 메서드

#### 1. 파일 읽기/쓰기
```python
# 파일 읽기
textgrid_data = reader.read()

# 파일 저장
reader.write("output.TextGrid")  # 새 파일로 저장
reader.write()  # 원본 파일에 저장
```

#### 2. Interval 찾기
```python
# 단일 interval 찾기
interval = reader.find_interval("phone", "a")

# 여러 interval 찾기
intervals = reader.find_intervals_by_text("phone", "sp")
```

#### 3. Interval 수정
```python
# xmin, xmax 값 수정
success = reader.modify_interval_boundaries(
    "phone", "a", 
    new_xmin=1.5, 
    new_xmax=2.0,
    interval_number=6  # 특정 interval 번호 (선택사항)
)
```

#### 4. Boundary 무결성 검사 및 수정
```python
# 무결성 검사
issues = reader.validate_boundaries()
if issues:
    print("발견된 boundary 문제:", issues)

# 자동 수정
success = reader.boundary_fix(
    output_path="fixed.TextGrid",  # 선택사항
    backup=True,  # 백업 파일 생성
    inplace=False  # 원본 파일에 덮어쓰기 여부
)
```

#### 5. 정보 조회
```python
# tier 이름 목록
tier_names = reader.get_tier_names()

# 특정 tier의 interval 목록
intervals = reader.get_intervals_by_tier("phone")

# 전체 지속 시간
duration = reader.get_total_duration()
```

## 데이터 구조

### Interval 클래스
```python
@dataclass
class Interval:
    xmin: float          # 시작 시간
    xmax: float          # 끝 시간
    text: str            # 텍스트 라벨
    interval_number: int # interval 번호
```

### Tier 클래스
```python
@dataclass
class Tier:
    name: str                    # tier 이름
    xmin: float                  # tier 시작 시간
    xmax: float                  # tier 끝 시간
    intervals: List[Interval]    # interval 리스트
```

### TextGridData 클래스
```python
@dataclass
class TextGridData:
    xmin: float                      # 전체 시작 시간
    xmax: float                      # 전체 끝 시간
    tiers: Dict[str, Tier]           # tier 딕셔너리
```

## 명령행 도구 사용법

### Boundary Checker

```bash
# 단일 파일 검사
python textgrid_boundary_checker.py file.TextGrid

# 디렉토리 내 모든 파일 검사
python textgrid_boundary_checker.py /path/to/directory

# 문제 발견시 자동 수정
python textgrid_boundary_checker.py file.TextGrid --fix

# 원본 파일에 덮어쓰기 (백업 생성)
python textgrid_boundary_checker.py file.TextGrid --fix --inplace

# 백업 파일 생성하지 않음
python textgrid_boundary_checker.py file.TextGrid --fix --no-backup
```

## 자동 업데이트 기능

### 1. 파일 전체 xmin, xmax 자동 업데이트
- interval 수정 시 모든 tier의 최소/최대값을 고려하여 파일 전체 범위 자동 계산
- 저장 시 정확한 범위 반영

### 2. Tier별 xmin, xmax 자동 업데이트
- 각 tier의 첫 번째 interval의 xmin과 마지막 interval의 xmax로 tier 범위 자동 계산
- interval 수정 시 해당 tier의 범위도 자동으로 업데이트

### 3. Boundary 수정 시 자동 업데이트
- boundary 수정 후 전체 파일과 tier 범위 자동 업데이트
- 상세한 로그로 변경 사항 추적

## 주의사항

1. **백업**: 중요한 파일을 수정하기 전에 항상 백업을 생성하세요.
2. **Interval 번호**: 같은 텍스트가 여러 개 있을 경우 `interval_number`를 지정하여 정확한 interval을 수정하세요.
3. **Boundary 무결성**: 수정 후에는 `validate_boundaries()`를 사용하여 무결성을 확인하세요.
4. **파일 형식**: TextGrid 파일은 Praat의 long format을 지원합니다.
5. **클래스 사용 권장**: `TextGridReader` 클래스를 사용하는 것이 더 안전하고 효율적입니다.

## 예제 스크립트

### 기본 사용 예제
```bash
python textgrid_io_example.py
```

### 기존 호환성 예제
```bash
python textgrid_modifier_example.py
```

## 로깅

모든 함수는 상세한 로그를 출력합니다. 로그 레벨을 조정하려면:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)  # 상세한 로그
logging.getLogger().setLevel(logging.WARNING)  # 경고만 출력
```

## 마이그레이션 가이드

### 기존 코드에서 새로운 클래스로 전환

**기존 코드:**
```python
from textgrid_modifier import parse_textgrid, modify_interval_boundaries

textgrid_data = parse_textgrid("file.TextGrid")
modify_interval_boundaries(textgrid_data, "phone", "a", new_xmin=1.5)
```

**새로운 코드:**
```python
from textgrid_io import TextGridReader

reader = TextGridReader("file.TextGrid")
reader.modify_interval_boundaries("phone", "a", new_xmin=1.5)
reader.write("modified_file.TextGrid")
```

### 장점
- 더 안전한 파일 처리
- 자동 백업 및 복원
- 상세한 로깅
- 자동 범위 업데이트
- 더 직관적인 API
