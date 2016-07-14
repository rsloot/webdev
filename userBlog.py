import signup
import re
import urllib2
import logging
from handler import *

from xml.dom import minidom

from google.appengine.ext import ndb

# global newPost
# global categoriesDict
newPost = False
# if categoriesDict is None:
categoriesDict = {}


def check_newPost():
    # global newPost
    return newPost
def check_newCat(category):
    # global categoriesDict
    # logging.error(categoriesDict)
    # x = categoriesDict[category]
    try:
        x =categoriesDict[category]
        return x
    except Exception, e:
        return True

def set_strike(key, values):
    memcache.set(key, (values))

def post_from_memchache(key):
    r = memcache.get(key)
    # if r:
    #     key, val = r
    # else:
    #     r = None
    # logging.error(str('val:'+val))
    return r

def add_post(ip, post):
    post.put()
    get_posts(update = True)
    return str(post.key().id())

# def check_memcache(key):
#     if post_from_memchache(str(key)):
#         return True
#     return False

def get_posts_byKey(key, filterX=False, update = False, nposts=10):
    if type(key)==bool:
        memc_key = str(filterX)
    else:
        memc_key = str(key)
    posts = post_from_memchache(memc_key)
    if posts is None or update:
        logging.info("DB QUERY")
        # logging.error(str(check_memcache(key)))
        if not filterX:
            return list(UserBlogPost.all().order(key).fetch(limit=nposts))
        elif type(key) == bool:
            q = UserBlogPost.all().order('-created').filter("%s = "% filterX, key)\
                                  .fetch(limit = nposts)
            global categoriesDict
            categoriesDict[filterX] = False
            posts = list(q)
            if update:
                set_strike(filterX, q)
            else:
                memcache.add(filterX, q)
        else:
            q = UserBlogPost.all().order('-created').filter("%s = " % filterX, key)\
                                  .fetch(limit = nposts)
            posts = list(q)
            if update:
                set_strike(key, q)
            else:
                memcache.add(key, q)
            global newPost
            newPost = False
        # logging.error(type(str(posts)))
    return posts

def box_TrueFalse(box=False):
    if box:
        return True
    else:
        return False


# db class for all blogposts
class UserBlogPost(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    creator = db.StringProperty(required = True)
    lowerName = db.StringProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)
    tldr = db.TextProperty(required = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    # categories = db.ListProperty(bool, indexed=True, default=[])
    sports = db.BooleanProperty()
    news = db.BooleanProperty()
    business = db.BooleanProperty()
    tech = db.BooleanProperty()
    science = db.BooleanProperty()
    health = db.BooleanProperty()
    other = db.BooleanProperty()

    @classmethod
    def by_lower_name(cls, nameCheck, update=False, nposts=10):
        # ubp = cls.all().filter('lowerName = %s'% '',nameCheck.lower()).fetch(10)
        q = get_posts_byKey(nameCheck.lower(), filterX='lowerName', 
                            update=update, nposts=nposts)
        return q

    @classmethod
    def by_category(cls, category, update=False, nposts=10):
        q = get_posts_byKey(True, filterX=category, update=update,nposts=nposts)
        # logging.error(str(categories[2]))
        return q
    @classmethod
    def get_latest(cls, num=20):
        q = get_posts_byKey('-created',nposts=num)
        return q

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)
    def render_strike(self):
        self._render_text = self.tldr.replace('\n', '<br')
        return render_str('strike_post.html', p = self)
    
    def as_dict(self):
        time_fmt = '%c'
        # cats = ['sports', 'news', 'business','tech','science','health','other']
        # categories = dict(map(lambda x,y: [x,y], cats,self.categories))
        d = {'creator': self.creator,
             'lowerName': self.lowerName,
             'subject': self.subject,
             'content': self.content,
             'tldr' : self.tldr,
             'created': self.created.strftime(time_fmt),
             'last_modified': self.last_modified.strftime(time_fmt),
             # 'categories': categories#,
             'sports': self.sports,
             'news': self.news,
             'business': self.business,
             'tech': self.tech,
             'science': self.science,
             'health': self.health,
             'other': self.other
             }

        return d


class MainPage(signup.Handler, Handler):
    def get(self, user):
        user = user[1:]
        if self.user:
            u = signup.User.by_lower_name(self.user.name)
        # update query if new posts don't otherwise
        if not newPost:
            posts = UserBlogPost.by_lower_name(nameCheck=user, update = True)
            # logging.error(str(u.name))
            # logging.error(str(get_posts(user)))
        else:
            posts = UserBlogPost.by_lower_name(nameCheck=user, update = True)
            # logging.error(str(get_posts(user)[0]))
        if posts is None:
            self.write("you have nothing")
        if self.format == 'html':
            if self.user:
                if user == u.name:
                    self.render("user_blog_front.html", posts=posts,
                                username="%s" % u.name, logout=" (Sign Out)",
                                USER_ID="%s" % user, usernameTitle="%s"%user,
                                curUser=True)
                else:
                    self.render("user_blog_front.html", posts=posts,
                                username="%s" % u.name, logout=" (Sign Out)",
                                USER_ID="%s" % user, usernameTitle="%s"%user,
                                follow=True)
            else:
                # self.write(str(posts))
                self.render("user_blog_front.html", posts=posts, 
                            signup="Sign up", login="Sign in", 
                            usernameTitle="%s" % user)
        else:
            return self.render_json([p.as_dict() for p in posts])

class NewPost(signup.Handler):
    def render_newPost(self, subject="", content="", tldr="", subError="", 
                             contentError="", tldrError="", username=""):
        self.render("user_new_blog_post.html", subject=subject, content=content,
                    tldr=tldr, subError=subError, contentError=contentError,
                    tldrError=tldrError,
                    logout="%s (Sign Out)" % self.user.name,
                    usernameTitle=self.user.name)

    # if signed in allow new post otherwise redirect to login
    def get(self, user=False):
        if self.user:
            self.render_newPost()
        else:
            self.redirect('/login/blog/%s' % user[1:])

    # if creator is Ryan(me) allow script otherwise sanitize(escape unsafe html)
    def post(self,user=None):
        subject = self.request.get("subject")
        content = self.request.get("content")
        tldr = self.request.get("tldr")
        #category of post
        sports = box_TrueFalse(self.request.get("sportsBox"))
        news = box_TrueFalse(self.request.get("newsBox"))
        business = box_TrueFalse(self.request.get("businessBox"))
        tech = box_TrueFalse(self.request.get("techBox"))
        science = box_TrueFalse(self.request.get("scienceBox"))
        health = box_TrueFalse(self.request.get("healthBox"))
        other = box_TrueFalse(self.request.get("otherBox"))
        cat_keys = ['sports', 'news', 'business', 'tech', 'science', 'health',
                    'other']
        cat_values = [sports, news, business, tech, science, health, other]
        #blogger username
        creator = self.user.name
        if creator == user[1:]:
            content = sanitize_html(content)
        elif content:
            content = sanitize_html(content)
        # put newpost into db redirect to permalink if valid subject and content, otherwise prompt for such
        subError = " *Required"
        contentError = " *Invalid"
        tldrError = " *Required"
        if tldr:
            tldr = sanitize_html(tldr)
        if subject and content and tldr:
            if True in cat_values:
                cat_values = [sports, news, business, tech, science, health, 
                              other]
                x = dict(zip(cat_keys,cat_values))
                if categoriesDict:
                    y = categoriesDict
                else:
                    vals = [False,False,False,False,False,False,False,]
                    y = dict(zip(cat_keys,vals))
                for i,j in x.iteritems():
                    for a,b in y.iteritems():
                        if j == True and b == False and i==a:
                            # global categoriesDict
                            y[i] = True
                        else:
                            pass
                global categoriesDict
                categoriesDict = dict(y)
                # categories = cat_values
                # categories = [int(sports), int(news), int(business), int(tech), int(science), int(health), int(other)]
                # logging.error(str(cat12.map(catList)[0]))
                pass
            else:
                other = True
                cat_values = [sports, news, business, tech, science, health, other]
                x = dict(zip(cat_keys,cat_values))
                if categoriesDict:
                    y = categoriesDict
                else:
                    vals = [False,False,False,False,False,False,False,]
                    y = dict(zip(cat_keys,vals))
                for i,j in x.iteritems():
                    for a,b in y.iteritems():
                        if j == True and b == False and i==a:
                            # global categoriesDict
                            y[i] = True
                        else:
                            pass
                global categoriesDict
                categoriesDict = dict(y)
            np = UserBlogPost(subject=subject, content=content, creator=creator,
                              lowerName=creator.lower(), tldr=tldr,
                              sports=sports, news=news, business=business,
                              tech=tech, science=science, health=health,
                              other=other)# categories=categories)
            blog_key = np.put()

            self.redirect("/blog/%s" % user[1:])
            global newPost
            newPost = True
        # check for invalid subject or content
        elif subject and not content:
            self.render_newPost(subject, content, tldr,
                                contentError=contentError, tldrError=tldrError)#, sub_error="", error="")
        elif not subject and content:
            self.render_newPost(subject, content, tldr,
                                subError=subError, tldrError=tldrError)#, content_error="", error="")
        elif subject and content and not tldr:
            self.render_newPost(subject, content, tldr, tldrError=tldrError)#, sub_error="", error="")
        elif tldr and subject and not content:
            self.render_newPost(subject, content, tldr,
                                contentError=contentError)
        elif tldr and contet and not subject:
            self.render_newPost(subject, content, tldr, subError=subError)
        else:
            self.render_newPost(subject, content, tldr, subError=subError,
                                contentError=contentError, tldrError=tldrError)#, sub_error="", error="")


# after a new post -> directed here
# class Permalink(Handler):
# ##    def render_permalink(self, subject="", content=""):
# ##        self.render("permalink.html", subject=subject, content=content)
    
#     def get(self, post_id):
#         post_key = 'POST_' + post_id

#         post, age = age_get(post_key)

#         if not post:
#             key = db.Key.from_path('BlogPost', int(post_id))
#             post = db.get(key)
#             age_set(post_key, post)
#             age = 0
        
#         if not post:
#             self.error(404)
#             return
#         if self.format == 'html':
#             self.render("permalink.html", subject=post.subject, content=post.content, age = age_str(age))
#         else:
#             self.render_json(post.as_dict())
        
##        self.render_permalink(subject=newPost.subject, content=newPost.content)