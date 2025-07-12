from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

def setup_driver():
    """크롬 드라이버 설정"""
    options = webdriver.ChromeOptions()
    # 다운로드 경로 설정
    download_path = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_path, exist_ok=True)
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False
    }
    options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def upload_file(driver, url, file_path):
    """파일 업로드 및 다운로드 자동화"""
    try:
        # 웹사이트 접속
        driver.get(url)
        
        # 파일 업로드 버튼 찾기 및 클릭
        upload_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        upload_button.send_keys(file_path)
        
        # 처리 완료 대기
        time.sleep(5)
        
        # 다운로드 버튼 클릭
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.download-button"))
        )
        download_button.click()
        
        # 다운로드 완료 대기
        time.sleep(5)
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # 사용 예시
    url = "https://example.com/upload"  # 실제 웹사이트 URL로 변경 필요
    file_path = "path/to/your/file.txt"  # 실제 파일 경로로 변경 필요
    
    driver = setup_driver()
    upload_file(driver, url, file_path) 