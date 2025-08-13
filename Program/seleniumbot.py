import logging
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
# import tools  # Commented out as we're simplifying
import math
import functools
import requests
import os
from datetime import datetime
import pickle


class GetCurrencyError(Exception):
    pass

class SeleniumBot:

    @staticmethod
    def retry(max_attempts=2, delay=10):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                attempts = 0
                while attempts < max_attempts:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        attempts += 1
                        print(f"Attempt {attempts} failed with error: {e}. Retrying...")
                        time.sleep(delay)
                return func(*args, **kwargs)
            return wrapper
        return decorator


    def __init__(self, username = 'ilsun', headless = True, platform = 'nas'):
        self.folder = os.path.join(os.getcwd(), "Data")  # Simplified folder path
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, 20)
        self.username = username
        self.lterm = 10
        self.sterm = 3
        # Telegram functionality disabled for now
        # self.chat_id = tools.fjson('ilsun', 'telegram', 'id')
        # self.token = tools.fjson('ilsun', 'telegram', 'token')
        # self.bot = tools.MyBot(token=self.token , id=self.chat_id)

        # Create log folder
        self.log_folder = os.path.join(self.folder, 'log')
        os.makedirs(self.log_folder, exist_ok=True)

        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Setup logging for this instance
        self.logger_name = f"{self.__class__.__name__}_{date_str}"
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.INFO)
        
        # FileHandler path using class name and username
        self.log_file_path = os.path.join(f"{self.log_folder}", f"{self.logger_name}.log")
        
        # Ensure no duplicate handlers
        if not self.logger.handlers:
            fh = logging.FileHandler(self.log_file_path)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

        # Example usage
        self.logger.info(f"Initialized {self.__class__.__name__} for {self.username}")

    def log_message(self, message):
        self.logger.info(message)

    def log_photo(self, message):
        # Assuming a method to take a screenshot or handle a photo
        self.logger.info(message)
        # Example logging a dummy screenshot path
        screenshot_path = f'{self.log_folder}/{self.logger_name}_{int(time.time())}.png'
        self.driver.save_screenshot(screenshot_path)
        self.logger.info(f'Screenshot saved: {screenshot_path}')

    def send_log_file(self):
        # Telegram functionality disabled
        self.logger.info("Telegram functionality disabled in simplified version")

    def _init_driver(self, headless):
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')  # Bypass OS security model
        options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
        options.add_argument('--disable-gpu')  # Applicable to windows os only
        options.add_argument('disable-infobars')
        options.add_argument('--disable-extensions')

        if headless:
            options.add_argument('--headless')  # Run in headless mode
            options.add_argument('start-maximized')  # Start maximized
            options.add_argument("--window-size=1920,1080")

        else:
            # options.add_argument("window-size=1,1")
            options.add_argument("--window-position=-32000,-32000")
        return webdriver.Chrome(options=options)

    def handle_alert(self):
        try:
            # Wait for the alert to be present and then accept it
            WebDriverWait(self.driver, 10).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            print(f"Alert displayed: {alert_text}")
            alert.accept()
            print("Alert accepted.")
            return alert_text
        except (NoAlertPresentException, TimeoutException):
            # Handle cases where no alert is present or the wait times out
            print("No alert present or alert handling timed out.")

    def wait_for_element(self, by, value, timeout=10):
        time.sleep(1)
        # Wait for the element to be clickable for the specified timeout
        return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))

    def wait_for_elements(self, by, value, timeout=10):
        time.sleep(1)
        # Wait for all elements located by the specified method and value to be clickable
        return WebDriverWait(self.driver, timeout).until(EC.visibility_of_all_elements_located((by, value)))

    def download_image(self, image_url, save_path):
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                print(f"Image downloaded to {save_path}, from {image_url}")
                file.write(response.content)

    def click_via_javascript(self, by, value, timeout=10):
        try:
            element = self.wait_for_element(by, value, timeout)
            self.driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            print(f"Error while clicking element via JavaScript: {e}")


    def element_exists(self, by, value, timeout=5):
        try:
            # Wait for the element to be present for the specified timeout
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))
            return True
        except TimeoutException:
            # If the element is not found within the timeout period
            return False
        
    retry(max_attempts=3, delay=5)
    def get_currency(self, currency='USD'):

        try :
            self.driver.get('https://mongnas.synology.me:8887/')
            target = self.wait_for_element(By.ID, f"value_currency_list_{currency}").text.split(':')[1].replace('"', '')

            self.log_message(f"get_currency : {currency} {target}")
            self.value = target

        except Exception as e:
            print(e)
            print(f"get_currency : error!")
            self.send_photo(message="get_currency : error!")


    def send_photo(self, message, path=None):
        if path is None:
            path = f"{self.folder}/temp.png"
        self.driver.save_screenshot(path)
        self.logger.info(f"Screenshot saved: {path} - {message}")
        # Telegram functionality disabled
        # self.bot.send_message(f"{time.strftime('%c', time.localtime())} {message}")
        # self.bot.send_photo(path)

    def send_message(self, message):
        self.logger.info(f"Message: {message}")
        # Telegram functionality disabled
        # self.bot.send_message(f"{time.strftime('%c', time.localtime())} {message}")

    def checkbox_selector(self, by, target):
        try:
            checkbox = self.driver.find_element(by, target)
            if not checkbox.is_selected():
                print(f"checkbox_selector : {target} is not selected!")
                self.driver.execute_script("arguments[0].click();", checkbox)
                print(f"checkbox_selector : {target} selected!")
            else:
                print(f"checkbox_selector : {target} already selected!")
        except ElementNotInteractableException as e:
            print(f"Checkbox selection failed for {target}: {e}")

    def input_text_and_wait(self, by, element_id, text):
        element = WebDriverWait(self.driver, self.sterm).until(EC.visibility_of_element_located((by, element_id)))
        element.clear()
        element.send_keys(text)

    def click_and_wait(self, by, element_id):
        WebDriverWait(self.driver, self.sterm).until(EC.element_to_be_clickable((by, element_id))).click()


    def save_cookies(self, cookie_path):
        try:
            cookies = self.driver.get_cookies()
            with open(cookie_path, "wb") as cookie_file:
                pickle.dump(cookies, cookie_file)
            print(f"Cookies saved : {cookie_path}")
        except Exception as e:
            print(f"Error saving cookies: {e}")

    def load_cookies(self, cookie_path):
        try:
            self.driver.delete_all_cookies()
            with open(cookie_path, "rb") as cookie_file:
                cookies = pickle.load(cookie_file)
            for cookie in cookies:
                self.driver.add_cookie(cookie)

            print(f"Cookie loaded: {cookie}")
        except Exception as e:
            print(f"Error loading cookies: {e}")