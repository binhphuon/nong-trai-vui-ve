import contextlib
import logging
import time
import urllib.parse
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import random
from src.browser import Browser
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        self.webdriver.get(
            "https://login.live.com/"
        )  # changed site to allow bypassing when M$ blocks access to login.live.com randomly
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
                    self.utils.waitUntilVisible(By.ID, "i0116", 10)
                    break
                except Exception:  # pylint: disable=broad-except
                    if self.utils.tryDismissAllMessages():
                        continue

        if not alreadyLoggedIn:
            if isLocked := self.executeLogin():
                return "Locked"
        self.utils.tryDismissCookieBanner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.goHome()
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] " + "Ensuring you are logged into Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def executeLogin(self):
        self.utils.waitUntilVisible(By.ID, "i0116", 10)
        logging.info("[LOGIN] " + "Entering email...")
        self.utils.waitUntilClickable(By.NAME, "loginfmt", 10)
        email_field = self.webdriver.find_element(By.NAME, "loginfmt")

        while True:
            email_field.send_keys(self.browser.username)
            time.sleep(3)
            if email_field.get_attribute("value") == self.browser.username:
                self.webdriver.find_element(By.ID, "idSIButton9").click()
                break

            email_field.clear()
            time.sleep(3)

        self.enterPassword(self.browser.password)

        while not (
            urllib.parse.urlparse(self.webdriver.current_url).path == "/"
            and urllib.parse.urlparse(self.webdriver.current_url).hostname
            == "account.microsoft.com"
        ):
            
            if urllib.parse.urlparse(self.webdriver.current_url).hostname == "rewards.bing.com":
                self.webdriver.get("https://account.microsoft.com")

            if "Abuse" in str(self.webdriver.current_url):
                logging.error(f"[LOGIN] {self.browser.username} is locked")
                return True
            self.utils.tryDismissAllMessages()
            time.sleep(1)

        self.utils.waitUntilVisible(
            By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 10
        )

    def enterPassword(self, password):
        self.utils.waitUntilClickable(By.NAME, "passwd", 10)
        self.utils.waitUntilClickable(By.ID, "idSIButton9", 10)
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')        
        logging.info("[LOGIN] " + "Writing password...")
        password_field = self.webdriver.find_element(By.NAME, "passwd")

        while True:
            password_field.send_keys(password)
            time.sleep(3)
            if password_field.get_attribute("value") == password:
                self.webdriver.find_element(By.ID, "idSIButton9").click()
                break

            password_field.clear()
            time.sleep(3)
        time.sleep(3)
    def remove_everything_after_at(email):
        # Tìm vị trí của ký tự '@' trong chuỗi
        at_position = email.find('@')
        # Nếu '@' không tồn tại trong chuỗi, trả về chuỗi gốc
        if at_position == -1:
            return email
        # Cắt và trả về phần chuỗi từ đầu đến vị trí của '@'
        return email[:at_position]

    def create_account(self):
        input_data = input("Enter the details in 'address_hotmail|pass_hotmail|name|last_name' format: ")
        address_hotmail, pass_hotmail, name, last_name = input_data.split('|')
        delay = random.uniform(0.2, 1)
        # B1: Truy cập vào login.live.com
        self.webdriver.get("https://login.live.com")
        time.sleep(2)  # Đợi trang tải
        
        # B2: Click vào "Create one!"
        self.webdriver.find_element(By.ID, "signup").click()
        time.sleep(2)
        
        # B3 - B5: Điền hotmail và click next
        hotmail_field = WebDriverWait(self.webdriver, 10).until(
            EC.visibility_of_element_located((By.NAME, "MemberName"))
        )
        for char in address_hotmail:
            hotmail_field.send_keys(char)
            time.sleep(delay)
        time.sleep(1)
        self.webdriver.find_element(By.ID, "iSignupAction").click()
        time.sleep(2)
        
        # B6 - B8: Điền mật khẩu và click next
        passhotmail_field = WebDriverWait(self.webdriver, 10).until(
            EC.visibility_of_element_located((By.NAME, "Password"))
        )
        for char in pass_hotmail:
            passhotmail_field.send_keys(char)
            time.sleep(delay)
        time.sleep(1)
        if passhotmail_field.get_attribute("value") == pass_hotmail:
            self.webdriver.find_element(By.ID, "iSignupAction").click()
        time.sleep(2)
        
        # B9 - B11: Điền tên, họ và click next
        name_field = self.webdriver.find_element(By.NAME, "FirstName")
        lastname_field = self.webdriver.find_element(By.NAME, "LastName")
        for char in name:
            name_field.send_keys(char)
            time.sleep(delay)
        for char in last_name:
            lastname_field.send_keys(char)
            time.sleep(delay)
        time.sleep(1)
        if name_field.get_attribute("value") == name and lastname_field.get_attribute("value") == last_name:
            self.webdriver.find_element(By.ID, "iSignupAction").click()
        time.sleep(2)
        
        # B12: Điền ngày tháng năm sinh và click next
        # Các ID cho dropdown menu ngày tháng năm
        day_select = Select(self.webdriver.find_element(By.ID, "BirthDay"))
        month_select = Select(self.webdriver.find_element(By.ID, "BirthMonth"))
        year_select = self.webdriver.find_element(By.ID, "BirthYear")
        
        Month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        Days = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28"]
        Years = ["1970", "1971", "1972", "1973", "1974", "1975", "1976", "1977", "1978", "1979", "1980", "1981", "1982", "1983", "1984", "1985", "1986", "1987", "1988", "1989", "1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999", "2000", "2001", "2002", "2003", "2004", "2005"]
        # Chọn giá trị từ dropdown menu.
        self.webdriver.find_element(By.ID, "BirthMonth").click()
        month_select.select_by_visible_text(random.choice(Month))
        self.webdriver.find_element(By.ID, "BirthDay").click()
        day_select.select_by_visible_text(random.choice(Days))
        year_select.send_keys(random.choice(Years))

        time.sleep(1) # Đợi dropdown được cập nhật
        self.webdriver.find_element(By.ID, "iSignupAction").click()
        input("Enter when done! ")
        time.sleep(9999999)



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
