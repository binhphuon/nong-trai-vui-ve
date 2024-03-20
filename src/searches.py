import json
import logging
import random
import time
from datetime import date, timedelta

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from src.browser import Browser
from src.utils import Utils


class Searches:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def getGoogleTrends(self, wordsCount: int) -> list:
        # Function to retrieve Google Trends search terms starting from a specific index
        searchTerms: list[str] = []
        startFrom = 13
        i = 0
        while len(searchTerms) < (wordsCount + startFrom):
            i += 1
            # Fetching daily trends from Google Trends API
            r = requests.get(
                f'https://trends.google.com/trends/api/dailytrends?hl={self.localeLang}&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.localeGeo}&ns=15'
            )
            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0]["trendingSearches"]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(
                    relatedTopic["query"].lower()
                    for relatedTopic in topic["relatedQueries"]
                )
            # Remove duplicates and keep unique search terms
            searchTerms = list(set(searchTerms))
        # Adjust the list to start from the specified index and limit to the desired count
        searchTerms = searchTerms[startFrom : startFrom + wordsCount]
        return searchTerms

    def getRelatedTerms(self, word: str) -> list:
        # Function to retrieve related terms from Bing API
        try:
            r = requests.get(
                f"https://api.bing.com/osjson.aspx?query={word}",
                headers={"User-agent": self.browser.userAgent},
            )
            return r.json()[1]
        except Exception:  # pylint: disable=broad-except
            return []

    def bingSearches(self, numberOfSearches: int, pointsCounter: int = 0):
        # Function to perform Bing searches
        logging.info(
            f"[BING] Starting {self.browser.browserType.capitalize()} Edge Bing searches..."
        )

        search_terms = self.getGoogleTrends(numberOfSearches)
        my_terms = ['google', 'youtube', 'facebook', 'pornhub', 'twitter', 'wikipedia', 'instagram', 'reddit', 'xvideos', 'duckduckgo', 'amazon', 'yahoo', 'yahoo japan', 'tiktok', 'xnxx', 'whatsapp', 'weather', 'bing', 'openai', 'yandex', 'vk', 'bilibili', 'pinterest', 'mail.ru', 'turbo pages', 'discord', 'the weather channel', 'microsoft', 'max', 'twitch', 'telegram', 'quora', 'linkedin', 'netflix', 'office', 'zen news', 'microsoft bing', 'xhamster', 'samsung electronics', 'microsoft online', 'naver', 'docomo', 'microsoft outlook', 'yandex search', 'baidu', 'x', 'google search', 'microsoft 365', 'who is Isaac Newton', 'how did Isaac Newton die', "Isaac Newton's inventions", 'who is Albert Einstein', 'how did Albert Einstein die', "Albert Einstein's inventions", 'who is Galileo Galilei', 'how did Galileo Galilei die', "Galileo Galilei's inventions", 'who is Charles Darwin', 'how did Charles Darwin die', "Charles Darwin's inventions", 'who is Marie Curie', 'how did Marie Curie die', "Marie Curie's inventions", 'who is Nikola Tesla', 'how did Nikola Tesla die', "Nikola Tesla's inventions", 'who is Stephen Hawking', 'how did Stephen Hawking die', "Stephen Hawking's inventions", 'who is Michael Faraday', 'how did Michael Faraday die', "Michael Faraday's inventions", 'who is James Clerk Maxwell', 'how did James Clerk Maxwell die', "James Clerk Maxwell's inventions", 'who is Louis Pasteur', 'how did Louis Pasteur die', "Louis Pasteur's inventions", 'who is Richard Feynman', 'how did Richard Feynman die', "Richard Feynman's inventions", 'who is Erwin Schrödinger', 'how did Erwin Schrödinger die', "Erwin Schrödinger's inventions", 'who is Gregor Mendel', 'how did Gregor Mendel die', "Gregor Mendel's inventions", 'who is Leonardo da Vinci', 'how did Leonardo da Vinci die', "Leonardo da Vinci's inventions", 'who is Carl Linnaeus', 'how did Carl Linnaeus die', "Carl Linnaeus's inventions", 'who is Dmitri Mendeleev', 'how did Dmitri Mendeleev die', "Dmitri Mendeleev's inventions", 'who is Thomas Edison', 'how did Thomas Edison die', "Thomas Edison's inventions", 'who is Max Planck', 'how did Max Planck die', "Max Planck's inventions", 'who is Niels Bohr', 'how did Niels Bohr die', "Niels Bohr's inventions", 'who is Alan Turing', 'how did Alan Turing die', "Alan Turing's inventions", 'Bohemian Rhapsody', 'Imagine', 'Stairway to Heaven', 'Like a Rolling Stone', 'Smells Like Teen Spirit', 'Hotel California', 'Billie Jean', 'Shape of You', 'Hey Jude', 'A Day in the Life', 'Thriller', 'I Will Always Love You', 'Purple Rain', "What's Going On", "Sweet Child o' Mine", 'Rolling in the Deep', 'Lose Yourself', 'Yesterday', 'My Heart Will Go On', 'Despacito', 'Baby Shark', 'Wheels on the Bus', 'Let It Go', 'Happy', 'Old MacDonald Had a Farm', 'Twinkle Twinkle Little Star', 'Baa Baa Black Sheep', 'Head, Shoulders, Knees and Toes', "How Far I'll Go", 'The Lion Sleeps Tonight', "Can't Stop the Feeling!", 'Five Little Ducks', 'Row, Row, Row Your Boat', "If You're Happy and You Know It", 'Mary Had a Little Lamb', 'BINGO', 'Do You Want to Build a Snowman?', 'Paw Patrol Theme Song', 'Under the Sea', "We're Going on a Bear Hunt", 'calculus practice problems', 'Vietnam War summary', 'chemical reaction experiments for high school', 'how to write a persuasive essay', 'latest Taylor Swift song', 'best strategy games for PC', 'how to manage time for studying', 'photosynthesis process', 'study tips for physics exams', 'famous poets of the 20th century', 'social media marketing basics', "how to solve a Rubik's cube fast", 'upcoming Marvel movies', 'healthy study snacks', 'Python programming for beginners', 'world history important events', 'how to prepare for college interviews', 'scholarships for high school seniors', 'stress relief exercises', 'benefits of meditation for students', 'how do rainbows form', 'funny cat videos', 'simple math games for kids', 'alphabet songs', 'how to draw a dinosaur', 'Peppa Pig episodes', 'why is the sky blue', 'bedtime stories online', 'how to make slime', 'best educational apps for kids', 'space cartoons for kids', 'learning shapes and colors', 'animal sounds for children', 'fairy tales for kids', 'easy crafts for kids', 'why do we need to sleep', 'dinosaur facts for kids', 'what do animals eat', 'how to tie shoelaces', 'songs about numbers']
        N = len(search_terms) // 3
        random_elements_from_B = random.sample(my_terms, len(search_terms) - N)
        random_indexes = random.sample(range(len(search_terms)), len(search_terms) - N)
        for index, new_value in zip(random_indexes, random_elements_from_B):
            search_terms[index] = new_value
        random.shuffle(search_terms)


        
        self.webdriver.get("https://bing.com")

        i = 0
        attempt = 0
        for word in search_terms:
            i += 1
            logging.info(f"[BING] {i}/{numberOfSearches}")
            points = self.bingSearch(word)
            if points <= pointsCounter:
                relatedTerms = self.getRelatedTerms(word)[:2]
                for term in relatedTerms:
                    points = self.bingSearch(term)
                    if not points <= pointsCounter:
                        break
            if points > 0:
                pointsCounter = points
            else:
                break

            if points <= pointsCounter:
                attempt += 1
                if attempt == 2:
                    logging.warning(
                        "[BING] Possible blockage. Refreshing the page."
                    )
                    self.webdriver.refresh()
                    attempt = 0
        logging.info(
            f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !"
        )
        return pointsCounter

    def bingSearch(self, word: str):
        # Function to perform a single Bing search
        i = 0

        while True:
            try:
                self.browser.utils.waitUntilClickable(By.ID, "sb_form_q")
                searchbar = self.webdriver.find_element(By.ID, "sb_form_q")
                searchbar.clear()
                searchbar.send_keys(word)
                searchbar.submit()
                time.sleep(Utils.randomSeconds(100, 180))

                # Scroll down after the search (adjust the number of scrolls as needed)
                for _ in range(3):  # Scroll down 3 times
                    self.webdriver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    time.sleep(
                        Utils.randomSeconds(7, 10)
                    )  # Random wait between scrolls

                return self.browser.utils.getBingAccountPoints()
            except TimeoutException:
                if i == 5:
                    logging.info("[BING] " + "TIMED OUT GETTING NEW PROXY")
                    self.webdriver.proxy = self.browser.giveMeProxy()
                elif i == 10:
                    logging.error(
                        "[BING] "
                        + "Cancelling mobile searches due to too many retries."
                    )
                    return self.browser.utils.getBingAccountPoints()
                self.browser.utils.tryDismissAllMessages()
                logging.error("[BING] " + "Timeout, retrying in 5~ seconds...")
                time.sleep(Utils.randomSeconds(7, 15))
                i += 1
                continue
