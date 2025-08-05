from decimal import Decimal
import logging
from random import choice, uniform
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import WebDriverWait
import time
from typing import Any, Optional

BASE_URL = 'https://amazon.com'

class amazon_scraper:
    driver: Any
    products: list[Any]
    keyword: str
    pages: int

    def __init__(self, query: str, max_pages: int) -> None:
        self.driver = self._setup_driver()
        self.products = []
        self.keyword = query
        self.pages = max_pages
    
    def _setup_driver(self):
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        options.add_argument(f'--user-agent={choice(user_agents)}')

        # Вимкнення зображень (для прискорення)
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

        return webdriver.Chrome(options=options)
    
    def _random_delay(self) -> None:
        delay = uniform(1, 3)
        time.sleep(delay)

    def _get_title_and_url(self, container: WebElement) -> tuple[str, str]:
        title = container.find_element(By.CSS_SELECTOR, 'a > h2 > span')
        link = title.find_element(By.XPATH, 'ancestor::a').get_attribute('href')
        assert link is not None
        return (title.text.strip(), link)
    
    def _get_rating(self, container: WebElement) -> Optional[float]:
        try:
            rating = container.find_element(By.CSS_SELECTOR,
                                            "[data-cy='reviews-ratings-slot'] > span").get_attribute('innerHTML')
            return float(rating.split()[0]) if rating and len(rating) > 0 else None
        except NoSuchElementException:
            return None
        
    def _get_reviews(self, container: WebElement) -> int:
        try:
            reviews = container.find_element(By.CSS_SELECTOR,
                                            "[data-csa-c-slot-id='alf-reviews'] span").get_attribute('innerHTML')
            return int(reviews.replace(',', '')) if reviews and len(reviews) > 0 else 0
        except NoSuchElementException:
            return 0
        
    def _get_prices(self, container: WebElement) -> tuple[int, int]:
        # Є дві ціни: current price та original price
        try:
            price = container.find_element(By.CSS_SELECTOR, ".a-price:not([data-a-strike = 'true']) > .a-offscreen").get_attribute('innerHTML')
        except NoSuchElementException:
            price = '-1'
        try:
            original_price = container.find_element(By.CSS_SELECTOR, ".a-price[data-a-strike = 'true'] > .a-offscreen").get_attribute('innerHTML')
        except NoSuchElementException:
            original_price = price
        if price == '-1':
            # Є лише одна ціна (зокрема, якщо локацією обрати Україну)
            try:
                price = container.find_element(By.CSS_SELECTOR, "[data-cy='secondary-offer-recipe'] .a-color-base").get_attribute('innerHTML')
            except NoSuchElementException:
                price = '-1'
            original_price = price
        assert price and original_price
        # Ціна в центах, щоб можна було використовувати тип даних int
        price_dec = int(Decimal(re.sub(r'[^0-9\.\-]', '', price)) * 100)
        original_price_dec = int(Decimal(re.sub(r'[^0-9\.\-]', '', original_price)) * 100)
        return (price_dec, original_price_dec)
    
    def _get_delivery(self, container: WebElement) -> bool:
        try:
            delivery = container.find_element(By.CSS_SELECTOR, '.udm-primary-delivery-message > div').get_attribute('innerHTML')
            return delivery != ''
        except NoSuchElementException:
            return False

    def _extract_data(self, container: WebElement) -> dict[str, Any]:
        product = {}
        try:
            product['title'], product['url'] = self._get_title_and_url(container)
            product['rating'] = self._get_rating(container)
            product['reviews'] = self._get_reviews(container)
            prices = self._get_prices(container)
            product['current_price'] = prices[0] if prices[0] >= 0 else None
            product['original_price'] = prices[1] if prices[1] >= 0 else product['current_price']
            product['delivery_available'] = self._get_delivery(container)

        except Exception as e:
            logging.error(f'Помилка під час пошуку даних: {e}')
        finally:
            return product

    def _scrape_page(self) -> None:
        self._random_delay()
        try:
            container = WebDriverWait(self.driver, 10).until(
                conditions.visibility_of_element_located(
                    (By.CSS_SELECTOR, "[data-component-type='s-search-results']")))
            cards = container.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
            products_data = [self._extract_data(card) for card in cards]
            self.products += [item for item in products_data if item]
        except TimeoutException:
            logging.error('Не вдалося завантажити результати пошуку')
        except Exception as e:
            logging.error(f'Помилка під час пошуку даних: {e}')
    
    def _next_page(self) -> bool:
        try:
            btn_next = WebDriverWait(self.driver, 10).until(
                conditions.presence_of_element_located((By.CSS_SELECTOR, 'a.s-pagination-next')))
            btn_class = btn_next.get_attribute('class')
            assert btn_class is not None
            if 's-pagination-disabled' in btn_class:
                return False
            btn_next.click()
            return True
        except NoSuchElementException:
            return False

    def search_by_keyword(self) -> list[dict[str, Any]]:
        try:
            self.driver.get(BASE_URL)
            self._random_delay()

            # Пошук за ключовим словом
            input_search = WebDriverWait(self.driver, 10).until(
                conditions.presence_of_element_located((By.ID, 'twotabsearchtextbox')))
            input_search.clear()
            input_search.send_keys(self.keyword)
            btn_submit = WebDriverWait(self.driver, 10).until(
                conditions.element_to_be_clickable((By.ID, 'nav-search-submit-text')))
            btn_submit.click()
            self._random_delay()

            # Скрапінг даних з кожної сторінки
            for page in range(1, self.pages+1):
                self._scrape_page()
                if page == self.pages or not self._next_page():
                    break

        except Exception as e:
            logging.error(f'Помилка під час пошуку даних: {e}')
            self.products.clear()
        finally:

            return self.products
