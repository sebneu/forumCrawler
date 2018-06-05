import time
from dateutil import rrule
from datetime import datetime

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import sys

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

import logging
import locale
locale.setlocale(locale.LC_ALL, "de_AT.utf8")


class Crawler:
    def __init__(self):
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_driver = os.path.join(sys.path[0], 'chromedriver')

        self.browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.quit()


class StandardCrawler(Crawler):
    def __init__(self):
        Crawler.__init__(self)

    def load_more_postings(self):
        def _get_more_button():
            loadmore = self.browser.find_element_by_class_name("forum-loadmore")
            more_button = loadmore.find_element_by_class_name('forum-tb-navi')
            self.browser.execute_script("arguments[0].click();", more_button)
            return True

        try:
            return _get_more_button()
        except NoSuchElementException as e:
            return False
        except StaleElementReferenceException as e:
            logging.debug("Exception in finding date")
            logging.debug(e)
            time.sleep(2)
            return _get_more_button()

    def get_postings_from_html(self, formatted_result, url):
        soup = BeautifulSoup(formatted_result, 'html.parser')

        postinglist = soup.find('div', id='postinglist')
        if not postinglist:
            raise Exception('')

        for posting in postinglist.find_all('div', class_='posting'):
            p = {'article_id': url, 'newspaper': 'derstandard'}
            if posting.has_attr('data-communityname') and posting['data-communityname']:
                p['username'] = posting['data-communityname'].encode('utf-8')

            if posting.has_attr('data-communityidentityid') and posting['data-communityidentityid']:
                p['user_id'] = posting['data-communityidentityid']

            if posting.has_attr('data-postingid') and posting['data-postingid']:
                p['_id'] = posting['data-postingid']

            if posting.has_attr('data-parentpostingid') and posting['data-parentpostingid']:
                p['parent_id'] = posting['data-parentpostingid']

            if posting.has_attr('data-level') and posting['data-level']:
                p['level'] = int(posting['data-level'])

            text_tag = posting.find('div', class_='upost-text')
            if text_tag:
                p['text'] = text_tag.get_text().encode('utf-8')
            title_tag = posting.find('h4', class_='upost-title')
            if title_tag:
                tmp = title_tag.get_text()
                if tmp:
                    p['title'] = title_tag.get_text().encode('utf-8')
            if 'text' not in p and 'title' not in p:
                # if no text we ignore the posting
                continue

            date_tag = posting.find('span', class_='js-timestamp')
            if date_tag.has_attr('data-date'):
                d = date_tag['data-date']
            else:
                d = date_tag.get_text()
            d = d.encode('utf-8')
            p['date'] = datetime.strptime(d, '%d. %B %Y, %H:%M:%S')
            # ratings
            p['positive'] = int(posting.find('span', class_='ratings-positive-count').get_text())
            p['negative'] = int(posting.find('span', class_='ratings-negative-count').get_text())

            yield p

    def get_postings(self, url, politeness):
        try:
            if politeness > 0:
                time.sleep(politeness)

            self.browser.get(url)

            privacy_button = self.browser.find_element_by_class_name('privacy-button')
            if privacy_button:
                self.browser.execute_script("arguments[0].click();", privacy_button)

            postings = {}
            for p in self.get_postings_from_html(self.browser.page_source, url):
                postings[p['_id']] = p

            while self.load_more_postings():
                for p in self.get_postings_from_html(self.browser.page_source, url):
                    postings[p['_id']] = p

            return postings.values()
        except Exception as e:
            logging.debug('Exception for article: ' + str(url))
            logging.debug(e)
            return []

    def article_links(self, formatted_result):
        soup = BeautifulSoup(formatted_result, 'html.parser')
        articles = []
        articlelist = soup.find('ul', id='resultlist')
        for article in articlelist.find_all('li'):
            if article.has_key('class') and 'ad-std' in article['class']:
                continue
            a = {}
            d = article.find('div', class_='date')
            d = d.get_text()
            d = ' '.join(d.split())
            a['date'] = datetime.strptime(d, '%d.%m.%Y %H:%M')
            text = article.find('div', class_='text')
            a['title'] = text.find('h3').find('a').get_text()
            a['url'] = text.find('h3').find('a')['href']
            a['topic'] = text.find('h6').find('a')['href']
            # extract ID
            a['_id'] = a['url'].split('/')[1]
            articles.append(a)
        return articles

    def archive_articles(self, start, end, politeness):
        month_count = 0
        for dt in rrule.rrule(rrule.DAILY, dtstart=start, until=end):
            if month_count != dt.month:
                month_count = dt.month
                logging.info('Crawling archive articles month ' + str(dt.month) + ', year ' + str(dt.year))

            archive_page = 'https://derstandard.at/archiv/' + str(dt.year) + '/' + str(dt.month) + '/' + str(dt.day)
            try:
                if politeness > 0:
                    time.sleep(politeness)

                self.browser.get(archive_page)
                day_articles = self.article_links(self.browser.page_source)
                yield day_articles
            except Exception as e:
                logging.debug('Exception for archive page: ' + archive_page)
                logging.debug(e)

