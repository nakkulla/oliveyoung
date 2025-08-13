#!/usr/bin/env python3
"""
Single category test - Simple version
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def test_single_page():
    # Setup Chrome options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Mobile emulation
    mobile_emulation = {
        "deviceMetrics": {
            "width": 375,
            "height": 812,
            "pixelRatio": 3.0
        },
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    
    # Additional options to avoid detection
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Test URL
        url = "https://m.oliveyoung.co.kr/m/mtn?menu=ranking&t_page=home&t_click=GNB&t_gnb_type=ranking&t_swiping_type=N&tab=sales&period=REALTIME"
        
        print(f"Navigating to: {url}")
        driver.get(url)
        
        print("Waiting for page load...")
        time.sleep(5)
        
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Check if blocked
        if "잠시만 기다리십시오" in driver.title:
            print("⚠️  Blocked by anti-bot system")
        else:
            print("✅ Page loaded successfully")
            
            # Try to find the container
            container_exists = driver.execute_script("""
                return document.querySelector('#main-inner-swiper-ranking') !== null;
            """)
            
            if container_exists:
                print("✅ Container found")
            else:
                print("❌ Container not found")
        
    finally:
        driver.quit()
        print("Driver closed")

if __name__ == "__main__":
    test_single_page()