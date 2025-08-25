from argparse import ArgumentParser
from database.interactions import db_create_table, db_truncate_table, db_insert
from fake_useragent import FakeUserAgent
import logging
from scraper import AmazonScraper

logging.basicConfig(level=logging.INFO,
                    format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s')

def argparser_init() -> ArgumentParser:
    ap = ArgumentParser()
    ap.add_argument('--query', default='laptop')
    ap.add_argument('--pages', type=int, default=5)
    ap.add_argument('--db', default='amazon.db')
    return ap

def main(query: str, pages: int, db: str) -> None:
    db_create_table(db)

    user_agent = FakeUserAgent(platforms='desktop').random
    scraper = AmazonScraper(query, pages, user_agent)
    results = scraper.search_by_keyword()
    if len(results) > 0:
        db_truncate_table(db)
        db_insert(db, results)

if __name__ == '__main__':
    parser = argparser_init()
    ns = parser.parse_args()
    main(ns.query, ns.pages, ns.db)