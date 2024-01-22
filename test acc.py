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






def log_daily_points_to_csv(date, earned_points, points_difference):
    logs_directory = Path(__file__).resolve().parent / "logs"
    csv_filename = logs_directory / "points_data.csv"

    # Create a new row with the date, daily points, and points difference
    date = datetime.now().strftime("%Y-%m-%d")
    new_row = {
        "Date": date,
        "Earned Points": earned_points,
        "Points Difference": points_difference,
    }

    fieldnames = ["Date", "Earned Points", "Points Difference"]
    is_new_file = not csv_filename.exists()

    with open(csv_filename, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if is_new_file:
            writer.writeheader()

        writer.writerow(new_row)


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


def executeBot(currentAccount, notifier: Notifier, args: argparse.Namespace):
    logging.info(f'******************** {currentAccount.get("username", "")} ********************')
    accountPointsCounter = 0
    remainingSearches = 0
    remainingSearchesM = 0
    startingPoints = 0

    try:
        with Browser(mobile=False, account=currentAccount, args=args) as desktopBrowser:
            try:
                accountPointsCounter = Login(desktopBrowser).login()
            except:
                logging.info("Failed to log in Desktop")
            

            startingPoints = accountPointsCounter
            if startingPoints == "Locked":
                notifier.send("🚫 Account is Locked", currentAccount)
                return 0
            if startingPoints == "Verify":
                notifier.send("❗ Account needs to be verified", currentAccount)
                return 0

            goalPoints = 3000
            try:
                goalTitle = desktopBrowser.utils.getGoalTitle()
            except:
                logging.info("Failed to retrieve goal title") 
            desktopBrowser.closeBrowser()
    except:
        logging.error("An exception occurred")


    try:
        with Browser(mobile=True, account=currentAccount, args=args) as mobileBrowser:
            try:
                accountPointsCounter = Login(mobileBrowser).login()
            except:
                logging.info("Failed to log in mobile")
            mobileBrowser.closeBrowser()
    except:
        logging.error("An exception occurred in mobile searches")

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
    main()

