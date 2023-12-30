import contextlib
import logging
import time
import urllib.parse
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By

from src.browser import Browser


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        self.webdriver.get("https://login.live.com/")
        alreadyLoggedIn = False
        while True:
            try:
                self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 0.1
                )
                alreadyLoggedIn = True
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    self.utils.waitUntilVisible(By.ID, "loginHeader", 0.1)
                    break
                except Exception:  # pylint: disable=broad-except
                    if self.utils.tryDismissAllMessages():
                        continue

        if not alreadyLoggedIn:
            self.executeLogin()
        self.utils.tryDismissCookieBanner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.goHome()
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] " + "Ensuring login on Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully !")
        return points


    def executeLogin(self):
        try:
            for attempt in range(3):  # Thử tối đa 3 lần
                try:
                    self.utils.waitUntilVisible(By.ID, "loginHeader", 10)
                    self.webdriver.find_element(By.NAME, "loginfmt").send_keys(self.browser.username)
                    self.webdriver.find_element(By.ID, "idSIButton9").click()
                    self.enterPassword(self.browser.password)
                    time.sleep(10)
                    if self.isLoginSuccessful():
                        return
                    else:
                        logging.info(f"[LOGIN] Đăng nhập thất bại, thử lại lần {attempt + 1}")
                except WebDriverException:
                    logging.error("[LOGIN] Trình duyệt không phản hồi, thử lại...")
                    # Khởi động lại trình duyệt ở đây nếu cần

            logging.error("[LOGIN] Không thể đăng nhập sau 3 lần thử, chuyển sang tài khoản tiếp theo")
            raise Exception("Đăng nhập thất bại sau 3 lần thử")
        except TimeoutException:
            logging.error("[LOGIN] Quá thời gian chờ, chuyển sang tài khoản tiếp theo")
            raise

    def isLoginSuccessful(self):
        try:
            self.utils.waitUntilVisible(By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 10)
            return True
        except TimeoutException:
            return False

    def enterPassword(self, password):
        self.utils.waitUntilClickable(By.NAME, "passwd", 10)
        self.utils.waitUntilClickable(By.ID, "idSIButton9", 10)
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')
        self.webdriver.execute_script(
            f'document.getElementsByName("passwd")[0].value = "{password}";'
        )
        logging.info("[LOGIN] " + "Writing password...")
        self.webdriver.find_element(By.ID, "idSIButton9").click()
        time.sleep(3)

    def checkBingLogin(self):
        self.webdriver.get(
            "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
        )
        while True:
            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        return
            time.sleep(1)
