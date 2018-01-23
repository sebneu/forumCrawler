# coding=utf-8
import time
import dateparser

from bs4 import BeautifulSoup

from selenium import webdriver
import logging
import locale
locale.setlocale(locale.LC_ALL, "de_AT.utf8")


class Crawler:
    def __init__(self):
        self.browser = webdriver.Chrome('./chromedriver')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.quit()

    def load_more_postings(self):
        loadmore = self.browser.find_element_by_id("comment-list")
        more_button = loadmore.find_element_by_class_name('next')
        self.browser.execute_script("arguments[0].click();", more_button)

        selected_page = loadmore.find_element_by_class_name("selected").text
        page_number = loadmore.find_element_by_class_name("commentList__maxCount").text.split(' ')[1]
        if selected_page != page_number:
            return True
        else:
            return False


    def get_postings_from_html(self, formatted_result, article_id):
        soup = BeautifulSoup(formatted_result, 'html.parser')
        postinglist = soup.find('div', id='comment-list')

        for posting in postinglist.find_all('div', class_='c_comment'):
            p = {'article_id': article_id}
            p['username'] = posting.find('div', class_='c_name').get_text().encode('utf-8')
            d = posting.find('div', class_='c_datetime').get_text().strip().encode('utf-8').split(', ')[1].replace('Jänner', 'Januar')
            p['date'] = dateparser.parse(d, languages=['de'])

            text_tag = posting.find('p')
            p['text'] = text_tag.get_text().encode('utf-8')

            # ratings
            pos = posting.find('div', class_='c_up').find('span', class_='c_count').get_text()
            if not pos:
                pos = '0'
            p['positive'] = int(pos)
            neg = posting.find('div', class_='c_down').find('span', class_='c_count').get_text()
            if not neg:
                neg = '0'
            p['negative'] = int(neg)

            yield p


    def get_postings(self, db, article_id, politeness):
        articles_collection = db.articles
        postings_collection = db.postings

        page = 'http://www.krone.at/' + article_id
        article = {'_id': article_id, 'url': page}
        try:
            if politeness > 0:
                time.sleep(politeness)
            self.browser.get(page)

            # get article metadata
            a_center = self.browser.find_element_by_class_name('col-xs-8')
            a_datetime = a_center.find_element_by_class_name('c_pretitle').find_element_by_class_name('c_time').text.encode('utf-8')
            article['date'] = dateparser.parse(a_datetime, languages=['de'])

            a_title = a_center.find_element_by_class_name('c_title').find_element_by_tag_name('h1').text.encode('utf-8').strip()
            article['title'] = a_title

            a_topic = self.browser.find_element_by_class_name('c_active').find_element_by_tag_name('a').get_attribute('href').strip()
            article['topic'] = a_topic

            articles_collection.insert(article)

            postings = []
            for p in self.get_postings_from_html(self.browser.page_source, article_id):
                postings.append(p)

            while self.load_more_postings():
                for p in self.get_postings_from_html(self.browser.page_source, article_id):
                    postings.append(p)

            postings_collection.insert_many(postings)
        except Exception as e:
            logging.debug('Exception for article: ' + page)
            logging.debug(e)


def get_links_from_doc(doc='krone_links.txt'):
    idset = set()
    with open(doc) as f:
        for line in f:
            id = line.split('www.krone.at/')[1].strip()
            if id.isdigit():
                idset.add(id)
    with open('krone_links_cleaned.txt', 'w') as f:
        for id in idset:
            f.write(id + '\n')


if __name__ == '__main__':
    c = Crawler()
    #with open('krone_links_cleaned.txt') as f:
    #    for code in f:
    #        c.get_postings(code.strip(), 1)
    #c = Crawler()
    #c.archive_articles()
    c.get_postings(None, "1611934", politeness=1)
