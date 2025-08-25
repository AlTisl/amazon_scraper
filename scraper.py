from decimal import Decimal
import logging
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import WebDriverWait
from typing import Any
from utilities import random_delay

BASE_URL = 'https://amazon.com'

locators = {
    'keyword_input': 'twotabsearchtextbox',
    'keyword_submit': 'nav-search-submit-text',
    'next_page_link': 'a.s-pagination-next',
    'search_results': "[data-component-type='s-search-results']",
    'search_item': "[data-component-type='s-search-result']",
    'item_title': 'a > h2 > span',
    'item_url': 'ancestor::a',
    'item_rating': "[data-cy='reviews-ratings-slot'] > span",
    'item_reviews': "[data-csa-c-slot-id='alf-reviews'] span",
    'item_price': [".a-price:not([data-a-strike = 'true']) > .a-offscreen",
                "[data-cy='secondary-offer-recipe'] .a-color-base"],
    'item_original_price': ".a-price[data-a-strike = 'true'] > .a-offscreen",
    'item_delivery': '.udm-primary-delivery-message > div'
}

class AmazonScraper:
    _driver: Any
    _products: list[Any]
    _keyword: str
    _pages: int

    def __init__(self, query: str, max_pages: int, user_agent: str) -> None:
        self._driver = self._setup_driver(user_agent)
        self._products = []
        self._keyword = query
        self._pages = max_pages
        
    
    def _setup_driver(self, agent: str):
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--headless')
        options.add_argument(f'--user-agent={agent}')

        # Вимкнення зображень (для прискорення)
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

        return webdriver.Chrome(options=options)

    def _get_title_and_url(self, container: WebElement) -> tuple[str, str]:
        title = container.find_element(By.CSS_SELECTOR, locators['item_title'])
        link = title.find_element(By.XPATH, locators['item_url']).get_attribute('href')
        assert link is not None
        return (title.text.strip(), link)
    
    def _get_rating(self, container: WebElement) -> float|None:
        try:
            rating = container.find_element(By.CSS_SELECTOR,
                                            locators['item_rating']).get_attribute('innerHTML')
            return float(rating.split()[0]) if rating and len(rating) > 0 else None
        except NoSuchElementException:
            return None
        
    def _get_reviews(self, container: WebElement) -> int:
        try:
            reviews = container.find_element(By.CSS_SELECTOR,
                                            locators['item_reviews']).get_attribute('innerHTML')
            return int(reviews.replace(',', '')) if reviews and len(reviews) > 0 else 0
        except NoSuchElementException:
            return 0
        
    def _get_prices(self, container: WebElement) -> tuple[int, int]:
        # Є дві ціни: current price та original price
        try:
            price = container.find_element(By.CSS_SELECTOR, locators['item_price'][0]).get_attribute('innerHTML')
        except NoSuchElementException:
            price = '-1'
        try:
            original_price = container.find_element(By.CSS_SELECTOR, locators['item_original_price']).get_attribute('innerHTML')
        except NoSuchElementException:
            original_price = price
        if price == '-1':
            # Є лише одна ціна (зокрема, якщо локацією обрати Україну)
            try:
                price = container.find_element(By.CSS_SELECTOR, locators['item_price'][1]).get_attribute('innerHTML')
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
            delivery = container.find_element(By.CSS_SELECTOR, locators['item_delivery']).get_attribute('innerHTML')
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
        random_delay(1, 3)
        try:
            container = WebDriverWait(self._driver, 10).until(
                conditions.visibility_of_element_located(
                    (By.CSS_SELECTOR, locators['search_results'])))
            cards = container.find_elements(By.CSS_SELECTOR, locators['search_item'])
            products_data = [self._extract_data(card) for card in cards]
            self._products += [item for item in products_data if item]
        except TimeoutException:
            logging.error('Не вдалося завантажити результати пошуку')
        except Exception as e:
            logging.error(f'Помилка під час пошуку даних: {e}')
    
    def _next_page(self) -> bool:
        try:
            btn_next = WebDriverWait(self._driver, 10).until(
                conditions.presence_of_element_located((By.CSS_SELECTOR, locators['next_page_link'])))
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
            self._driver.get(BASE_URL)
            random_delay(1, 3)

            # Пошук за ключовим словом
            input_search = WebDriverWait(self._driver, 10).until(
                conditions.presence_of_element_located((By.ID, locators['keyword_input'])))
            input_search.clear()
            input_search.send_keys(self._keyword)
            btn_submit = WebDriverWait(self._driver, 10).until(
                conditions.element_to_be_clickable((By.ID, locators['keyword_submit'])))
            btn_submit.click()
            random_delay(1, 3)

            # Скрапінг даних з кожної сторінки
            for page in range(1, self._pages+1):
                self._scrape_page()
                if page == self._pages or not self._next_page():
                    break

        except Exception as e:
            logging.error(f'Помилка під час пошуку даних: {e}')
            self._products.clear()
        finally:
            self._driver.quit()
            return self._products

