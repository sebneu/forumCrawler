##################################################################################################
#Imported packages need to be installed first
##################################################################################################
library(mongolite)
##################################################################################################

##################################################################################################
# IMPORTING DATA FROM RUNNING MONGO-DB with the package mongolite
##################################################################################################
# newspaper 1 - derStandard
np1postings <- mongo(collection = "postings", db = "derstandardat", url = "mongodb://localhost",
            verbose = FALSE, options = ssl_options())
np1articles <- mongo(collection = "articles", db = "derstandardat", url = "mongodb://localhost",
             verbose = FALSE, options = ssl_options())
##################################################################################################
# newspaper 2 - krone
np2postings <- mongo(collection = "postings", db = "krone", url = "mongodb://localhost",
             verbose = FALSE, options = ssl_options())

np2articles <- mongo(collection = "articles", db = "krone", url = "mongodb://localhost",
              verbose = FALSE, options = ssl_options())
##################################################################################################
# newspaper 2 only 2016/2017
np2postingsNew <- mongo(collection = "postingsnew", db = "krone", url = "mongodb://localhost",
                verbose = FALSE, options = ssl_options())
np2articlesNew <- mongo(collection = "articlesnew", db = "krone", url = "mongodb://localhost",
                 verbose = FALSE, options = ssl_options())
##################################################################################################
# newspaper 3 - diePresse
np3postings <- mongo(collection = "postings", db = "diepresse", url = "mongodb://localhost",
             verbose = FALSE, options = ssl_options())
#presse articles
np3articles <- mongo(collection = "articles", db = "diepresse", url = "mongodb://localhost",
              verbose = FALSE, options = ssl_options())
##################################################################################################
## newspaper 3 only 2016/2017
np3postingsNew <- mongo(collection = "postingsnew", db = "diepresse", url = "mongodb://localhost",
                verbose = FALSE, options = ssl_options())
np3articlesNew <- mongo(collection = "articlesnew", db = "diepresse", url = "mongodb://localhost",
                 verbose = FALSE, options = ssl_options())
##################################################################################################

##################################################################################################
# DATA STATISTICS - Newspaper 1 - for other newspaper change number in variable name
##################################################################################################
# postings per user = ppu
ppu <- np1postings$aggregate('[{"$group" :{"_id" : "$username", "total" : { "$sum" : 1 }}}]')
plot(table(ppu[2]), main = "Postings per User", ylab = "Users", xlab= "Postings", type ="p", log="x")
# 10 most active users
head(ppu[order(ppu$total, decreasing=TRUE),],10)
##################################################################################################
# articles per topic = apt
apt <- np1articles$aggregate('[{"$group" :{"_id" : "$topic", "total" : { "$sum" : 1 }}}]')
plot(table(apt[2]), main = "Articles per Topic", ylab = "Topics", xlab= "Articles", type ="p")
# top 10 topics
head(apt[order(apt$total, decreasing=TRUE),],10)
##################################################################################################
# postings per topic new #ppa=postins per article
ppa <- np1postings$aggregate('[ {"$group" :{"_id" : "$article_id", "total" : { "$sum" : 1 }}} ]') 
# 10 articles with most postings
head(ppa[order(ppa$total, decreasing=TRUE),],10)
# id and topic from article = idTopic
idTopic <- np1articles$find(fields='{"topic":true}')
# postings per topic = ppt
ppt <- merge(ppa,idTopic,all.x=TRUE)
ppt[is.na(ppt)] <- 0
topicPosts <- aggregate(total ~ topic,ppt,sum)
# 10 topics with most postings
head(topicPosts[order(topicPosts$total, decreasing=TRUE),],10)
##################################################################################################
# Level graph - shows distribution of the level variable
level <- np1postings$find(  '{"level":{"$gt": -1}}'  , fields =    '{"level":1}')
levelLog <- table(level[2]+1)
plot(levelLog, main = "Level distribution", ylab = "Postings", xlab= "Level", type="l",log="x", xaxt="n")
# for x axis we need custom labels to work with log scale
# for newspaper 3 u can use: axis(1, at=c(1:16),labels=c(0:15), las=2)
axis(1, at=c(1:60),labels=c(0:59), las=1)
##################################################################################################
# same username over multiple datasets 
# get all distinct usernames
eins <- np1postings$   distinct("username")
zwei <- np2postingsNew$distinct("username") 
drei <- np3postingsNew$distinct("username")
# intersect searches for same names
intersect(intersect(eins,zwei),drei)
intersect(eins, zwei)
intersect(eins, drei)
intersect(drei, zwei)
##################################################################################################
##################################################################################################

