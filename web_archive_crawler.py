# coding=utf-8
import time

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains



class Crawler:
    def __init__(self):
        self.browser = webdriver.Chrome('./chromedriver')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.quit()

    def iterYears(self, until):
        years = self.browser.find_element_by_class_name("div-btn")
        buttons = years.find_elements_by_class_name('year-btn')
        for b in reversed(buttons):
            b.click()
            time.sleep(30)
            yield b.text
            if b.text == until:
                break
        yield until


    def get_urls_from_html(self, formatted_result):
        soup = BeautifulSoup(formatted_result, 'html.parser')
        circle = soup.find('g', id='d3_container')
        res = set()
        for link in circle.find_all('a'):
            if link.has_attr('xlink:href'):
                res.add(link['xlink:href'])
            elif link.has_attr('href'):
                res.add(link['href'])
        return res

    def get_articles(self, site):
        waybackMachine = 'https://web.archive.org/web/sitemap/' + site
        self.browser.get(waybackMachine)
        all_links = set()
        time.sleep(150)

        years_iter = self.iterYears(until='2015')
        for y in years_iter:
            print 'year: ', y
            all_links |= self.get_urls_from_html(self.browser.page_source)
            #circle = self.browser.find_element_by_id("d3_container")
            #for path in circle.find_elements_by_tag_name('a'):
                #try:
                    #hover = ActionChains(self.browser).move_to_element(path)
                    #hover.perform()
                    #el = self.browser.find_element_by_class_name('sequence')
                    #link_el = el.find_element_by_tag_name('a')
                    #if link_el:
                    #    text = link_el.get_attribute('href')
                    #    all_links.add(text)
                    #    print text
                #except Exception:
                #    print 'element not displayed'

        return all_links



if __name__ == '__main__':
    #c = Crawler()
    #with open('presse_links_cleaned.txt') as f:
    #    for code in f:
    #        c.get_postings(code.strip(), 1)
    #
    c = Crawler()
    articles = c.get_articles(site='http://www.krone.at/')
    with open('krone_links.txt', 'w') as f:
        for l in articles:
            f.write(l)
            f.write('\n')
