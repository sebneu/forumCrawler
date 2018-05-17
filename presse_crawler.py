# coding=utf-8
import time
import dateparser
import requests

from bs4 import BeautifulSoup

from derstandard_crawler import Crawler

import logging
import locale
import dateutil.parser

locale.setlocale(locale.LC_ALL, "de_AT.utf8")


def get_article_id(url):
    parts = url.split('/')

    article_id = None
    for p in parts:
        if p.isdigit():
            article_id = p
            break
    return article_id


class PresseCrawler(Crawler):
    def __init__(self):
        Crawler.__init__(self)

    def load_all_postings(self):
        # loadmore = self.browser.find_element_by_class_name("comments")
        more_button = self.browser.find_element_by_class_name('comments__load-btn')
        while (more_button):
            more_button.click()
            more_button = self.browser.find_element_by_class_name('comments__load-btn')

    def get_postings_from_html(self, formatted_result, article_id):
        soup = BeautifulSoup(formatted_result, 'html.parser')
        postinglist = soup.find('div', class_='comments__list')

        prev_level = 0
        prev_comment_id = None
        prev_comments = []
        for posting in postinglist.find_all('div', class_='comment'):
            p = {'article_id': article_id}

            p['_id'] = posting['id']

            p['username'] = posting.find('div', class_='comment__username').get_text().encode('utf-8')
            d = posting.find('div', class_='comment__date')['data-date']
            p['date'] = dateparser.parse(d, languages=['de'])

            text_tag = posting.find('div', class_='comment__body')
            p['text'] = text_tag.get_text().strip().encode('utf-8')

            # ratings
            pos = posting.find('span', class_='comment__vote-count').get_text()
            if not pos:
                pos = '0'
            p['positive'] = int(pos)

            # is repsonse
            layer = posting.find('span', class_='comment__layer')
            resp_level = len(layer.find_all('span', class_='symbol--triangle'))

            if resp_level > prev_level:
                prev_comments.append(prev_comment_id)

            if resp_level < prev_level:
                for i in range(prev_level - resp_level):
                    prev_comments.pop()

            if resp_level > 0:
                p['parent_id'] = prev_comments[-1]

            prev_level = resp_level
            prev_comment_id = p['_id']
            yield p

    def insert_article(self, db, page, politeness):
        articles_collection = db.articles

        article_id = get_article_id(url)

        if not article_id:
            print 'no id found: ', page
            return

        category = page.split('diepresse.com/home/')[-1].split('/')[0]

        if articles_collection.find_one({'_id': article_id}):
            print 'article already stored: ', page
            return

        article = {'_id': article_id, 'url': page}
        try:
            if politeness > 0:
                time.sleep(politeness)
            self.browser.get(page)

            # get article metadata
            a_center = self.browser.find_element_by_class_name('article')
            a_datetime = a_center.find_element_by_class_name('article__byline').find_element_by_class_name(
                'article__timestamp').text.encode('utf-8')
            article['date'] = dateparser.parse(a_datetime, languages=['de'])

            a_title = a_center.find_element_by_class_name('article__headline').text.encode('utf-8').strip()
            article['title'] = a_title
            article['topic'] = category

            # Number of postings. Currently not needed: could change over time, and can be computed from DB
            #count = self.browser.find_element_by_css_selector('#page > div.page__wrapper > div > article > section > div.article__byline > div.badge__commentcount.badge__commentcount--byline > a > span.comments-count')
            #article['postings_count'] = int(count.text)
            articles_collection.insert(article)

        except Exception as e:
            logging.debug('Exception for article: ' + page)
            logging.debug(e)


def get_postings_data(d, postings, parent_id=None, level=0):
    posting = d['_res']

    p = {
        'article_id': str(posting['articleId']),
        '_id': str(posting['commentId']),
        'date': dateutil.parser.parse(posting['creation']),
        'positive': posting['_votings']['up'],
        'level': level
    }

    if 'content' in posting and posting['content']:
        p['text'] = posting['content'].encode('utf-8')
    elif 'title' in posting and posting['title']:
        p['text'] = posting['title'].encode('utf-8')
    else:
        return

    if 'userId' in posting and posting['userId']:
        p['user_id'] = str(posting['userId'])

    if 'metadata' in posting and posting['metadata'] and 'username' in posting['metadata']:
        p['username'] = posting['metadata']['username'].encode('utf-8')

    if parent_id:
        p['parent_id'] = parent_id

    postings.append(p)
    for sub_d in posting['userComments']:
        get_postings_data(sub_d, postings, parent_id=p['_id'], level=level + 1)


def get_postings(url, comments=15, politeness=1):
    try:
        article_id = get_article_id(url)
        a = {'article_id': article_id}
        page = 0

        url = 'https://comment-middleware.getoctopus.com/live/diepresse/contents'
        #base = 'http://localhost:55020/instances/diepresse/contents'
        current = url + '/{0}/comments?page={1}&size={2}'.format(article_id, page, comments)

        resp = requests.get(current)

        if resp.status_code == 200:
            postings = []
            data = resp.json()
            while True:
                if 'contents' in data['_links']:
                    res = data['_links']['contents']
                    if isinstance(res, list):
                        for p in res:
                            get_postings_data(p, postings)
                    elif isinstance(res, dict):
                        get_postings_data(res, postings)
                    else:
                        break
                else:
                    break
                page += 1

                # as long as "last" exists and the current one is not the last one, we are not on the last page
                if data['_links'].get('last') and data['_links']['self']['href'] != data['_links']['last']['href']:
                    current = url + '/{0}/comments?page={1}&size={2}'.format(article_id, page, comments)
                    resp = requests.get(current)
                    data = resp.json()
                else:
                    break

            return a, postings
        else:
            raise Exception(resp.content)
    except Exception as e:
        logging.debug('Exception for article: ' + str(url))
        logging.debug(e)
        return {}, []


def get_links_from_doc(doc='presse_links.txt'):
    idset = set()
    with open(doc) as f:
        for line in f:
            tmp = line.split('diepresse.com/home/')
            if len(tmp) > 1:
                id = tmp[1].strip()
                page = 'https://diepresse.com/home/' + id
                page = page.split('?')[0]
                idset.add(page)
    with open('presse_links_cleaned.txt', 'w') as f:
        for id in idset:
            f.write(id + '\n')


if __name__ == '__main__':
    #c = Crawler()
    # with open('krone_links_cleaned.txt') as f:
    #    for code in f:
    #        c.get_postings(code.strip(), 1)
    # c = Crawler()
    # c.archive_articles()
    get_links_from_doc()
