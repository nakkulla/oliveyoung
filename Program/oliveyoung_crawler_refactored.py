import time
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from PIL import Image
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from base_crawler import BaseCrawler


@dataclass
class RankingCategory:
    """Data class for ranking category information"""
    name: str
    display_name: str
    url: str
    category_code: Optional[str] = None


class RankingPeriod(Enum):
    """Enum for ranking periods"""
    REALTIME = "REALTIME"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ScreenshotManager:
    """Manages screenshot capture and merging operations"""
    
    def __init__(self, base_dir: Path, session_id: str, logger):
        self.base_dir = base_dir
        self.session_id = session_id
        self.logger = logger
        self.temp_dir = base_dir / 'temp' / session_id
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def capture_scrolling_screenshots(
        self,
        driver,
        container_xpath: str,
        category_name: str,
        max_scrolls: int = 50,
        scroll_pause: float = 1.5
    ) -> List[str]:
        """Capture screenshots while scrolling through container"""
        screenshots = []
        
        try:
            # Check container exists
            if not self._container_exists(driver, container_xpath):
                self.logger.error(f"Container not found: {container_xpath}")
                return screenshots
            
            # Get initial container info
            container_info = self._get_container_info(driver, container_xpath)
            self.logger.info(
                f"Container info - Height: {container_info['scrollHeight']}px, "
                f"Client Height: {container_info['clientHeight']}px"
            )
            
            # Capture screenshots while scrolling
            scroll_count = 0
            last_scroll_top = -1
            
            while scroll_count < max_scrolls:
                # Capture screenshot
                screenshot_path = self.temp_dir / f"{category_name}_{scroll_count:03d}.png"
                driver.save_screenshot(str(screenshot_path))
                screenshots.append(str(screenshot_path))
                
                # Scroll
                scroll_result = self._scroll_container(driver, container_xpath)
                scroll_count += 1
                
                self.logger.debug(
                    f"Scroll #{scroll_count}: "
                    f"{scroll_result['before_scroll']}px -> {scroll_result['after_scroll']}px"
                )
                
                # Check if reached bottom
                if scroll_result['after_scroll'] == last_scroll_top:
                    self.logger.info(f"Reached bottom after {scroll_count} scrolls")
                    break
                
                last_scroll_top = scroll_result['after_scroll']
                time.sleep(scroll_pause)
            
            return screenshots
            
        except Exception as e:
            self.logger.error(f"Error capturing scrolling screenshots: {e}")
            return screenshots
    
    def _container_exists(self, driver, xpath: str) -> bool:
        """Check if container exists"""
        return driver.execute_script(f"""
            try {{
                return document.evaluate('{xpath}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue !== null;
            }} catch(e) {{
                return false;
            }}
        """)
    
    def _get_container_info(self, driver, xpath: str) -> Dict:
        """Get container information"""
        return driver.execute_script(f"""
            var container = document.evaluate('{xpath}', document, null,
                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            return {{
                scrollHeight: container.scrollHeight,
                clientHeight: container.clientHeight,
                scrollTop: container.scrollTop
            }};
        """)
    
    def _scroll_container(self, driver, xpath: str) -> Dict:
        """Scroll container and return scroll information"""
        return driver.execute_script(f"""
            var container = document.evaluate('{xpath}', document, null,
                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            var beforeScrollTop = container.scrollTop;
            var beforeHeight = container.scrollHeight;
            
            container.scrollTop += container.clientHeight;
            
            return {{
                before_scroll: beforeScrollTop,
                after_scroll: container.scrollTop,
                before_height: beforeHeight,
                after_height: container.scrollHeight,
                client_height: container.clientHeight
            }};
        """)
    
    def merge_screenshots(
        self,
        screenshots: List[str],
        output_name: str,
        overlap_pixels: int = 100
    ) -> Optional[str]:
        """Merge multiple screenshots into one long image"""
        if not screenshots:
            self.logger.error("No screenshots to merge")
            return None
        
        try:
            # Remove last few screenshots if they're duplicates
            if len(screenshots) > 2:
                screenshots = screenshots[:-2]
            
            # Open all images
            images = [Image.open(path) for path in screenshots]
            
            # Calculate dimensions
            width = images[0].width
            total_height = sum(img.height for img in images)
            
            # Adjust for overlap if needed
            if overlap_pixels > 0 and len(images) > 1:
                total_height -= overlap_pixels * (len(images) - 1)
            
            # Create merged image
            merged = Image.new('RGB', (width, total_height))
            
            # Paste images
            y_offset = 0
            for i, img in enumerate(images):
                merged.paste(img, (0, y_offset))
                y_offset += img.height
                
                # Adjust for overlap
                if overlap_pixels > 0 and i < len(images) - 1:
                    y_offset -= overlap_pixels
                
                img.close()
            
            # Save merged image
            output_path = self.base_dir / f"{output_name}_{self.session_id}.png"
            merged.save(str(output_path), optimize=True, quality=95)
            merged.close()
            
            self.logger.info(f"Merged screenshot saved: {output_path}")
            
            # Cleanup temp files
            self._cleanup_temp_files(screenshots)
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error merging screenshots: {e}")
            return None
    
    def _cleanup_temp_files(self, files: List[str]):
        """Clean up temporary files"""
        for file_path in files:
            try:
                Path(file_path).unlink()
            except Exception as e:
                self.logger.warning(f"Failed to delete temp file {file_path}: {e}")


class OliveYoungCrawler(BaseCrawler):
    """Refactored Olive Young ranking crawler"""
    
    # Base URL template
    BASE_URL_TEMPLATE = (
        "https://m.oliveyoung.co.kr/m/mtn?menu=ranking&"
        "t_page=home&t_click=GNB&t_gnb_type=ranking&"
        "t_swiping_type=N&tab=sales{category}&period={period}"
    )
    
    # Container XPath
    RANKING_CONTAINER_XPATH = '//*[@id="main-inner-swiper-ranking"]'
    
    def __init__(
        self,
        headless: bool = True,
        use_mobile: bool = True,
        config: Optional[Dict] = None
    ):
        # Store mobile setting first
        self.use_mobile = use_mobile
        
        # Setup configuration
        default_config = {
            'base_dir': '/Users/isy_mac_mini/Project/personal/oliveyoung/Data',
            'window_size': {'width': 375, 'height': 812} if use_mobile else {'width': 1920, 'height': 1080},
            'wait_timeout': 20,
            'retry_attempts': 3,
            'retry_delay': 5,
            'log_level': 'INFO'
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(
            name="OliveYoungCrawler",
            headless=headless,
            config=default_config
        )
        self.screenshot_manager = ScreenshotManager(
            self.screenshot_dir,
            self.session_id,
            self.logger
        )
        
        # Setup categories
        self.categories = self._load_categories()
        
        # Apply mobile settings if needed
        if use_mobile:
            self._setup_mobile_emulation()
    
    def _get_chrome_options(self) -> Options:
        """Override to add mobile emulation if needed"""
        options = super()._get_chrome_options()
        
        if self.use_mobile:
            mobile_emulation = {
                "deviceMetrics": {
                    "width": 375,
                    "height": 812,
                    "pixelRatio": 3.0,
                    "touch": True,
                    "mobile": True
                },
                "userAgent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/15.0 Mobile/15E148 Safari/604.1"
                )
            }
            options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        return options
    
    def _setup_mobile_emulation(self):
        """Setup mobile emulation settings"""
        if self.use_mobile and self.driver:
            self.driver.set_window_size(375, 812)
            self.logger.info("Mobile emulation enabled")
    
    def _wait_for_page_complete_load(self, timeout: int = 30):
        """Wait for page and all images to be completely loaded"""
        try:
            # Wait for document ready state
            for _ in range(timeout):
                ready_state = self.driver.execute_script("return document.readyState")
                if ready_state == "complete":
                    break
                time.sleep(1)
            
            # Wait for images to load
            self.driver.execute_script("""
                return new Promise((resolve) => {
                    const images = document.querySelectorAll('img');
                    let loadedCount = 0;
                    const totalImages = images.length;
                    
                    if (totalImages === 0) {
                        resolve();
                        return;
                    }
                    
                    const checkAllLoaded = () => {
                        loadedCount++;
                        if (loadedCount >= totalImages) {
                            resolve();
                        }
                    };
                    
                    images.forEach(img => {
                        if (img.complete) {
                            checkAllLoaded();
                        } else {
                            img.addEventListener('load', checkAllLoaded);
                            img.addEventListener('error', checkAllLoaded);
                        }
                    });
                    
                    // Timeout after 10 seconds
                    setTimeout(resolve, 10000);
                });
            """)
            
            # Wait for lazy-loaded images
            time.sleep(2)
            
            # Scroll down a bit to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            self.logger.info("Page and images loaded completely")
            
        except Exception as e:
            self.logger.warning(f"Error waiting for page load: {e}")
    
    def _load_categories(self) -> List[RankingCategory]:
        """Load ranking categories"""
        categories = [
            RankingCategory(
                name="all",
                display_name="전체 랭킹",
                url="https://m.oliveyoung.co.kr/m/mtn?menu=ranking&t_page=home&t_click=GNB&t_gnb_type=ranking&t_swiping_type=N&tab=sales&period=REALTIME"
            ),
            RankingCategory(
                name="bodycare",
                display_name="바디케어",
                url="https://m.oliveyoung.co.kr/m/mtn?oy=0&menu=ranking&t_page=home&t_click=GNB&t_gnb_type=ranking&t_swiping_type=N&tab=sales&category=10000010003&period=REALTIME"
            )

        ]
        
        # Save categories to config file
        config_file = self.data_dir / 'categories_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(
                [{'name': c.name, 'display_name': c.display_name, 'url': c.url} 
                 for c in categories],
                f,
                ensure_ascii=False,
                indent=2
            )
        
        return categories
    
    @BaseCrawler.retry(max_attempts=3, delay=5)
    def capture_category_ranking(
        self,
        category: RankingCategory,
        period: RankingPeriod = RankingPeriod.REALTIME
    ) -> Optional[str]:
        """Capture ranking screenshots for a specific category"""
        with self.error_handler(f"Capturing {category.display_name} rankings"):
            # Navigate to category page (URL is already complete, no formatting needed)
            url = category.url
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Initial wait for page load
            time.sleep(3)
            
            # Check and handle blocking page
            max_wait_attempts = 5
            for attempt in range(max_wait_attempts):
                if "잠시만 기다리십시오" in self.driver.title:
                    self.logger.warning(f"Detected blocking page, attempt {attempt + 1}/{max_wait_attempts}")
                    time.sleep(10)
                    self.driver.refresh()
                    time.sleep(5)
                else:
                    break
            
            # Wait for content to be fully loaded
            self._wait_for_page_complete_load()
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            # Log page info
            page_info = self.get_page_info()
            self.logger.info(
                f"Page loaded - Title: {page_info['title']}, "
                f"URL: {page_info['url']}"
            )
            
            # Capture scrolling screenshots
            screenshots = self.screenshot_manager.capture_scrolling_screenshots(
                self.driver,
                self.RANKING_CONTAINER_XPATH,
                f"{category.name}_realtime",
                max_scrolls=50,
                scroll_pause=1.5
            )
            
            if not screenshots:
                self.logger.error(f"No screenshots captured for {category.display_name}")
                return None
            
            # Merge screenshots
            output_name = f"{category.name}_realtime_ranking"
            merged_path = self.screenshot_manager.merge_screenshots(
                screenshots,
                output_name,
                overlap_pixels=50
            )
            
            return merged_path
    
    def capture_all_rankings(
        self,
        categories: Optional[List[str]] = None,
        period: RankingPeriod = RankingPeriod.REALTIME
    ) -> Dict[str, str]:
        """Capture rankings for multiple categories"""
        results = {}
        
        # Filter categories if specified
        target_categories = self.categories
        if categories:
            target_categories = [c for c in self.categories if c.name in categories]
        
        total = len(target_categories)
        
        for i, category in enumerate(target_categories, 1):
            self.logger.info(f"Processing {i}/{total}: {category.display_name}")
            
            try:
                result = self.capture_category_ranking(category, period)
                if result:
                    results[category.name] = result
                    self.logger.info(f"Successfully captured {category.display_name}")
                else:
                    self.logger.warning(f"Failed to capture {category.display_name}")
            
            except Exception as e:
                self.logger.error(f"Error processing {category.display_name}: {e}")
                continue
            
            # Add delay between categories to avoid blocking
            if i < total:
                self.logger.info("Waiting before next category...")
                time.sleep(10)
        
        # Save results summary
        summary_file = self.data_dir / f"capture_summary_{self.session_id}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    'session_id': self.session_id,
                    'timestamp': datetime.now().isoformat(),
                    'period': period.value,
                    'results': results
                },
                f,
                ensure_ascii=False,
                indent=2
            )
        
        self.logger.info(f"Capture complete. Results saved to {summary_file}")
        return results
    
    def run(
        self,
        categories: Optional[List[str]] = None,
        period: str = "REALTIME"
    ):
        """Main execution method"""
        try:
            self.logger.info(f"Starting Olive Young crawler - Session: {self.session_id}")
            
            # Convert period string to enum
            period_enum = RankingPeriod[period.upper()]
            
            # Capture rankings
            results = self.capture_all_rankings(categories, period_enum)
            
            # Log summary
            self.logger.info(f"Completed capturing {len(results)} categories")
            for category, path in results.items():
                self.logger.info(f"  - {category}: {path}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Crawler execution failed: {e}")
            raise
        
        finally:
            self.cleanup()


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Olive Young Ranking Crawler')
    parser.add_argument(
        '--categories',
        nargs='+',
        help='Categories to capture (e.g., all skincare makeup)',
        default=None
    )
    parser.add_argument(
        '--period',
        choices=['REALTIME', 'DAILY', 'WEEKLY', 'MONTHLY'],
        default='REALTIME',
        help='Ranking period'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run in headless mode'
    )
    parser.add_argument(
        '--mobile',
        action='store_true',
        default=True,
        help='Use mobile emulation'
    )
    
    args = parser.parse_args()
    
    # Create crawler instance
    crawler = OliveYoungCrawler(
        headless=args.headless,
        use_mobile=args.mobile
    )
    
    # Run crawler
    try:
        results = crawler.run(
            categories=args.categories,
            period=args.period
        )
        print(f"\nCapture completed successfully!")
        print(f"Results: {results}")
    
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())