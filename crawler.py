import undetected_chromedriver as uc
import time
import random
import json
import utils
import re
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import os


class Crawler:
    def __init__(self, options=None,
                 headless=False,
                 name="output",
                 browser_path=None,
                 driver_path=None,
                 ):

        self.driver: uc.Chrome = uc.Chrome(headless=headless,
                                options=options,
                                user_multi_procs=True,
                                version_main=int(120),
                                browser_executable_path=browser_path,
                                driver_executable_path=driver_path)

        self.driver.get("https://www.google.ru")

        time.sleep(random.randint(1, 4))
        self.dismiss_accept_button()

        time.sleep(random.randint(1, 4))
        self.dismiss_notification()
        time.sleep(random.randint(1,4))
        self.dismiss_english_button()

    def retrieve_data(self) -> list[list[str]]:
        collection: list[list[str]] = []
        try:
            source = self.driver.page_source
            soup = bs(source, "html.parser")
            elements = soup.css.select("#rso > div")


            for element in elements:
                inner_text = element.get_text()
                emails = re.findall(r"([a-zA-Z0-9_.+%$-]+@[a-zA-Z0-9_-]+\.com)", inner_text)
                email_one = ""
                if len(emails) != 0:
                    email_one = (emails[0])

                try:
                    data_path = os.path.join(os.getcwd(), "data")
                    os.makedirs(data_path, exist_ok=True)
                    
                    profLink = (element.css.select_one("a[href^='https://']").attrs["href"])

                    title = (element.css.select_one("h3").get_text())
                    title = title.encode("utf-8", "ignore").decode("utf-8")
                    collection.append([title, profLink, email_one])
                    
                except Exception as e:
                    print("skip this")
                    print(e)
        except Exception as e:
            print("Not a search result page!")
            print(e)
        finally:
            return collection

    def dismiss_english_button(self):
        try:
            english_btn = self.driver.find_element("xpath", "//a[text()='English']")
            english_btn.click()
        except:
            print("no english button\n")

    def dismiss_accept_button(self):
        try:
            self.dismiss_notification()
            self.driver.execute_script('''
            document.querySelectorAll("button > div[role='none']")[3].click()
            ''')
        except:
            print("no accept button\n")

    def dismiss_notification(self):
        try:
            self.driver.switch_to.alert.dismiss()
        except:
            print("no location sharing request")

