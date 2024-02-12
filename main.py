import argparse
import atexit
import csv
import json
import logging
import logging.handlers as handlers
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
import os
import pandas as pd
import psutil
import threading
from src import (
    Browser,
    DailySet,
    Login,
    MorePromotions,
    PunchCards,
    Searches,
    VersusGame,
)
from src.loggingColoredFormatter import ColoredFormatter
from src.notifier import Notifier
from src.utils import Utils

POINTS_COUNTER = 0


def main():
    print("test", Utils.randomSeconds(5, 10))
    args = argumentParser()
    notifier = Notifier(args)
    setupLogging(args.verbosenotifs, notifier)
    loadedAccounts = setupAccounts()
    # Register the cleanup function to be called on script exit
    atexit.register(cleanupChromeProcesses)

    # Load previous day's points data
    previous_points_data = load_previous_points_data()

    for currentAccount in loadedAccounts:
        try:
            earned_points = executeBot(currentAccount, notifier, args)
            account_name = currentAccount.get("username", "")
            previous_points = previous_points_data.get(account_name, 0)

            # Calculate the difference in points from the prior day
            points_difference = earned_points - previous_points

            # Append the daily points and points difference to CSV and Excel
            log_daily_points_to_csv(account_name, earned_points, points_difference)

            # Update the previous day's points data
            previous_points_data[account_name] = earned_points

            logging.info(f"[POINTS] Data for '{account_name}' appended to the file.")
            close_chrome()
            time.sleep(10)
        except Exception as e:
            notifier.send("⚠️ Error occurred, please check the log", currentAccount)
            logging.exception(f"{e.__class__.__name__}: {e}")

    # Save the current day's points data for the next day in the "logs" folder
    save_previous_points_data(previous_points_data)
    logging.info("[POINTS] Data saved for the next day.")


def close_chrome():
    """
    Hàm này sẽ tắt tất cả các cửa sổ Chrome đang mở.
    """
    os.system("taskkill /im chrome.exe /f")






def log_daily_points_to_csv(account_name, earned_points, points_difference):
    logs_directory = Path(__file__).resolve().parent / "logs"
    csv_filename = logs_directory / "points_data.csv"

    # Đọc dữ liệu hiện tại từ CSV
    if csv_filename.exists():
        with open(csv_filename, mode="r") as file:
            reader = csv.DictReader(file)
            data = list(reader)
    else:
        data = []

    # Tạo hoặc cập nhật dòng dữ liệu
    date = datetime.now().strftime("%Y-%m-%d")
    row = next((item for item in data if item["Account Name"] == account_name and item["Date"] == date), None)
    if row:
        # Cập nhật dòng nếu tài khoản đã tồn tại
        row["Earned Points"] = earned_points
        row["Points Difference"] = points_difference
    else:
        # Thêm dòng mới nếu tài khoản chưa tồn tại
        data.append({
            "Date": date,
            "Account Name": account_name,
            "Earned Points": earned_points,
            "Points Difference": points_difference,
        })

    # Ghi lại dữ liệu vào CSV
    fieldnames = ["Date", "Account Name", "Earned Points", "Points Difference"]
    with open(csv_filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def setupLogging(verbose_notifs, notifier):
    ColoredFormatter.verbose_notifs = verbose_notifs
    ColoredFormatter.notifier = notifier

    format = "%(asctime)s [%(levelname)s] %(message)s"
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(format))

    logs_directory = Path(__file__).resolve().parent / "logs"
    logs_directory.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                logs_directory / "activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
        ],
    )


def cleanupChromeProcesses():
    # Use psutil to find and terminate Chrome processes
    for process in psutil.process_iter(["pid", "name"]):
        if process.info["name"] == "chrome.exe":
            try:
                psutil.Process(process.info["pid"]).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


def argumentParser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MS Rewards Farmer")
    parser.add_argument(
        "-v", "--visible", action="store_true", help="Optional: Visible browser"
    )
    parser.add_argument(
        "-l", "--lang", type=str, default=None, help="Optional: Language (ex: en)"
    )
    parser.add_argument(
        "-g", "--geo", type=str, default=None, help="Optional: Geolocation (ex: US)"
    )
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        default=None,
        help="Optional: Global Proxy (ex: http://user:pass@host:port)",
    )
    parser.add_argument(
        "-t",
        "--telegram",
        metavar=("TOKEN", "CHAT_ID"),
        nargs=2,
        type=str,
        default=None,
        help="Optional: Telegram Bot Token and Chat ID (ex: 123456789:ABCdefGhIjKlmNoPQRsTUVwxyZ 123456789)",
    )
    parser.add_argument(
        "-d",
        "--discord",
        type=str,
        default=None,
        help="Optional: Discord Webhook URL (ex: https://discord.com/api/webhooks/123456789/ABCdefGhIjKlmNoPQRsTUVwxyZ)",
    )
    parser.add_argument(
        "-vn",
        "--verbosenotifs",
        action="store_true",
        help="Optional: Send all the logs to discord/telegram",
    )
    parser.add_argument(
        "-cv",
        "--chromeversion",
        type=int,
        default=None,
        help="Optional: Set fixed Chrome version (ex. 118)",
    )
    return parser.parse_args()


def setupAccounts() -> list:
    """Sets up and validates a list of accounts loaded from 'accounts.json'."""

    def validEmail(email: str) -> bool:
        """Validate Email."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email))

    accountPath = Path(__file__).resolve().parent / "accounts.json"
    if not accountPath.exists():
        accountPath.write_text(
            json.dumps(
                [{"username": "Your Email", "password": "Your Password"}], indent=4
            ),
            encoding="utf-8",
        )
        noAccountsNotice = """
    [ACCOUNT] Accounts credential file "accounts.json" not found.
    [ACCOUNT] A new file has been created, please edit with your credentials and save.
    """
        logging.warning(noAccountsNotice)
        exit()
    loadedAccounts = json.loads(accountPath.read_text(encoding="utf-8"))
    for account in loadedAccounts:
        if not validEmail(account["username"]):
            logging.error(f"[CREDENTIALS] Wrong Email Address: '{account['username']}'")
            exit()
    random.shuffle(loadedAccounts)
    return loadedAccounts


def login_with_timeout(desktopBrowser, notifier, currentAccount, shared_result):
    try:
        login_result = Login(desktopBrowser).login()
        shared_result['login_result'] = login_result
    except Exception as e:
        notifier.send(f"⚠️ Error occurred during login for account {currentAccount.get('username')}: {e}", currentAccount)
        shared_result['login_result'] = None

def executeBot(currentAccount, notifier: Notifier, args: argparse.Namespace):
    logging.info(f'******************** {currentAccount.get("username", "")} ********************')
    accountPointsCounter = 0
    remainingSearches = 0
    remainingSearchesM = 0
    startingPoints = 0
    skip_account = False
    shared_result = {}

    try:
        with Browser(mobile=False, account=currentAccount, args=args) as desktopBrowser:
            login_thread = threading.Thread(target=login_with_timeout, args=(desktopBrowser, notifier, currentAccount, shared_result))
            login_thread.start()
            login_thread.join(timeout=600)

            if login_thread.is_alive():
                notifier.send(f"⚠️ Account {currentAccount.get('username')} đăng nhập không thành công", currentAccount)
                login_thread.join()  # Đợi cho đến khi thread hoàn tất
                desktopBrowser.closeBrowser()
                skip_account = True
            elif shared_result.get('login_result') is not None:
                accountPointsCounter = shared_result['login_result']
                startingPoints = accountPointsCounter
                login_successful = True
            else:
                notifier.send(f"❗ Account {currentAccount.get('username')} needs attention", currentAccount)
                desktopBrowser.closeBrowser()
                skip_account = True
    
            logging.info(f"[POINTS] You have {desktopBrowser.utils.formatNumber(accountPointsCounter)} points on your account")
            
            try:
                DailySet(desktopBrowser).completeDailySet()
            except:
                logging.info("Failed to do Daily set")
                

            try:
                PunchCards(desktopBrowser).completePunchCards()
            except:
                logging.info("Failed to do PunchCards")
                

            try:
                MorePromotions(desktopBrowser).completeMorePromotions()
            except:
                logging.info("Failed to do MorePromotions")
                

            try:
                remainingSearches, remainingSearchesM = desktopBrowser.utils.getRemainingSearches()
            except:
                logging.info("Failed to getRemainingSearches")
 

            # Introduce random pauses before and after searches
            pause_before_search = random.uniform(11.0, 15.0)  # Random pause between 11 to 15 seconds
            time.sleep(pause_before_search)

            try:
                if remainingSearches != 0:
                    accountPointsCounter = Searches(desktopBrowser).bingSearches(remainingSearches)
            except:
                logging.info("Failed to do Searches")
           

            pause_after_search = random.uniform(11.0, 15.0)  # Random pause between 11 to 15 seconds
            time.sleep(pause_after_search)
            
            desktopBrowser.utils.goHome()
            goalPoints = 3000
            try:
                goalTitle = desktopBrowser.utils.getGoalTitle()
            except:
                logging.info("Failed to retrieve goal title")
            desktopBrowser.closeBrowser()

    except:
        logging.error("An exception occurred")

    if remainingSearchesM != 0:
        try:
            with Browser(mobile=True, account=currentAccount, args=args) as mobileBrowser:
                login_thread = threading.Thread(target=login_with_timeout, args=(mobileBrowser, notifier, currentAccount))
                login_thread.start()
                login_thread.join(timeout=600)  # Đặt giới hạn thời gian là 10 phút

                if login_thread.is_alive():
                    notifier.send(f"⚠️ Account {currentAccount.get('username')} đăng nhập trên mobile không thành công", currentAccount)
                    login_thread.join()  # Đợi cho đến khi thread hoàn tất
                    mobileBrowser.closeBrowser()
                    skip_account = True


                login_result = login_with_timeout(mobileBrowser, notifier, currentAccount)

                if login_result is None or login_result in ["Locked", "Verify"]:
                    notifier.send(f"❗ Account {currentAccount.get('username')} needs attention: {login_result}", currentAccount)
                    mobileBrowser.closeBrowser()
                    skip_account = True

    

                accountPointsCounter = login_result or 0
                  

                try:
                    if remainingSearchesM != 0:
                        accountPointsCounter = Searches(mobileBrowser).bingSearches(remainingSearchesM)
                except:
                    logging.info("Failed to do mobile Searches")
                  

                mobileBrowser.utils.goHome()
                mobileBrowser.closeBrowser()
        except:
            logging.error("An exception occurred in mobile searches")

    logging.info(f"[POINTS] You have earned {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)} points today!")
    logging.info(f"[POINTS] You are now at {desktopBrowser.utils.formatNumber(accountPointsCounter)} points!")

    goalNotifier = ""
    if goalPoints > 0:
        percentage_of_goal_reached = (accountPointsCounter / goalPoints) * 100
        logging.info(f"[POINTS] You are now at {desktopBrowser.utils.formatNumber(percentage_of_goal_reached)}% of your goal ({goalTitle})! ")
        goalNotifier = f"🎯 Goal reached: {desktopBrowser.utils.formatNumber(percentage_of_goal_reached)}% ({goalTitle})"

    notifier.send(
        "\n".join([
            f"*****************************",
            f"⭐️ Points earned today: {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)}",
            f"💰 Total points: {desktopBrowser.utils.formatNumber(accountPointsCounter)}",
            goalNotifier,
        ]),
        currentAccount,
    )
    if accountPointsCounter > goalPoints:
        notifier.send(f"🎯 Đã đủ point @everyone")
        
    if skip_account:
        return 0

    if remainingSearchesM == 0:
        logging.info(f"[SLEEP] Account is lvl 1!!! Sleeping for 2 hours")
        time.sleep(random.randint(3500, 4000))
        
    return accountPointsCounter



def export_points_to_csv(points_data):
    logs_directory = Path(__file__).resolve().parent / "logs"
    csv_filename = logs_directory / "points_data.csv"
    with open(csv_filename, mode="a", newline="") as file:  # Use "a" mode for append
        fieldnames = ["Account", "Earned Points", "Points Difference"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Check if the file is empty, and if so, write the header row
        if file.tell() == 0:
            writer.writeheader()

        for data in points_data:
            writer.writerow(data)


# Define a function to load the previous day's points data from a file in the "logs" folder
def load_previous_points_data():
    logs_directory = Path(__file__).resolve().parent / "logs"
    try:
        with open(logs_directory / "previous_points_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Define a function to save the current day's points data for the next day in the "logs" folder
def save_previous_points_data(data):
    logs_directory = Path(__file__).resolve().parent / "logs"
    with open(logs_directory / "previous_points_data.json", "w") as file:
        json.dump(data, file, indent=4)



if __name__ == "__main__":
    while True:
        main()
        time.sleep(900)
