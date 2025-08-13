import time
import os
import logging
import traceback
import glob
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from PIL import Image

from seleniumbot import SeleniumBot

class OliveYoungCrawler(SeleniumBot):
    """올리브영 모바일 페이지 크롤러"""
    
    # URL 상수
    RANKING_URL = "https://m.oliveyoung.co.kr/m/mtn?menu=ranking&t_page=home&t_click=GNB&t_gnb_type=ranking&t_swiping_type=N&tab=sales&period=REALTIME"
    BODYCARE_URL = "https://m.oliveyoung.co.kr/m/mtn?oy=0&menu=ranking&t_page=home&t_click=GNB&t_gnb_type=ranking&t_swiping_type=N&tab=sales&category=10000010003&period=REALTIME"
    
    # 모바일 디바이스 설정
    MOBILE_WIDTH = 375
    MOBILE_HEIGHT = 812
    PIXEL_RATIO = 3.0
    
    def __init__(self, username: str = 'ilsun', headless: bool = False, platform: str = 'nas'):
        """크롤러 초기화
        
        Args:
            username: 사용자명
            headless: 헤드리스 모드 사용 여부 (테스트용으로 False 설정)
            platform: 플랫폼 타입
        """
        super().__init__(username=username, headless=headless, platform=platform)
        
        self.logger = self._setup_logger()
        self.driver = self._setup_driver(headless)
        self.date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._setup_directories()
    
    def _setup_driver(self, headless: bool) -> webdriver.Chrome:
        """Chrome 드라이버 설정"""
        chrome_options = self._get_chrome_options(headless)
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(self.MOBILE_WIDTH, self.MOBILE_HEIGHT)
        return driver
    
    def _get_chrome_options(self, headless: bool) -> Options:
        """Chrome 옵션 설정"""
        options = Options()
        
        # 헤드리스 모드 설정 (테스트 시 False)
        if headless:
            options.add_argument('--headless')
        
        # 기본 옵션
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 모바일 에뮬레이션
        mobile_emulation = {
            "deviceMetrics": {
                "width": self.MOBILE_WIDTH,
                "height": self.MOBILE_HEIGHT,
                "pixelRatio": self.PIXEL_RATIO,
                "touch": True,
                "mobile": True
            },
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        return options
        
    def _setup_logger(self) -> logging.Logger:
        """로깅 설정"""
        # 로그 디렉토리 생성
        log_dir = os.path.join(os.getcwd(), "Data", "oliveyoung", "mobile", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # 로거 생성
        logger = logging.getLogger("OliveYoungCrawler")
        logger.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 파일 핸들러
        log_file = os.path.join(
            log_dir, 
            f"oliveyoung_mobile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _setup_directories(self) -> None:
        """작업 디렉토리 설정"""
        # 기본 데이터 디렉토리
        self.data_dir = os.path.join(os.getcwd(), "Data", "oliveyoung", "mobile")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 이미지 디렉토리
        self.image_dir = os.path.join(self.data_dir, "images")
        os.makedirs(self.image_dir, exist_ok=True)
        
        # 임시 이미지 디렉토리
        self.temp_image_dir = os.path.join(self.image_dir, "temp", self.date_str)
        os.makedirs(self.temp_image_dir, exist_ok=True)
    
    def _scroll_and_capture(self, page_type: str = "ranking", max_scrolls: int = 50) -> bool:
        """페이지를 스크롤하며 스크린샷 캡처
        
        Args:
            page_type: 페이지 타입 (ranking, bodycare)
            max_scrolls: 최대 스크롤 횟수
            
        Returns:
            성공 여부
        """
        self.logger.info(f"{page_type} 페이지 스크롤 시작...")
        
        try:
            # 컨테이너 확인
            if not self._check_container_exists():
                self.logger.error(f"{page_type} 컨테이너를 찾을 수 없습니다.")
                return False
            
            # 컨테이너 정보 가져오기
            container_info = self._get_container_info()
            self.logger.info(
                f"컨테이너 초기 정보 - 높이: {container_info['scrollHeight']}px, "
                f"클라이언트 높이: {container_info['clientHeight']}px"
            )
            
            # 초기 스크린샷
            self._save_screenshot(page_type, 0)
            
            # 스크롤 반복
            scroll_count = 0
            last_scroll_top = -1
            
            while scroll_count < max_scrolls:
                # 스크롤 실행
                scroll_result = self._perform_scroll()
                scroll_count += 1
                
                # 로깅
                self._log_scroll_info(scroll_count, scroll_result)
                
                # 스크린샷 저장
                self._save_screenshot(page_type, scroll_count)
                
                # 로딩 대기
                time.sleep(1.5)
                
                # 스크롤 끝 확인
                if scroll_result['after_scroll'] == last_scroll_top:
                    self.logger.info(f"스크롤 끝 도달 (총 {scroll_count}회)")
                    break
                    
                last_scroll_top = scroll_result['after_scroll']
            
            # 최종 정보 로깅
            final_info = self._get_container_info()
            self.logger.info(
                f"스크롤 완료 - 총 {scroll_count}회, "
                f"최종 높이: {final_info['scrollHeight']}px"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"{page_type} 스크롤 중 오류: {str(e)}")
            traceback.print_exc()
            return False
            
    def _merge_screenshots(self, page_type: str = "ranking") -> bool:
        """스크린샷을 하나의 이미지로 합치기
        
        Args:
            page_type: 페이지 타입
            
        Returns:
            성공 여부
        """
        try:
            self.logger.info(f"{page_type} 스크린샷 합치기 시작...")
            
            # 스크린샷 파일 찾기
            screenshot_files = self._get_screenshot_files(page_type)
            if not screenshot_files:
                return False
            
            # 이미지 로드
            images = self._load_images(screenshot_files)
            
            # 이미지 합치기
            merged_image = self._combine_images(images)
            
            # 저장
            output_path = os.path.join(
                self.image_dir, 
                f"full_{page_type}_{self.date_str}.png"
            )
            merged_image.save(output_path)
            merged_image.close()
            
            self.logger.info(f"전체 스크린샷 저장: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"스크린샷 합치기 오류: {str(e)}")
            traceback.print_exc()
            return False
    
    def capture_pages(self) -> bool:
        """모든 페이지 캡처 실행
        
        Returns:
            성공 여부
        """
        try:
            pages = [
                {"name": "ranking", "url": self.RANKING_URL},
                {"name": "bodycare", "url": self.BODYCARE_URL}
            ]
            
            for page in pages:
                self.logger.info(f"\n{'='*50}")
                self.logger.info(f"{page['name'].upper()} 페이지 처리 시작")
                self.logger.info(f"{'='*50}")
                
                # 페이지 캡처
                if not self._capture_single_page(page['name'], page['url']):
                    self.logger.error(f"{page['name']} 페이지 캡처 실패")
                    continue
                    
            self.logger.info("\n모든 페이지 캡처 완료!")
            return True
            
        except Exception as e:
            self.logger.error(f"페이지 캡처 중 오류: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            self.close()
    
    def _capture_single_page(self, page_type: str, url: str) -> bool:
        """단일 페이지 캡처
        
        Args:
            page_type: 페이지 타입
            url: 페이지 URL
            
        Returns:
            성공 여부
        """
        # 페이지 접속
        self.logger.info(f"{page_type} 페이지 접속 중...")
        self.driver.get(url)
        time.sleep(3)
        
        # 페이지 정보 로깅
        self._log_page_info()
        
        # 스크롤 및 캡처
        if not self._scroll_and_capture(page_type):
            return False
            
        # 스크린샷 합치기
        return self._merge_screenshots(page_type)

    # 헬퍼 메서드들
    def _check_container_exists(self) -> bool:
        """컨테이너 존재 확인"""
        return self.driver.execute_script("""
            try {
                return document.evaluate(
                    '//*[@id="main-inner-swiper-ranking"]', 
                    document, null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null
                ).singleNodeValue !== null;
            } catch(e) {
                return false;
            }
        """)
    
    def _get_container_info(self) -> Dict:
        """컨테이너 정보 가져오기"""
        return self.driver.execute_script("""
            var container = document.evaluate(
                '//*[@id="main-inner-swiper-ranking"]', 
                document, null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, null
            ).singleNodeValue;
            return {
                scrollHeight: container.scrollHeight,
                clientHeight: container.clientHeight,
                scrollTop: container.scrollTop
            };
        """)
    
    def _perform_scroll(self) -> Dict:
        """스크롤 실행"""
        return self.driver.execute_script("""
            var container = document.evaluate(
                '//*[@id="main-inner-swiper-ranking"]', 
                document, null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, null
            ).singleNodeValue;
            
            var beforeHeight = container.scrollHeight;
            var beforeScrollTop = container.scrollTop;
            
            // 클라이언트 높이만큼 스크롤
            container.scrollTop += container.clientHeight;
            
            return {
                before_height: beforeHeight,
                after_height: container.scrollHeight,
                before_scroll: beforeScrollTop,
                after_scroll: container.scrollTop,
                client_height: container.clientHeight
            };
        """)
    
    def _save_screenshot(self, page_type: str, index: int) -> None:
        """스크린샷 저장"""
        filename = f"{page_type}_{index:03d}.png"
        filepath = os.path.join(self.temp_image_dir, filename)
        self.driver.save_screenshot(filepath)
        self.logger.info(f"스크린샷 저장: {filename}")
    
    def _log_scroll_info(self, count: int, scroll_result: Dict) -> None:
        """스크롤 정보 로깅"""
        self.logger.info(
            f"스크롤 #{count}: "
            f"{scroll_result['before_scroll']}px -> {scroll_result['after_scroll']}px "
            f"(변화: {scroll_result['after_scroll'] - scroll_result['before_scroll']}px)"
        )
    
    def _log_page_info(self) -> None:
        """페이지 정보 로깅"""
        self.logger.info(f"페이지 제목: {self.driver.title}")
        self.logger.info(f"페이지 URL: {self.driver.current_url}")
    
    def _get_screenshot_files(self, page_type: str) -> List[str]:
        """스크린샷 파일 목록 가져오기"""
        pattern = os.path.join(self.temp_image_dir, f"{page_type}_*.png")
        files = sorted(glob.glob(pattern))
        
        if not files:
            self.logger.error(f"{page_type} 스크린샷 파일을 찾을 수 없습니다.")
            return []
            
        # 마지막 2개 제외 (중복 가능성)
        files = files[:-2] if len(files) > 2 else files
        self.logger.info(f"{len(files)}개 스크린샷 파일 발견")
        return files
    
    def _load_images(self, files: List[str]) -> List[Image.Image]:
        """이미지 파일 로드"""
        return [Image.open(f) for f in files]
    
    def _combine_images(self, images: List[Image.Image]) -> Image.Image:
        """이미지 리스트를 하나로 합치기"""
        if not images:
            raise ValueError("이미지가 없습니다.")
            
        width = images[0].width
        total_height = sum(img.height for img in images)
        
        merged = Image.new('RGB', (width, total_height))
        
        y_offset = 0
        for img in images:
            merged.paste(img, (0, y_offset))
            y_offset += img.height
            img.close()
            
        return merged
    
    def close(self) -> None:
        """드라이버 종료"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info("드라이버 종료")


if __name__ == "__main__":
    # 테스트를 위해 headless=False로 설정 (브라우저 창 표시)
    crawler = OliveYoungCrawler(headless=False)
    crawler.capture_pages()