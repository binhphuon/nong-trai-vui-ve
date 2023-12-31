import argparse
import json
import logging
import logging.handlers as handlers
import random
import sys
from pathlib import Path

from selenium.common.exceptions import TimeoutException
from src import Browser, DailySet, Login, MorePromotions, PunchCards, Searches
from src.constants import VERSION
from src.loggingColoredFormatter import ColoredFormatter
from src.notifier import Notifier
import time


POINTS_COUNTER = 0


def main():
    setupLogging()
    args = argumentParser()
    notifier = Notifier(args)
    loadedAccounts = setupAccounts()
    for currentAccount in loadedAccounts:
        try:
            executeBot(currentAccount, notifier, args)
        except Exception as e:
            logging.exception(f"{e.__class__.__name__}: {e}")


def setupLogging():
    format = "%(asctime)s [%(levelname)s] %(message)s"
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(format))

    (Path(__file__).resolve().parent / "logs").mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                "logs/activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
        ],
    )


def argumentParser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Microsoft Rewards Farmer")
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
    return parser.parse_args()


def bannerDisplay():
    farmerBanner = """
    ███╗   ███╗███████╗    ███████╗ █████╗ ██████╗ ███╗   ███╗███████╗██████╗
    ████╗ ████║██╔════╝    ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗
    ██╔████╔██║███████╗    █████╗  ███████║██████╔╝██╔████╔██║█████╗  ██████╔╝
    ██║╚██╔╝██║╚════██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══╝  ██╔══██╗
    ██║ ╚═╝ ██║███████║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║
    ╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝"""
    logging.error(farmerBanner)
    logging.warning(
        f"        by binhphuon             version {VERSION}\n"
    )


def setupAccounts() -> dict:
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
    random.shuffle(loadedAccounts)
    return loadedAccounts


def executeBot(currentAccount, notifier: Notifier, args: argparse.Namespace):
    logging.info(
        f'********************{ currentAccount.get("username", "") }********************'
    )
    timeout_counter = 0  # Thêm biến đếm timeout
    max_timeouts = 4     # Số lần tối đa trước khi chuyển tài khoản

    try:
        with Browser(mobile=False, account=currentAccount, args=args) as desktopBrowser:
            try:
                accountPointsCounter = Login(desktopBrowser).login()
            except Exception as e:
                logging.exception("Lỗi khi đăng nhập: " + str(e))
                notifier.send_login_failure(currentAccount.get('username'))
                return    # Chuyển sang tài khoản tiếp theo nếu không thể đăng nhập



            startingPoints = accountPointsCounter
            logging.info(
                f"[POINTS] You have {desktopBrowser.utils.formatNumber(accountPointsCounter)} points on your account !"
            )

            # Thực hiện DailySet
            try:
                DailySet(desktopBrowser).completeDailySet()
            except Exception as e:
                logging.exception("Lỗi khi thực hiện DailySet: " + str(e))

            # Thực hiện PunchCards
            try:
                PunchCards(desktopBrowser).completePunchCards()
            except Exception as e:
                logging.exception("Lỗi khi thực hiện PunchCards: " + str(e))

            # Thực hiện MorePromotions
            try:
                MorePromotions(desktopBrowser).completeMorePromotions()
            except Exception as e:
                logging.exception("Lỗi khi thực hiện MorePromotions: " + str(e))

            # Thực hiện tìm kiếm Bing
            try: #Search pc
                remainingSearches, remainingSearchesM = desktopBrowser.utils.getRemainingSearches()
                if remainingSearches != 0:
                    logging.info(
                        f"Doing pc search"
                    )                    
                    accountPointsCounter = Searches(desktopBrowser).bingSearches(remainingSearches)

                    timeout_counter = 0  # Reset biến đếm timeout khi tìm kiếm thành công
                else:
                    logging.info(
                        f"Pc search is done"
                    )
                    #Search mobile
                    
                if remainingSearchesM != 0:
                    desktopBrowser.closeBrowser()
                    try:
                        with Browser(mobile=True, account=currentAccount, args=args) as mobileBrowser:
                            try:
                                accountPointsCounter = Login(mobileBrowser).login()
                            except Exception as e:
                                logging.exception("Lỗi khi đăng nhập trên mobile: " + str(e))
                                notifier.send_login_failure(currentAccount.get('username'))
                                return    # Chuyển sang tài khoản tiếp theo nếu không thể đăng nhập

                            accountPointsCounter = Searches(mobileBrowser).bingSearches(remainingSearchesM)
                    except Exception as e:
                        logging.exception("Lỗi tổng thể khi thực hiện trên mobile: " + str(e))
                        return  
                else:
                    logging.info(
                        f"Mobile search is done"
                    )
                    
            except TimeoutException as e:
                timeout_counter += 1
                logging.exception("Timeout trong quá trình tìm kiếm Bing: " + str(e))
                if timeout_counter >= max_timeouts:
                    return  # Thoát khỏi hàm để chuyển sang tài khoản tiếp theo
            except Exception as e:
                logging.exception("Lỗi khác khi thực hiện tìm kiếm Bing: " + str(e))

            # Kết thúc và gửi thông báo
            logging.info(
                f"[POINTS] You have earned {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)} points today !"
            )
            logging.info(
                f"[POINTS] You are now at {desktopBrowser.utils.formatNumber(accountPointsCounter)} points !\n"
            )


            input_str = desktopBrowser.utils.formatNumber(accountPointsCounter)
            # Loại bỏ dấu phẩy
            cleaned_str = input_str.replace(",", "")
            # Chuyển đổi thành float
            float_value = float(cleaned_str)
            if float_value > 3000:
                notifier.send(
                    "\n".join(
                        [
                            "_____________________",
                            f"{currentAccount.get('username', '')}",
                            f"Earned: {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)}",
                            f"Total: {desktopBrowser.utils.formatNumber(accountPointsCounter)}",
                            f"@everyone"
                        ]
                    )
                )
            else:
                notifier.send(
                    "\n".join(
                        [
                            "_____________________",
                            f"{currentAccount.get('username', '')}",
                            f"Earned: {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)}",
                            f"Total: {desktopBrowser.utils.formatNumber(accountPointsCounter)}",
                        ]
                    )
                )

                
    except Exception as e:
        logging.exception("Một lỗi đã xảy ra: " + str(e))
        error_message = f"Lỗi đã xảy ra khi thực hiện nhiệm vụ với tài khoản {currentAccount.get('username')}: {str(e)} @everyone"
        notifier.send_error_notification(error_message)
        
while True:
    if __name__ == "__main__":
        main()
        time.sleep(900)
