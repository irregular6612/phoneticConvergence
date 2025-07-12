"""
설정 관리 모듈

이 패키지는 실험 프로그램의 설정을 관리합니다.
- ConfigManager: 설정 파일 로드/저장
- ConfigWindow: 설정 UI 창
"""

# 주요 클래스들을 쉽게 import할 수 있도록
try:
    from .config_manager import ConfigManager, ConfigWindow
except ImportError:
    print("ImportError: config_manager.py is not found")

# 외부에서 import할 수 있는 것들 정의
__all__ = [
    'ConfigManager',
    'ConfigWindow'
]