import dataset
import selenium
db = None
driver: selenium.webdriver.Chrome = None
class Scraper:
    def __init__(self, url: str, css_selector: str, interval: int):
        self.url = url
        self.css_selector = css_selector
        self.interval = interval
        self._last_scrape = None
    def scrape_website(self):
        """
        Scrape the website
        """
        