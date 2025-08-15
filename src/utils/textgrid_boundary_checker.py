"""
TextGrid Boundary Checker (개선된 버전)

새로운 textgrid_modifier 모듈을 사용하여 boundary 문제를 검사하고 수정합니다.

Author: Juhyeon Park
Date: 2025-01-08
"""

import os
import argparse
import logging
from typing import List, Dict, Tuple
from pathlib import Path

# 새로운 textgrid_io 모듈 import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'analysis'))
from textgrid_io import (
    parse_textgrid,
    validate_boundaries,
    boundary_fix,
    TextGridData
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_single_file(file_path: str, fix: bool = False, backup: bool = True, 
                     inplace: bool = False) -> Dict:
    """
    단일 TextGrid 파일의 boundary를 검사하고 필요시 수정합니다.
    
    Args:
        file_path (str): 검사할 TextGrid 파일 경로
        fix (bool): 문제 발견시 자동 수정 여부
        backup (bool): 백업 파일 생성 여부
        inplace (bool): 원본 파일에 덮어쓰기 여부
        
    Returns:
        Dict: 검사 결과 정보
    """
    result = {
        'file_path': file_path,
        'status': 'unknown',
        'issues': {},
        'total_issues': 0,
        'fixed': False
    }
    
    try:
        # 파일 파싱
        textgrid_data = parse_textgrid(file_path)
        
        # Boundary 무결성 검사
        issues = validate_boundaries(textgrid_data)
        
        result['issues'] = issues
        result['total_issues'] = sum(len(issues_list) for issues_list in issues.values())
        
        if result['total_issues'] == 0:
            result['status'] = 'clean'
            logger.info(f"✅ {file_path}: 모든 boundary가 정상입니다.")
        else:
            result['status'] = 'has_issues'
            logger.warning(f"⚠️  {file_path}: {result['total_issues']}개의 boundary 문제 발견")
            
            # 문제 상세 출력
            for tier_name, tier_issues in issues.items():
                logger.warning(f"  Tier '{tier_name}': {len(tier_issues)}개 문제")
                for interval_num, xmax, next_xmin in tier_issues[:3]:  # 처음 3개만
                    logger.warning(f"    interval {interval_num}: {xmax:.3f} vs {next_xmin:.3f}")
            
            # 자동 수정 요청시
            if fix:
                logger.info(f"🔄 {file_path}: Boundary 수정 시작...")
                success = boundary_fix(file_path, backup=backup, inplace=inplace)
                
                if success:
                    result['fixed'] = True
                    result['status'] = 'fixed'
                    logger.info(f"✅ {file_path}: Boundary 수정 완료")
                    
                    # 수정 후 재검사
                    fixed_data = parse_textgrid(file_path if inplace else 
                                              file_path.replace('.TextGrid', '_fixed.TextGrid'))
                    fixed_issues = validate_boundaries(fixed_data)
                    remaining_issues = sum(len(issues_list) for issues_list in fixed_issues.values())
                    
                    if remaining_issues == 0:
                        logger.info(f"✅ {file_path}: 수정 후 모든 boundary가 정상입니다.")
                    else:
                        logger.warning(f"⚠️  {file_path}: 수정 후에도 {remaining_issues}개 문제가 남아있습니다.")
                        result['remaining_issues'] = remaining_issues
                else:
                    result['status'] = 'fix_failed'
                    logger.error(f"❌ {file_path}: Boundary 수정 실패")
    
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        logger.error(f"❌ {file_path}: 처리 중 오류 발생 - {e}")
    
    return result

def check_directory(directory_path: str, fix: bool = False, backup: bool = True, 
                   inplace: bool = False) -> List[Dict]:
    """
    디렉토리 내의 모든 TextGrid 파일을 검사합니다.
    
    Args:
        directory_path (str): 검사할 디렉토리 경로
        fix (bool): 문제 발견시 자동 수정 여부
        backup (bool): 백업 파일 생성 여부
        inplace (bool): 원본 파일에 덮어쓰기 여부
        
    Returns:
        List[Dict]: 각 파일별 검사 결과
    """
    results = []
    directory = Path(directory_path)
    
    if not directory.exists():
        logger.error(f"디렉토리를 찾을 수 없습니다: {directory_path}")
        return results
    
    # TextGrid 파일 찾기
    textgrid_files = list(directory.rglob("*.TextGrid")) + list(directory.rglob("*.textgrid"))
    
    if not textgrid_files:
        logger.warning(f"디렉토리에서 TextGrid 파일을 찾을 수 없습니다: {directory_path}")
        return results
    
    logger.info(f"총 {len(textgrid_files)}개의 TextGrid 파일 발견")
    
    # 각 파일 검사
    for file_path in textgrid_files:
        result = check_single_file(str(file_path), fix=fix, backup=backup, inplace=inplace)
        results.append(result)
    
    return results

def print_summary(results: List[Dict]):
    """
    검사 결과 요약을 출력합니다.
    
    Args:
        results (List[Dict]): 검사 결과 리스트
    """
    if not results:
        return
    
    total_files = len(results)
    clean_files = sum(1 for r in results if r['status'] == 'clean')
    issue_files = sum(1 for r in results if r['status'] == 'has_issues')
    fixed_files = sum(1 for r in results if r['status'] == 'fixed')
    error_files = sum(1 for r in results if r['status'] == 'error')
    fix_failed_files = sum(1 for r in results if r['status'] == 'fix_failed')
    
    total_issues = sum(r['total_issues'] for r in results if 'total_issues' in r)
    
    print("\n" + "="*60)
    print("📊 검사 결과 요약")
    print("="*60)
    print(f"총 파일 수: {total_files}")
    print(f"정상 파일: {clean_files}")
    print(f"문제 파일: {issue_files}")
    print(f"수정 완료: {fixed_files}")
    print(f"수정 실패: {fix_failed_files}")
    print(f"오류 파일: {error_files}")
    print(f"총 문제 수: {total_issues}")
    
    if issue_files > 0:
        print(f"\n⚠️  문제가 있는 파일들:")
        for result in results:
            if result['status'] == 'has_issues':
                print(f"  - {result['file_path']}: {result['total_issues']}개 문제")
    
    if error_files > 0:
        print(f"\n❌ 오류가 발생한 파일들:")
        for result in results:
            if result['status'] == 'error':
                print(f"  - {result['file_path']}: {result.get('error', 'Unknown error')}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="TextGrid 파일의 boundary 무결성을 검사하고 수정합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  # 단일 파일 검사
  python textgrid_boundary_checker.py file.TextGrid
  
  # 디렉토리 내 모든 파일 검사
  python textgrid_boundary_checker.py /path/to/directory
  
  # 문제 발견시 자동 수정
  python textgrid_boundary_checker.py file.TextGrid --fix
  
  # 원본 파일에 덮어쓰기 (백업 생성)
  python textgrid_boundary_checker.py file.TextGrid --fix --inplace
        """
    )
    
    parser.add_argument("target", help="검사할 TextGrid 파일 또는 디렉토리 경로")
    parser.add_argument("--fix", action="store_true", 
                       help="문제 발견시 자동으로 수정")
    parser.add_argument("--no-backup", action="store_true", 
                       help="백업 파일 생성하지 않음")
    parser.add_argument("--inplace", action="store_true", 
                       help="원본 파일에 덮어쓰기 (기본값: 새 파일 생성)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="상세한 로그 출력")
    
    args = parser.parse_args()
    
    # 로그 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    target_path = args.target
    
    if not os.path.exists(target_path):
        logger.error(f"대상을 찾을 수 없습니다: {target_path}")
        return 1
    
    try:
        if os.path.isfile(target_path):
            # 단일 파일 처리
            result = check_single_file(
                target_path, 
                fix=args.fix, 
                backup=not args.no_backup, 
                inplace=args.inplace
            )
            print_summary([result])
        else:
            # 디렉토리 처리
            results = check_directory(
                target_path, 
                fix=args.fix, 
                backup=not args.no_backup, 
                inplace=args.inplace
            )
            print_summary(results)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
        return 1
    except Exception as e:
        logger.error(f"예상치 못한 오류가 발생했습니다: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
