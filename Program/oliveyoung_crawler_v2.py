"""
Olive Young Crawler V2 - Optimized for multiple categories
Creates new driver session for each category to avoid blocking
"""

import time
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import logging


@dataclass
class RankingCategory:
    """Data class for ranking category information"""
    name: str
    display_name: str
    url: str


class RankingPeriod(Enum):
    """Enum for ranking periods"""
    REALTIME = "REALTIME"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class OliveYoungCrawlerV2:
    """Optimized Olive Young ranking crawler"""
    
    BASE_URL_TEMPLATE = (
        "https://m.oliveyoung.co.kr/m/mtn?menu=ranking&"
        "t_page=home&t_click=GNB&t_gnb_type=ranking&"
        "t_swiping_type=N&tab=sales{category}&period={period}"
    )
    
    RANKING_CONTAINER_XPATH = '//*[@id="main-inner-swiper-ranking"]'
    
    def __init__(self, base_dir: str = None, headless: bool = True):
        self.headless = headless
        self.base_dir = Path(base_dir or '/Users/isy_mac_mini/Project/personal/oliveyoung/Data')
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Setup directories
        self.data_dir = self.base_dir / 'crawler_v2'
        self.screenshot_dir = self.data_dir / 'screenshots'
        self.log_dir = self.data_dir / 'logs'
        self.temp_dir = self.data_dir / 'temp' / self.session_id
        
        for directory in [self.data_dir, self.screenshot_dir, self.log_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Load categories
        self.categories = self._load_categories()
        
        self.logger.info(f"Initialized OliveYoungCrawlerV2 - Session: {self.session_id}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger(f"OliveYoungV2_{self.session_id}")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        
        # File handler
        log_file = self.log_dir / f"crawler_{self.session_id}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_categories(self) -> List[RankingCategory]:
        """Load ranking categories"""
        return [
            RankingCategory(
                name="all",
                display_name="전체",
                url=self.BASE_URL_TEMPLATE.format(category="", period="{period}")
            ),
            RankingCategory(
                name="skincare",
                display_name="스킨케어",
                url=self.BASE_URL_TEMPLATE.format(category="&category=10000010001", period="{period}")
            ),
            RankingCategory(
                name="makeup",
                display_name="메이크업",
                url=self.BASE_URL_TEMPLATE.format(category="&category=10000010009", period="{period}")
            ),
            RankingCategory(
                name="bodycare",
                display_name="바디케어",
                url=self.BASE_URL_TEMPLATE.format(category="&category=10000010003", period="{period}")
            ),
            RankingCategory(
                name="haircare",
                display_name="헤어케어",
                url=self.BASE_URL_TEMPLATE.format(category="&category=10000010004", period="{period}")
            ),
            RankingCategory(
                name="perfume",
                display_name="향수/디퓨저",
                url=self.BASE_URL_TEMPLATE.format(category="&category=10000010008", period="{period}")
            ),
            RankingCategory(
                name="menscare",
                display_name="남성케어",
                url=self.BASE_URL_TEMPLATE.format(category="&category=10000010010", period="{period}")
            ),
            RankingCategory(
                name="health",
                display_name="헬스케어",
                url=self.BASE_URL_TEMPLATE.format(category="&category=10000020001", period="{period}")
            )
        ]
    
    def _create_driver(self) -> webdriver.Chrome:
        """Create a new Chrome driver instance"""
        options = Options()
        
        # Basic options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # Mobile emulation
        mobile_emulation = {
            "deviceMetrics": {
                "width": 375,
                "height": 812,
                "pixelRatio": 3.0
            },
            "userAgent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            )
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        # Anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        if self.headless:
            options.add_argument('--headless')
        
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(375, 812)
        
        return driver
    
    def capture_category(
        self,
        category: RankingCategory,
        period: RankingPeriod = RankingPeriod.REALTIME
    ) -> Optional[str]:
        """Capture ranking for a single category with new driver"""
        self.logger.info(f"Starting capture for {category.display_name}")
        
        # Create new driver for this category
        driver = self._create_driver()
        
        try:
            # Navigate to URL
            url = category.url.format(period=period.value)
            self.logger.info(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for page load
            time.sleep(5)
            
            # Check page status
            if "잠시만 기다리십시오" in driver.title:
                self.logger.warning(f"Blocked page detected for {category.display_name}")
                return None
            
            self.logger.info(f"Page loaded: {driver.title}")
            
            # Capture scrolling screenshots
            screenshots = self._capture_scrolling_screenshots(
                driver,
                category.name,
                period.value.lower()
            )
            
            if not screenshots:
                self.logger.error(f"No screenshots captured for {category.display_name}")
                return None
            
            # Merge screenshots
            output_path = self._merge_screenshots(
                screenshots,
                f"{category.name}_{period.value.lower()}"
            )
            
            self.logger.info(f"Successfully captured {category.display_name}: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error capturing {category.display_name}: {e}")
            return None
        
        finally:
            driver.quit()
            self.logger.info(f"Driver closed for {category.display_name}")
    
    def _capture_scrolling_screenshots(
        self,
        driver,
        category_name: str,
        period: str,
        max_scrolls: int = 50
    ) -> List[str]:
        """Capture screenshots while scrolling"""
        screenshots = []
        
        try:
            # Check container exists
            container_exists = driver.execute_script(f"""
                return document.evaluate('{self.RANKING_CONTAINER_XPATH}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue !== null;
            """)
            
            if not container_exists:
                self.logger.error("Container not found")
                return screenshots
            
            # Get container info
            container_info = driver.execute_script(f"""
                var container = document.evaluate('{self.RANKING_CONTAINER_XPATH}', document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                return {{
                    scrollHeight: container.scrollHeight,
                    clientHeight: container.clientHeight
                }};
            """)
            
            self.logger.info(
                f"Container: {container_info['scrollHeight']}px height, "
                f"{container_info['clientHeight']}px viewport"
            )
            
            # Scroll and capture
            scroll_count = 0
            last_scroll_top = -1
            
            while scroll_count < max_scrolls:
                # Capture screenshot
                screenshot_path = self.temp_dir / f"{category_name}_{period}_{scroll_count:03d}.png"
                driver.save_screenshot(str(screenshot_path))
                screenshots.append(str(screenshot_path))
                
                # Scroll
                scroll_result = driver.execute_script(f"""
                    var container = document.evaluate('{self.RANKING_CONTAINER_XPATH}', document, null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    var beforeTop = container.scrollTop;
                    container.scrollTop += container.clientHeight;
                    return {{
                        before: beforeTop,
                        after: container.scrollTop
                    }};
                """)
                
                scroll_count += 1
                
                # Check if reached bottom
                if scroll_result['after'] == last_scroll_top:
                    self.logger.info(f"Reached bottom after {scroll_count} scrolls")
                    break
                
                last_scroll_top = scroll_result['after']
                time.sleep(1.5)
            
            return screenshots
            
        except Exception as e:
            self.logger.error(f"Error during scrolling: {e}")
            return screenshots
    
    def _merge_screenshots(self, screenshots: List[str], output_name: str) -> Optional[str]:
        """Merge screenshots into one image"""
        if not screenshots:
            return None
        
        try:
            # Remove duplicates at the end
            if len(screenshots) > 2:
                screenshots = screenshots[:-2]
            
            # Open images
            images = [Image.open(path) for path in screenshots]
            
            # Calculate dimensions
            width = images[0].width
            total_height = sum(img.height for img in images)
            
            # Create merged image
            merged = Image.new('RGB', (width, total_height))
            
            # Paste images
            y_offset = 0
            for img in images:
                merged.paste(img, (0, y_offset))
                y_offset += img.height
                img.close()
            
            # Save
            output_path = self.screenshot_dir / f"{output_name}_{self.session_id}.png"
            merged.save(str(output_path), optimize=True, quality=95)
            merged.close()
            
            # Cleanup temp files
            for path in screenshots:
                try:
                    Path(path).unlink()
                except:
                    pass
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error merging screenshots: {e}")
            return None
    
    def capture_all(
        self,
        categories: Optional[List[str]] = None,
        period: RankingPeriod = RankingPeriod.REALTIME,
        delay_between: int = 15
    ) -> Dict[str, str]:
        """Capture multiple categories with delay between each"""
        results = {}
        
        # Filter categories
        target_categories = self.categories
        if categories:
            target_categories = [c for c in self.categories if c.name in categories]
        
        total = len(target_categories)
        
        for i, category in enumerate(target_categories, 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Processing {i}/{total}: {category.display_name}")
            self.logger.info(f"{'='*60}")
            
            result = self.capture_category(category, period)
            
            if result:
                results[category.name] = result
                self.logger.info(f"✅ Success: {category.display_name}")
            else:
                self.logger.warning(f"❌ Failed: {category.display_name}")
            
            # Delay between categories
            if i < total:
                self.logger.info(f"Waiting {delay_between} seconds before next category...")
                time.sleep(delay_between)
        
        # Save summary
        summary_file = self.data_dir / f"summary_{self.session_id}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'period': period.value,
                'results': results,
                'success_count': len(results),
                'total_count': total
            }, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Completed: {len(results)}/{total} categories captured")
        self.logger.info(f"Summary saved: {summary_file}")
        
        return results


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Olive Young Crawler V2')
    parser.add_argument('--categories', nargs='+', help='Categories to capture')
    parser.add_argument('--period', default='REALTIME', help='Ranking period')
    parser.add_argument('--delay', type=int, default=15, help='Delay between categories')
    parser.add_argument('--no-headless', action='store_true', help='Run with GUI')
    
    args = parser.parse_args()
    
    crawler = OliveYoungCrawlerV2(
        headless=not args.no_headless
    )
    
    results = crawler.capture_all(
        categories=args.categories,
        period=RankingPeriod[args.period],
        delay_between=args.delay
    )
    
    print(f"\n✅ Capture completed: {len(results)} categories")
    for cat, path in results.items():
        print(f"   - {cat}: {Path(path).name}")


if __name__ == "__main__":
    main()