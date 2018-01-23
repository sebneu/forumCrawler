import argparse
import logging
import time
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

import derstandard_crawler
import krone_crawler
import presse_crawler


def store_articles(client, args):
    start = datetime.strptime(args.start, '%Y-%m-%d')
    end = datetime.strptime(args.end, '%Y-%m-%d')

    db = client.derstandardat
    articles_collection = db.articles

    with derstandard_crawler.Crawler() as crawler:
        iter_articles = crawler.archive_articles(start, end, args.politeness)
        for day_articles in iter_articles:
            try:
                articles_collection.insert_many(day_articles, ordered=False)
            except BulkWriteError as bwe:
                werrors = bwe.details['writeErrors']
                logging.warning('Inserting errors: ' + str(werrors))

        logging.info('Articles in MongoDB: ' + str(articles_collection.count()))


def get_std_postings_to_articles(client, args, check_if_in_db=True):
    db = client.derstandardat
    articles_collection = db.articles
    postings_collection = db.postings
    if args.start and args.end:
        start = datetime.strptime(args.start, '%Y-%m-%d')
        end = datetime.strptime(args.end, '%Y-%m-%d')
        iter = articles_collection.find({'date': {'$gt': start, '$lt': end}})
    else:
        iter = articles_collection.find()

    i = 0
    with derstandard_crawler.Crawler() as crawler:
        for i, article in enumerate(iter):
            a_postings = 0
            if check_if_in_db:
                a_postings = postings_collection.find({'article_id': article['_id']}).count()
            if a_postings <= 0:
                postings = crawler.get_postings(article['_id'], args.politeness)
                if postings:
                    try:
                        postings_collection.insert_many(postings, ordered=False)
                    except BulkWriteError as bwe:
                        werrors = bwe.details['writeErrors']
                        logging.warning('Inserting errors: ' + str(werrors))
            else:
                logging.debug('Article already processed: ' + article['url'])
            if i % 100 == 0:
                logging.info('Processed articles: ' + str(i))

    logging.info('Processed articles: ' + str(i))
    logging.info('Postings in MongoDB: ' + str(postings_collection.count()))


def get_krone_postings_to_articles(client, args):
    db = client.krone

    ids_file = args.article_ids
    with krone_crawler.Crawler() as c:
        with open(ids_file) as f:
            for code in f:
                c.get_postings(db, code.strip(), politeness=1)


def insert_presse_articles(client, args):
    db = client.diepresse

    ids_file = args.article_ids
    with presse_crawler.Crawler() as c:
        with open(ids_file) as f:
            for page in f:
                c.insert_article(db, page.strip(), politeness=0.5)


def get_presse_postings_to_articles(client, args):
    db = client.diepresse
    articles_collection = db.articles
    postings_collection = db.postings

    iter = articles_collection.find()
    for i, article in enumerate(iter):

        if args.politeness > 0:
            time.sleep(args.politeness)
        postings = presse_crawler.get_postings(article['_id'])
        if postings:
            try:
                postings_collection.insert_many(postings, ordered=False)
            except BulkWriteError as bwe:
                werrors = bwe.details['writeErrors']
                logging.warning('Inserting errors: ' + str(werrors))

        if i % 100 == 0:
            logging.info('Processed articles: ' + str(i))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='User comments extraction from newspaper forums')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=27017)
    filename = datetime.now().strftime('%Y-%m-%d') + '.log'
    parser.add_argument('--logfile', default=filename)
    parser.add_argument('--loglevel', type=str, default='info')
    parser.add_argument('-p', '--politeness', type=float, default=1)

    subparsers = parser.add_subparsers(help='Web scraping tools for articles and postings on derStandard.at')
    # create the parser for the "start" command
    parser_articles = subparsers.add_parser('std-articles', help='extract article URLs and titles from archive pages')
    parser_articles.add_argument('--start', help='start date: yyyy-mm-dd')
    parser_articles.add_argument('--end', help='end date: yyyy-mm-dd')
    parser_articles.set_defaults(func=store_articles)

    # create the parser for the "std-postings" command
    parser_postings = subparsers.add_parser('std-postings', help='extract postings from articles in MongoDB database')
    parser_postings.add_argument('--start', help='start date: yyyy-mm-dd')
    parser_postings.add_argument('--end', help='end date: yyyy-mm-dd')
    parser_postings.set_defaults(func=get_std_postings_to_articles)


    # create the parser for the "krone-postings" command
    parser_postings = subparsers.add_parser('krone-postings', help='extract postings from articles in MongoDB database')
    parser_postings.add_argument('--article-ids', default='krone_links_cleaned.txt')
    parser_postings.set_defaults(func=get_krone_postings_to_articles)

    # create the parser for the "presse-articles" command
    parser_postings = subparsers.add_parser('presse-articles', help='insert articles for diePresse.com')
    parser_postings.add_argument('--article-ids', default='presse_links_cleaned.txt')
    parser_postings.set_defaults(func=insert_presse_articles)

    # create the parser for the "presse-postings" command
    parser_postings = subparsers.add_parser('presse-postings', help='extract postings from Presse articles')
    parser_postings.set_defaults(func=get_presse_postings_to_articles)

    # parse arguments
    args = parser.parse_args()


    if args.loglevel == 'info':
        lvl = logging.INFO
    elif args.loglevel == 'debug':
        lvl = logging.DEBUG
    else:
        lvl = logging.DEBUG
    logging.basicConfig(level=lvl, filename=args.logfile, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    client = MongoClient(args.host, args.port)
    args.func(client, args)