from handler import *
from secrets import *
import signup
import re
from datetime import datetime, timedelta
import urllib2
import logging

from xml.dom import minidom


global newPost
newPost = False


def age_set(key, value):
    save_time = datetime.utcnow()
    memcache.set(key, (value, save_time))

def age_get(key):
    r = memcache.get(key)
    if r:
        val, save_time = r
        age = (datetime.utcnow() - save_time).total_seconds()
    else:
        val, age = None, 0

    return val, age

def add_post(ip, post):
    post.put()
    get_posts(update = True)
    return str(post.key().id())

def get_posts(update = False):
    # key = 'po'
    # posts = memcache.get(key)
    mc_key = 'BLOGS'

    posts, age = age_get(mc_key)
    if posts is None or update:
        q = BlogPost.all().order('-created').fetch(limit = 10)
        posts = list(q)
        age_set(mc_key, posts)

    return posts, age

# last time the page was queried (x seconds ago)
def age_str(age):
    s = 'queried %s seconds ago'
    age = int(age)
    if age == 1:
        s = s.replace('seconds', 'second')
    return s % age

# db class for all blogposts
class BlogPost(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    creator = db.StringProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    permalink = db.StringProperty(required = False)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)
    
    def as_dict(self):
        time_fmt = '%c'
        d = {'subject': self.subject,
             'content': self.content,
             'creator': self.creator,
             'created': self.created.strftime(time_fmt),
             'last_modified': self.last_modified.strftime(time_fmt),
             'permalink': self.permalink}
        return d

class MainPage(signup.Handler, Handler):
##    def render_front(self, posts=""):
##        self.render("blog_front.html", posts=posts)
    
    def get(self):
        # update query if new posts don't otherwise
        if not newPost:
            posts, age = get_posts()
        else:
            posts, age = get_posts(update = True)
            global newPost
            newPost = False
        # get ip/coords for openweathermap api 
        # return current temp according to city name recieved from hostip api
        ip = self.request.remote_addr#"74.125.74.194"#""218.107.132.66"#"184.179.24.180"#"74.125.74.194"#"100.179.24.100"##test-ips##"
        # logging.error(ip)
        t=None
        try:
            t = get_location(ip,True)
            # logging.error(t)
        except Exception, e:
            pass
        ## checking what is in t
        if t:
            tester12 = ' '.join(t).strip()
        else:
            tester12 = None
        # check ipInfo gave us right info back
        if tester12 == None:
            temp=0.0
            city=""
            state=""
            icon_img=""
        elif re.match('^[a-zA-Z]+', tester12):
            name = None
            city, state, country = t
            name = city+state+","+country
            weather = get_weather(name)
            ## check for weather with the valid city/state/country info
            if weather == None:
                temp=0.0
                city=""
                state=""
                icon_img=""
            else:
                temp, icon_id = weather
                icon_img = get_icon(icon_id)
        else:
            temp=0.0
            city=""
            state=""
            icon_img=""
        # render html with params, or json if specified
        if espn_heads():
            espn_headlines, espn_links = espn_heads()
        else:
            espn_headlines = None
            espn_links = None
        if self.format == 'html':
            if self.user:
                self.render("blog_front.html", posts=posts, age=age_str(age), 
                    username="%s" % self.user.name, logout=" (Sign Out)", 
                    temp=int(round(temp)), img_url=icon_img, 
                    city='%s %s'%(city, state), espn_headlines=None,#espn_headlines, 
                    espn_links=None, USER_ID=self.user.name)#espn_links, USER_ID=self.user.name)
            else:
                self.render("blog_front.html", posts = posts, age = age_str(age), 
                    signup="Sign up", login="Sign in", temp=int(round(temp)), 
                    img_url=icon_img, city='%s %s'%(city, state), 
                    espn_headlines=None,#espn_headlines, 
                    espn_links=None)#espn_links)
        else:
            return self.render_json([p.as_dict() for p in posts])

class NewPostHandler(signup.Handler):
    def render_newPost(self, subject='', content='', subError='', 
                       contentError=''):
        self.render("new_blog_post.html", subject=subject, content=content,
                    subError=subError, contentError=contentError,
                    logout="%s (Sign Out)" % self.user.name)

    # if signed in allow new post otherwise redirect to login
    def get(self):
        if self.user:
            self.render_newPost()
        else:
            self.redirect('/login/blog')

    # if creator is (me) allow script otherwise sanitize(escape unsafe html)
    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        creator = self.user.name
        if creator == me:
            pass
        elif content:
            content = sanitize_html(content)
        # put newpost into db redirect to permalink if valid subject and 
        # content, otherwise prompt for such
        if subject and content:
            np = BlogPost(subject=subject, content=content, creator=creator)
            blog_key = np.put()

            self.redirect("/blog/%d" % blog_key.id())
            global newPost
            newPost = True
        # check for invalid subject or content
        elif subject and not content:
            contentError = " *Invalid"
            self.render_newPost(subject, content, contentError=contentError)
        elif not subject and content:
            subError = " *Required"
            self.render_newPost(subject, content, subError=subError)
        else:
            contentError = " *Invalid"
            subError = " *Required"
            self.render_newPost(subject, content, contentError=contentError,
                                subError=subError)


# after a new post -> directed here
class Permalink(Handler):
    
    def get(self, post_id):
        post_key = 'POST_' + post_id

        post, age = age_get(post_key)

        if not post:
            key = db.Key.from_path('BlogPost', int(post_id))
            post = db.get(key)
            age_set(post_key, post)
            age = 0
        
        if not post:
            self.error(404)
            return
        post.permalink = post_id
        post.put()

        if self.format == 'html':
            self.render("permalink.html", subject=post.subject,
                        content=post.content, age = age_str(age))
        else:
            self.render_json(post.as_dict())
        
##        self.render_permalink(subject=newPost.subject, content=newPost.content)

# flush memcache for entire site--useful
class Flush(Handler):
    def get(self):
        memcache.flush_all()
        self.redirect('../welcome')

#ignore not in use!
class Sitemap(Handler):
    def get(self):
        xmlobj = md.parse("sitemap.xml")
        self.write(xmlobj.toprettyxml())

# get cordinantes(city and state name here) from hostip api passing in user ip address
IP_URL = 'http://api.ipinfodb.com/v3/ip-city/?key=%s&ip='%ip_key#"http://api.hostip.info/?ip="
def get_location(ip, countryCode=False):
    #ip = "4.2.2.2"
    # ip = "23.24.209.141"
    # ip = "74.125.74.194"
    if ip:
        url = IP_URL + ip + '&format=json'
        logging.error(str(url))
        content = None
        try:
            content = urllib2.urlopen(url, timeout=15)
        except urllib2.URLError, HTTPException:
            return None 
        if content:
            #parse json and find coords
            try:
                d = json.load(content)
            except ValueError, HTTPException:
                return None
            city = d['cityName'].replace(' ','')
            state = d['regionName'].replace(' ','')
            country = d["countryName"].replace(' ','')
            countryCode = d["countryCode"]
            if city and state and countryCode:
                if country == state:
                    return city, countryCode
                else:
                    return city+',', state, countryCode

    else:
        return None

# WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&units=imperial&APPID=b62e487dc41951733fd0a7585e53ce9e'
WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather?q=%s&units=imperial&APPID=%s'
# get weather based on value returned from get_location() using openweathermap api, return temperature and weather icon id
def get_weather(cityState):#lat, lon):
    # lat, lon = get_coords(ip)
    if cityState is None:
        return None
    # name = "Scottsdale, AZ"
    url = WEATHER_URL % (cityState, weather_key)
    content = None
    try:
        content = urllib2.urlopen(url, timeout=15)#"https://ryanslootpy.appspot.com/failedconnection")#
    except urllib2.URLError, HTTPException:
        return
    if content:
        # logging.error(str(content))
        try:
            j = json.load(content)
        except ValueError, HTTPException:
            return None
        temp = (j['main']['temp'])# for c in j)
        # logging.error(str(temp))
        icon_id = (j['weather'][0]['icon'])# for c in j)
        # city_name = (j['name'])
        return temp, icon_id#, city_name
    return None
        
WEATHER_ICON_URL = "http://openweathermap.org/img/w/"
# get and return weather icon associated with weather
def get_icon(icon_id):
    icon_img = None
    try:
        icon_img = WEATHER_ICON_URL + str(icon_id) + ".png"
    except urllib2.URLError:
        return
    if icon_img is not None:
        # logging.error(str(icon_img))
        return icon_img

ESPN_RSS_URL = "http://sports.espn.go.com/espn/rss/news"
# get headlines from ESPN's rss feed, who doesn't love sports
def espn_heads():
    try:
        content = urllib2.urlopen(ESPN_RSS_URL, timeout=15)
    except Exception, e:
        return
    d = feedparser.parse(content)
    headlines = [d.entries[i].title for i in range(len(d.entries))]
    links = [d.entries[i].link for i in range(len(d.entries))]
    # logging.error(headlines)
    return headlines, links

class fail_test(Handler):
    def get(self):
        self.render("failedconnection.html")

application = webapp2.WSGIApplication([
    ('/failedconnection/?', fail_test),
], debug=True)