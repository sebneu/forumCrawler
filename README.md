# forumCrawler

## Setup
The crawler uses [Selenium](http://selenium-python.readthedocs.io/) to get the website's data. Currently it uses Google Chrome; the required driver is already in the project directory.  

* `$ git clone git@github.com:sebneu/forumCrawler.git`
* `$ cd forumCrawler`
* (optionally) setup virtual environment
* `$ virtualenv --system-site-packages forumCrawler_env`
* `$ . forumCrawler_env/bin/activate`
* Install requirements 
* `$ python setup.py install`
* Restore DB dump (running MongoDB instance required)
* `$ cat db_dump/db_* | tar xzvf - -C db_dump`
* `$ mongorestore --db derstandardat db_dump/derstandardat`
* Run crawler
* `$ python ./main.py articles --start 2016-01-01 --end 2016-01-02`  to store articles in given timespan
* `$ python ./main.py postings --start 2016-01-01 --end 2016-01-02`  to store postings in given timespan
