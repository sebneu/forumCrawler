import argparse
import time
from datetime import datetime, timedelta
from time import mktime
from datetime import datetime


import requests
import sys
from pymongo import MongoClient
import logging
import os
import feedparser
import zlib
import base64

import krone_crawler
import presse_crawler
import derstandard_crawler


def decompress_article(content):
    return zlib.decompress(base64.b64decode(content))


def compress_article(url):
    try:
        resp = requests.get(url)
        if 200 <= resp.status_code < 300:
            data = resp.content
            return base64.b64encode(zlib.compress(data))
    except Exception as e:
        logging.info('Could not access link: ' + url)
    else:
        return None

def get_articles(db, args):
    politeness = args.politeness
    wd = os.path.join(sys.path[0], 'rss_feeds')
    for filename in os.listdir(wd):
        if filename.endswith('.txt'):
            newspaper = filename.split('.txt')[0]
            with open(os.path.join(wd, filename), 'r') as f:
                for url in f:
                    logging.info('RSS feed: ' + url)
                    rss_feed = feedparser.parse(url.strip())
                    logging.info('Total articles: ' + str(len(rss_feed.entries)))

                    i = 0
                    for entry in rss_feed.entries:
                        # if no article with link store content and schedule for crawling db.articles.find({''})
                        # get link without query parameters
                        url = entry.link.split('?')[0]
                        a = db.articles.find_one({'_id': url})
                        if not a:
                            doc = {
                                '_id': url,
                                'content': compress_article(url),
                                'accessed': datetime.now(),
                                'published': datetime.fromtimestamp(mktime(entry.published_parsed)),
                                'summary': entry.summary,
                                'title': entry.title,
                                'newspaper': newspaper,
                                'processed': False
                            }
                            db.articles.insert(doc)
                            i += 1
                            # wait for politeness value
                            time.sleep(politeness)
                    logging.info('Inserted articles: ' + str(i))


def get_comments(db, args):
    with krone_crawler.KroneCrawler() as kc, derstandard_crawler.StandardCrawler() as sc:
        for article in db.articles.find({'processed': False, 'accessed': {'$lte': datetime.now() - timedelta(days=7)}}, {'_id': 1, 'newspaper': 1}):
            postings = []
            if article['newspaper'] == 'krone':
                add_info, postings = kc.get_postings(article['_id'], politeness=args.politeness)
            elif article['newspaper'] == 'presse':
                add_info, postings = presse_crawler.get_postings(article['_id'], politeness=args.politeness)
            elif article['newspaper'] == 'derstandard':
                postings = sc.get_postings(article['_id'], politeness=args.politeness)

            for p in postings:
                try:
                    db.postings.insert_one(p)
                except Exception as e:
                    logging.exception('Error during DB insert of posting: ' + str(e) + ', ' + str(e.message))
            db.articles.update({'_id': article['_id']}, {'$set': {'processed': True}})





if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Crawl and store newspaper articles and comments')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=27017)
    parser.add_argument('--username')
    parser.add_argument('--password')
    parser.add_argument('--logfile')
    parser.add_argument('--loglevel', type=str, default='info')
    parser.add_argument('-p', '--politeness', type=float, default=1)

    subparsers = parser.add_subparsers(help='Load and store articles and comments')
    # create the parser for the "start" command
    parser_articles = subparsers.add_parser('articles', help='Get articles from RSS feeds')
    parser_articles.set_defaults(func=get_articles)

    parser_articles = subparsers.add_parser('comments', help='Get new comments from crawled articles')
    parser_articles.set_defaults(func=get_comments)

    # parse arguments
    args = parser.parse_args()

    if args.loglevel == 'info':
        lvl = logging.INFO
    elif args.loglevel == 'debug':
        lvl = logging.DEBUG
    else:
        lvl = logging.DEBUG
    logging.basicConfig(level=lvl, filename=args.logfile, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    client = MongoClient(args.host, args.port, username=args.username, password=args.password)
    db = client.forumdata
    args.func(db, args)