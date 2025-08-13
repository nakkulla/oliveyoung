import logging
import time
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import functools
import undetected_chromedriver as uc
from selenium_stealth import stealth
from fake_useragent import UserAgent
import random


class BaseCrawler:
    """Base crawler class with improved error handling and configuration management"""
    
    def __init__(
        self,
        name: str = "BaseCrawler",
        headless: bool = True,
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.headless = headless
        self.config = config or self._get_default_config()
        
        # Setup directories
        self.base_dir = Path(self.config.get('base_dir', '/root/project/etc/Data'))
        self.setup_directories()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize driver
        self.driver = None
        self.wait = None
        self._init_driver()
        
        # Session tracking
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.logger.info(f"Initialized {self.name} - Session: {self.session_id}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'base_dir': '/root/project/etc/Data',
            'window_size': {'width': 1920, 'height': 1080},
            'wait_timeout': 20,
            'retry_attempts': 3,
            'retry_delay': 5,
            'log_level': 'INFO'
        }
    
    def setup_directories(self):
        """Setup required directories"""
        self.data_dir = self.base_dir / self.name.lower()
        self.log_dir = self.data_dir / 'logs'
        self.screenshot_dir = self.data_dir / 'screenshots'
        
        for directory in [self.data_dir, self.log_dir, self.screenshot_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"{self.name}_{datetime.now().strftime('%Y%m%d')}")
        logger.setLevel(getattr(logging, self.config.get('log_level', 'INFO')))
        
        # Remove existing handlers
        logger.handlers = []
        
        # File handler
        log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_driver(self):
        """Initialize Chrome driver with anti-detection measures"""
        try:
            options = self._get_chrome_options()
            
            # Use undetected-chromedriver
            self.driver = uc.Chrome(options=options, headless=self.headless)
            self.wait = WebDriverWait(self.driver, self.config.get('wait_timeout', 20))
            
            # Apply stealth techniques
            stealth(self.driver,
                    languages=["ko-KR", "ko", "en-US", "en"],
                    vendor="Google Inc.",
                    platform="Linux armv8l" if self.config.get('use_mobile') else "Win32",
                    webgl_vendor="ARM" if self.config.get('use_mobile') else "Intel Inc.",
                    renderer="Mali-G78" if self.config.get('use_mobile') else "Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )
            
            # Inject additional anti-detection JavaScript
            self._inject_stealth_scripts()
            
            self.logger.info("Chrome driver initialized with anti-detection")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def _get_chrome_options(self) -> Options:
        """Get Chrome options with anti-detection settings"""
        options = uc.ChromeOptions()
        
        # Enhanced anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        # options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        # options.add_experimental_option('useAutomationExtension', False)
        
        # Language settings for Korean sites
        options.add_argument('--lang=ko-KR')
        options.add_experimental_option('prefs', {
            'intl.accept_languages': 'ko-KR,ko,en-US,en',
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False
        })
        
        # Performance and stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--start-maximized')
        
        # New headless mode for Chrome >= 109
        if self.headless:
            options.add_argument('--headless=new')
            window_size = self.config.get('window_size', {})
            width = window_size.get('width', 1920)
            height = window_size.get('height', 1080)
            options.add_argument(f'--window-size={width},{height}')
        
        # Random user agent
        ua = UserAgent()
        user_agent = self.config.get('user_agent', ua.random)
        options.add_argument(f'user-agent={user_agent}')
        
        return options
    
    def _inject_stealth_scripts(self):
        """Inject additional stealth JavaScript"""
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {get: () => false});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                    window.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'permissions', {
                        get: () => ({
                            query: (p) => p.name === 'notifications' ? 
                                Promise.resolve({ state: 'prompt' }) : 
                                Promise.resolve({ state: 'granted' })
                        })
                    });
                '''
            })
        except Exception as e:
            self.logger.warning(f"Could not inject stealth scripts: {e}")
    
    @staticmethod
    def retry(max_attempts: int = 3, delay: int = 5):
        """Decorator for retry logic"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return func(self, *args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if hasattr(self, 'logger'):
                            self.logger.warning(
                                f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}"
                            )
                        else:
                            print(f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}")
                        
                        if attempt < max_attempts - 1:
                            time.sleep(delay)
                
                if hasattr(self, 'logger'):
                    self.logger.error(f"All attempts failed for {func.__name__}")
                raise last_exception
            
            return wrapper
        return decorator
    
    @contextmanager
    def error_handler(self, operation: str):
        """Context manager for error handling"""
        try:
            self.logger.info(f"Starting: {operation}")
            yield
            self.logger.info(f"Completed: {operation}")
        except Exception as e:
            self.logger.error(f"Failed: {operation} - {e}")
            self.take_screenshot(f"error_{operation}")
            raise
    
    def wait_for_element(
        self,
        by: By,
        value: str,
        timeout: Optional[int] = None,
        condition: str = "clickable"
    ):
        """Wait for element with different conditions"""
        timeout = timeout or self.config.get('wait_timeout', 20)
        
        conditions = {
            "clickable": EC.element_to_be_clickable,
            "visible": EC.visibility_of_element_located,
            "present": EC.presence_of_element_located
        }
        
        condition_func = conditions.get(condition, EC.element_to_be_clickable)
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                condition_func((by, value))
            )
            return element
        except TimeoutException:
            self.logger.error(f"Timeout waiting for element: {by}={value}")
            raise
    
    def wait_for_elements(
        self,
        by: By,
        value: str,
        timeout: Optional[int] = None
    ) -> List:
        """Wait for multiple elements"""
        timeout = timeout or self.config.get('wait_timeout', 20)
        
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            return elements
        except TimeoutException:
            self.logger.error(f"Timeout waiting for elements: {by}={value}")
            return []
    
    def element_exists(self, by: By, value: str, timeout: int = 5) -> bool:
        """Check if element exists"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False
    
    def safe_click(self, by: By, value: str, use_js: bool = False):
        """Safely click an element"""
        try:
            element = self.wait_for_element(by, value)
            
            if use_js:
                self.driver.execute_script("arguments[0].click();", element)
            else:
                element.click()
            
            self.logger.debug(f"Clicked element: {by}={value}")
        except Exception as e:
            self.logger.error(f"Failed to click element: {by}={value} - {e}")
            raise
    
    def safe_input(self, by: By, value: str, text: str, clear: bool = True):
        """Safely input text to an element"""
        try:
            element = self.wait_for_element(by, value, condition="visible")
            
            if clear:
                element.clear()
            
            element.send_keys(text)
            self.logger.debug(f"Input text to element: {by}={value}")
        except Exception as e:
            self.logger.error(f"Failed to input text: {by}={value} - {e}")
            raise
    
    def scroll_to_element(self, element):
        """Scroll to make element visible"""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element
        )
        time.sleep(0.5)
    
    def take_screenshot(self, name: Optional[str] = None) -> str:
        """Take screenshot with automatic naming"""
        if not name:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        screenshot_path = self.screenshot_dir / f"{name}.png"
        self.driver.save_screenshot(str(screenshot_path))
        self.logger.info(f"Screenshot saved: {screenshot_path}")
        return str(screenshot_path)
    
    def get_page_info(self) -> Dict[str, str]:
        """Get current page information"""
        return {
            'url': self.driver.current_url,
            'title': self.driver.title,
            'source_length': len(self.driver.page_source)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Driver closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()