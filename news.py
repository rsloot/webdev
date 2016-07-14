import blog
import signup
from handler import *
import urllib2
import logging



GOOGLE_NEWS_LOCAL_URL = "https://news.google.com/news?pz=1&cf=all&ned=us&hl=en&geo=%s&output=rss" ## city will suffice for string
GOOGLE_NEWS_TOP = "https://news.google.com/news?pz=1&cf=all&ned=%s&hl=en&output=rss" ## need country code
ESPN_URL = "http://sports.espn.go.com/espn/rss/news"


def heads(topic_url):
        try:
            content = urllib2.urlopen(topic_url, timeout=60)
        except urllib2.URLError, HTTPException:
            return
        d = feedparser.parse(content)
        headlines = [d.entries[i].title for i in range(len(d.entries))]
        links = [d.entries[i].link for i in range(len(d.entries))]
        # logging.error(headlines)
        return headlines, links

def rm_source(hlist):
    for i in range(len(hlist)):
            if hlist[i].rfind('-'):
                dash_loc = hlist[i].rfind('-')
                hlist[i] = hlist[i][:dash_loc]
    return hlist

class news(blog.Handler):
######### TODO: 
######### 		going to need to make ip location call to get country code for 
#########       top news in country!
######### 		and think of other stuff!

    def get(self):
        ip = self.request.remote_addr#"184.119.34.1"#"74.125.74.194"#self.request.remote_addr#"218.107.132.66"#
        # if blog.get_location(ip) is not None:
        if 'tuple' in str(type(blog.get_location(ip))):
            city, state, countryCode = blog.get_location(ip, True)
            city1 = city.replace(" ", "%20")
            cityState = city1+state
            local_url = GOOGLE_NEWS_LOCAL_URL % cityState
            local_id = city + " " +state
            top_url = GOOGLE_NEWS_TOP % countryCode
            country_id = countryCode
        else: ##default to US
            local_url = GOOGLE_NEWS_LOCAL_URL % "us"
            local_id = "US"
            top_url = GOOGLE_NEWS_TOP % "us"
            country_id = "US"
        local_heads, local_links = heads(local_url)
        top_heads, top_links = heads(top_url)
        espn_heads, espn_links = heads(ESPN_URL)

        local_heads = rm_source(local_heads)
        top_heads = rm_source(top_heads)

        self.render("news.html", local_id=local_id, country_id=country_id,
                    local_links=local_links[:7], local_heads=local_heads[:7],
                    top_links=top_links[:7], top_heads=top_heads[:7],
                    espn_links=espn_links[:7], espn_heads=espn_heads[:7])


application = webapp2.WSGIApplication([
    ('/news/?', news),
], debug=True)