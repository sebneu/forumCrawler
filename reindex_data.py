import argparse
import logging
from pymongo import MongoClient
import time

from article_scheduler import compress_article


def reindex(client, oldclient, politeness):
    db = client.forumdata

    for newspaper, olddb in [('derstandard', oldclient.derstandardat), ('krone', oldclient.krone), ('presse', oldclient.diepresse)]:
        for a in olddb.articles.find():
            url = a['url'].split('?')[0]
            if newspaper == 'derstandard':
                url = 'https://derstandard.at' + url
            doc = {
                '_id': url,
                'content': compress_article(url),
                'published': a['date'],
                'title': a['title'],
                'newspaper': newspaper,
                'processed': True
            }
            if not db.articles.find({'_id': doc['_id']}):
                db.articles.insert(doc)

            postings = []
            for p in olddb.postings.find({'article_id': a['_id']}):
                p['article_id'] = url
                p['newspaper'] = newspaper
                postings.append(p)
            if postings:
                try:
                    db.postings.insert_many(postings, ordered=False)
                except Exception as e:
                    logging.info('Error while inserting postings: ' + str(e))

            time.sleep(politeness)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Store old data in new schema')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=27017)
    parser.add_argument('--oldhost', default='localhost')
    parser.add_argument('--oldport', type=int, default=27018)
    parser.add_argument('--username')
    parser.add_argument('--password')
    parser.add_argument('--logfile')
    parser.add_argument('--loglevel', type=str, default='debug')
    parser.add_argument('-p', '--politeness', type=float, default=1)

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
    oldclient = MongoClient(args.oldhost, args.oldport)

    reindex(client, oldclient, args.politeness)