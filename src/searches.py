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
                f'https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
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
        my_terms = ['google', 'youtube', 'facebook', 'pornhub', 'twitter', 'wikipedia', 'instagram', 'reddit', 'xvideos', 'duckduckgo', 'amazon', 'yahoo', 'yahoo japan', 'tiktok', 'xnxx', 'whatsapp', 'weather', 'bing', 'openai', 'yandex', 'vk', 'bilibili', 'pinterest', 'mail.ru', 'turbo pages', 'discord', 'the weather channel', 'microsoft', 'max', 'twitch', 'telegram', 'quora', 'linkedin', 'netflix', 'office', 'zen news', 'microsoft bing', 'xhamster', 'samsung electronics', 'microsoft online', 'naver', 'docomo', 'microsoft outlook', 'yandex search', 'baidu', 'x', 'google search', 'microsoft 365', 'who is Isaac Newton', 'how did Isaac Newton die', "Isaac Newton's inventions", 'who is Albert Einstein', 'how did Albert Einstein die', "Albert Einstein's inventions", 'who is Galileo Galilei', 'how did Galileo Galilei die', "Galileo Galilei's inventions", 'who is Charles Darwin', 'how did Charles Darwin die', "Charles Darwin's inventions", 'who is Marie Curie', 'how did Marie Curie die', "Marie Curie's inventions", 'who is Nikola Tesla', 'how did Nikola Tesla die', "Nikola Tesla's inventions", 'who is Stephen Hawking', 'how did Stephen Hawking die', "Stephen Hawking's inventions", 'who is Michael Faraday', 'how did Michael Faraday die', "Michael Faraday's inventions", 'who is James Clerk Maxwell', 'how did James Clerk Maxwell die', "James Clerk Maxwell's inventions", 'who is Louis Pasteur', 'how did Louis Pasteur die', "Louis Pasteur's inventions", 'who is Richard Feynman', 'how did Richard Feynman die', "Richard Feynman's inventions", 'who is Erwin Schrödinger', 'how did Erwin Schrödinger die', "Erwin Schrödinger's inventions", 'who is Gregor Mendel', 'how did Gregor Mendel die', "Gregor Mendel's inventions", 'who is Leonardo da Vinci', 'how did Leonardo da Vinci die', "Leonardo da Vinci's inventions", 'who is Carl Linnaeus', 'how did Carl Linnaeus die', "Carl Linnaeus's inventions", 'who is Dmitri Mendeleev', 'how did Dmitri Mendeleev die', "Dmitri Mendeleev's inventions", 'who is Thomas Edison', 'how did Thomas Edison die', "Thomas Edison's inventions", 'who is Max Planck', 'how did Max Planck die', "Max Planck's inventions", 'who is Niels Bohr', 'how did Niels Bohr die', "Niels Bohr's inventions", 'who is Alan Turing', 'how did Alan Turing die', "Alan Turing's inventions", 'Bohemian Rhapsody', 'Imagine', 'Stairway to Heaven', 'Like a Rolling Stone', 'Smells Like Teen Spirit', 'Hotel California', 'Billie Jean', 'Shape of You', 'Hey Jude', 'A Day in the Life', 'Thriller', 'I Will Always Love You', 'Purple Rain', "What's Going On", "Sweet Child o' Mine", 'Rolling in the Deep', 'Lose Yourself', 'Yesterday', 'My Heart Will Go On', 'Despacito', 'Baby Shark', 'Wheels on the Bus', 'Let It Go', 'Happy', 'Old MacDonald Had a Farm', 'Twinkle Twinkle Little Star', 'Baa Baa Black Sheep', 'Head, Shoulders, Knees and Toes', "How Far I'll Go", 'The Lion Sleeps Tonight', "Can't Stop the Feeling!", 'Five Little Ducks', 'Row, Row, Row Your Boat', "If You're Happy and You Know It", 'Mary Had a Little Lamb', 'BINGO', 'Do You Want to Build a Snowman?', 'Paw Patrol Theme Song', 'Under the Sea', "We're Going on a Bear Hunt", 'calculus practice problems', 'Vietnam War summary', 'chemical reaction experiments for high school', 'how to write a persuasive essay', 'latest Taylor Swift song', 'best strategy games for PC', 'how to manage time for studying', 'photosynthesis process', 'study tips for physics exams', 'famous poets of the 20th century', 'social media marketing basics', "how to solve a Rubik's cube fast", 'upcoming Marvel movies', 'healthy study snacks', 'Python programming for beginners', 'world history important events', 'how to prepare for college interviews', 'scholarships for high school seniors', 'stress relief exercises', 'benefits of meditation for students', 'how do rainbows form', 'funny cat videos', 'simple math games for kids', 'alphabet songs', 'how to draw a dinosaur', 'Peppa Pig episodes', 'why is the sky blue', 'bedtime stories online', 'how to make slime', 'best educational apps for kids', 'space cartoons for kids', 'learning shapes and colors', 'animal sounds for children', 'fairy tales for kids', 'easy crafts for kids', 'why do we need to sleep', 'dinosaur facts for kids', 'what do animals eat', 'how to tie shoelaces', 'songs about numbers', 'best budget travel destinations', 'how to build a resume', 'healthy meal prep recipes', 'latest fashion trends 2023', 'beginner yoga routines', 'part-time job opportunities near me', 'how to improve public speaking', 'easy coding projects for beginners', 'tips for managing college debt', 'DIY home decor ideas', 'how to start investing', 'best books for young adults', 'online photography course', 'how to brew craft beer at home', 'upcoming music festivals', 'maintaining mental health in college', 'how to learn a new language quickly', 'tips for acing job interviews', 'best smartphones under $500', 'how to make friends in a new city', 'how to balance work and family', 'best schools for children', 'healthy dinner recipes for families', 'mortgage rates comparison', 'mid-career change advice', 'how to start a small business', 'marathon training for beginners', 'gardening tips for beginners', 'investment strategies for retirement', 'travel destinations with kids', 'how to save for college education', 'stress management techniques', 'best cars for family safety', 'home renovation ideas on a budget', 'book recommendations for personal growth', 'tips for cooking healthy meals quickly', 'ways to increase home value', 'yoga for stress relief', 'best family pets', 'planning a family vacation on a budget', 'how to plan for early retirement', 'best health check-ups for age 40', 'college savings plans for children', 'home improvement DIY projects', 'career development for professionals over 40', 'best investment books', 'healthy meal planning for busy parents', 'advanced yoga classes online', 'how to start painting as a hobby', 'vacation spots for middle-aged couples', 'wine tasting guide for beginners', 'managing arthritis and joint pain', 'tips for helping aging parents', 'digital photography tips for beginners', 'cycling clubs for adults', 'how to improve sleep quality', 'top historical novels', 'estate planning basics', 'nutritional supplements for middle age', 'learning a musical instrument at 40', 'how to reduce cholesterol naturally', 'yoga retreats for adults', 'updating will and estate planning', 'college preparation for parents', 'mastering sourdough bread making', 'best places to visit in Europe', 'starting a vineyard', 'how to volunteer with wildlife conservation', 'effective workouts for people over 45', 'managing menopause symptoms', 'book clubs for adults', "online master's degree programs", 'landscape photography techniques', 'benefits of mindfulness meditation', 'personal finance for nearing retirement', 'restoring classic cars', 'learning to play guitar later in life', 'natural remedies for better sleep', 'adult bicycle clubs', 'gardening for biodiversity', 'best retirement savings strategies', 'travel destinations for retirees', 'health screenings for age 50', 'anti-inflammatory diet recipes', 'Tai Chi classes near me', 'how to write a memoir', 'wine making courses online', 'luxury train travel in Asia', 'grandparenting tips for the modern age', 'downsizing home in retirement', 'best electric cars 2023', 'maintaining cognitive health', 'volunteer opportunities for retirees', 'starting a bed and breakfast', 'age-appropriate fitness routines', 'art history courses for adults', 'managing arthritis pain', 'investing in real estate for beginners', 'meditation and aging', 'learning digital photography', 'senior cycling groups', 'preparing for knee replacement surgery', 'starting an online business', 'top 10 historical novels', 'herbal teas for health', 'building a greenhouse', 'Italian language course for beginners', 'managing empty nest syndrome', 'yoga for arthritis', 'financial planning for grandchildren s education', 'bird watching for beginners', 'classic car restoration tips', 'guides to the national parks', 'beginner watercolor painting', 'ancestry and genealogy research', 'tips for healthy aging', 'how to start a podcast', 'book recommendations for book clubs', 'elderly care for beginners', 'sustainable gardening practices', 'creative writing workshops online', 'how do bees make honey', 'best kids movies on Netflix', 'easy science experiments for kids', 'why is the ocean salty', 'how to draw a unicorn', 'Minecraft for beginners', 'ABC learning games online', 'what do animals dream about', 'simple DIY crafts for kids', 'how to make a paper airplane', 'songs to help with math', 'dinosaurs and their names', 'space videos for kids', 'underwater animals for children', 'why do we have seasons', 'learning to read books online', 'funny jokes for kids', 'how to take care of a pet fish', 'bedtime stories about dragons', 'ways to recycle at home for kids', 'learning about planets in solar system', 'fairy tale princesses and their stories', 'how to plant a flower', 'puzzle games for kids', 'cartoon drawing tutorials', 'what is the fastest animal', 'kids yoga video', 'magic tricks for kids', 'healthy snacks for kids', 'how to tie shoelaces for kids', 'playground games for children', 'what makes rainbows', 'origami for kids', 'why do we yawn', 'learning about different cultures for kids', 'how to make slime with glue', 'best children books 2023', 'easy baking recipes for kids', 'how to build a sandcastle', 'learning basic French for kids', 'nature scavenger hunt for kids', 'how to solve math problems faster', 'Roblox tips for beginners', 'science fair project ideas', 'history of the dinosaurs', 'how to write a short story', 'soccer drills for kids', 'fun facts about the solar system', 'chapter books for 9 year olds', 'drawing anime for beginners', 'learning magic card tricks', 'building a simple robot', 'coding for kids free resources', 'how to play chess', 'making friendship bracelets', 'easy songs to learn on the guitar', 'why do we dream when we sleep', 'volcano experiments for kids', 'best video games for kids', 'how to care for a hamster', 'ballet moves for beginners', 'learning about ancient Egypt', 'how to do a cartwheel', 'what are the seven wonders of the world', 'swimming tips for beginners', 'creating a comic book', 'how to make a bird feeder', 'studying tips for exams', 'planting a vegetable garden', 'DIY room decoration ideas for kids', 'beginner skateboard tricks', 'facts about the rainforest', 'how to write in cursive', 'learning to speak Spanish', 'making homemade pizza', 'cool science experiments', 'origami models for kids', 'what is global warming', 'how to make a YouTube video', 'learning about marine life', 'fun outdoor activities for kids', 'what is the fastest animal in the world', 'tips for starting middle school', 'math puzzles for 6th graders', 'how to do a science project on renewable energy', 'young adult fantasy book recommendations', 'beginner programming languages', 'how to customize your school locker', 'history of video games', 'simple baking recipes for kids', 'how to start a blog', 'DIY crafts for tweens', 'ways to deal with bullying', 'learning guitar chords', 'best apps for studying and homework', 'how to improve in soccer', 'studying the stars and planets', 'science experiments you can do at home', 'funny riddles and jokes', 'tips for memorizing faster', 'easy dances to learn', 'how to care for pet turtles', 'building model airplanes', 'video editing for beginners', 'learning about world cultures', 'creating digital art', 'how to solve a Rubik\'s cube', 'tips for writing a book', 'building a simple website', 'math games online', 'how to make new friends at school', 'the importance of healthy eating', 'cool magic tricks revealed', 'outdoor survival skills for kids', 'fun facts about ancient civilizations', 'how to draw manga characters', 'learning about the human body', 'how to play the piano', 'exploring the ocean', 'easy yoga for kids', 'projects with Raspberry Pi', 'understanding climate change', 'space exploration for kids', 'how to deal with acne', 'study tips for high school entrance exams', 'young adult books with strong female leads', 'DIY bedroom decor for teens', 'beginner workouts for teens', 'safety tips for social media', 'how to talk to your crush', 'math help for algebra', 'science fair projects on environmental issues', 'tips for learning a second language', 'volunteer opportunities for teens', 'how to manage stress and anxiety', 'understanding body image and self-esteem', 'programming projects for beginners', 'easy healthy meals for teenagers', 'choosing the right extracurricular activities', 'dealing with peer pressure', 'how to start a YouTube channel', 'online safety for teenagers', 'learning to play guitar', 'how to write a resume for your first job', 'beginner photography tips', 'creative writing prompts for teens', 'exploring career options for teenagers', 'building confidence in public speaking', 'teenagers\' rights and responsibilities', 'understanding global warming and climate action', 'how to save money as a teenager', 'the science of sleep for teenagers', 'personal hygiene tips for teens', 'cyberbullying: what it is and how to stop it', 'history of rock music', 'beginner skateboarding tricks', 'how to improve academic writing', 'mental health resources for teenagers', 'what is cryptocurrency', 'developing leadership skills as a teenager', 'science behind video games', 'ancient civilizations and their mysteries', 'DIY fashion projects for teens', 'learning about different cultures around the world', 'college application tips', 'how to budget for university', 'dating advice for young adults', 'beginner cooking recipes for college students', 'tips for living with roommates', 'best part-time jobs for students', 'how to build a good credit score', 'study abroad opportunities', 'internship application strategies', 'effective study techniques for college', 'first apartment checklist', 'maintaining long-distance friendships', 'personal safety on campus', 'beginner workout routines', 'managing stress during exams', 'starting a small online business', 'volunteer work that looks good on a resume', 'scholarship search strategies', 'healthy eating on a budget', 'time management apps for students', 'exploring career paths', 'basic car maintenance for new drivers', 'understanding student loans', 'DIY dorm room decor ideas', 'personal development books for young adults', 'how to meditate for stress relief', 'traveling solo safely', 'learning a new language online', 'dealing with homesickness', 'rights and responsibilities of new adults', 'how to negotiate your first salary', 'building a professional wardrobe', 'creating a personal brand online', 'writing a compelling CV', 'tips for acing job interviews', 'planning a gap year', 'safe sex education for adults', 'mental health resources for college students', 'understanding taxes for first-time earners', 'balancing work and study', 'finding mentorship in your field', 'how to network effectively', 'starting a fitness journey', 'developing leadership skills', 'legal rights as an 18-year-old', 'tips for buying your first car', 'self-defense classes for women', 'financial planning for young adults', 'ethical volunteering']









        
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
