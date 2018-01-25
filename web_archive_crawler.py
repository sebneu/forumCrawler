# coding=utf-8
import time

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
        #

    def get_articles(self, site):
        waybackMachine = 'https://web.archive.org/web/sitemap/' + site
        self.browser.get(waybackMachine)
        all_links = set()

        time.sleep(150)
        for y in self.iterYears(until='2015'):
            print 'year: ', y
            circle = self.browser.find_element_by_id("d3_container")
            for path in circle.find_elements_by_tag_name('path'):
                try:
                    hover = ActionChains(self.browser).move_to_element(path)
                    hover.perform()
                    el = self.browser.find_element_by_class_name('sequence')
                    link_el = el.find_element_by_tag_name('a')
                    if link_el:
                        text = link_el.get_attribute('href')
                        all_links.add(text)
                        print text
                except Exception:
                    print 'element not displayed'

        return all_links



if __name__ == '__main__':
    #c = Crawler()
    #with open('presse_links_cleaned.txt') as f:
    #    for code in f:
    #        c.get_postings(code.strip(), 1)
    # http://www.krone.at/
    c = Crawler()
    articles = c.get_articles(site='https://diepresse.com/home/')
    with open('presse_links.txt', 'w') as f:
        for l in articles:
            f.write(l)
            f.write('\n')
