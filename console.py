from argparse import ArgumentParser
from console.database.interactions import db_create_table, db_truncate_table, db_insert
import logging
from console.scraper import amazon_scraper

logging.basicConfig(level=logging.INFO,
                    format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s')

def argparser_init() -> ArgumentParser:
    ap = ArgumentParser()
    ap.add_argument('--query', default='laptop')
    ap.add_argument('--pages', type=int, default=5)
    ap.add_argument('--db', default='amazon.db')
    return ap

def run(query: str, pages: int, db: str) -> None:
    db_create_table(db)

    scraper = amazon_scraper(query, pages)
    results = scraper.search_by_keyword()
    if len(results) > 0:
        db_truncate_table(db)
        db_insert(db, results)

def main() -> None:
    parser = argparser_init()
    ns = parser.parse_args()
    run(ns.query, ns.pages, ns.db)

if __name__ == '__console__':
    main()