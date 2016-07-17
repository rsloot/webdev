from handler import *
from secrets import *
import signup
# import re
from datetime import datetime, timedelta
import urllib2
import logging


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

def get_posts(update = False):
    # key = 'po'
    # posts = memcache.get(key)
    mc_key = 'HIDDEN_BLOGS'

    posts, age = age_get(mc_key)
    if posts is None or update:
        q = HiddenPosts.all().order('-created').fetch(limit = 10)
        posts = list(q)
        age_set(mc_key, posts)

    return posts, age

# db class for all blogposts
class HiddenPosts(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    creator = db.StringProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)
    
    def as_dict(self):
        time_fmt = '%c'
        d = {'subject': self.subject,
             'content': self.content,
             'creator': self.creator,
             'created': self.created.strftime(time_fmt),
             'last_modified': self.last_modified.strftime(time_fmt)}
        return d


class BlogHandler(signup.Handler, Handler):
    def get(self):
        if self.user:
            if self.format == 'html':
                u = self.user.name
                if u == me:
                    posts, age = get_posts(update=True)				
                    self.render("hiddenBlog_fill.html", posts = posts, age = 1, 
                                username="%s" % self.user.name)
                else:
                    self.render("access_denied.html", u=u)
                    logging.error(u)
            else:
                u = self.user.name
                if u == me:
                    posts, age = get_posts(update=True)
                    return self.render_json([p.as_dict() for p in posts])
                else:
                    self.render('access_denied.html', u=u)
                    logging.error(u)
        else:
            self.render("access_denied.html", u='')


class NewPost(signup.Handler, Handler):
	def get(self):
		if self.user:
			if self.user.name == me:
				# TODO
				self.render("hidden_new_post.html")
			else:
				self.render("access_denied.html", u=self.user.name)
		else:
			self.render("access_denied.html", u='')
	def post(self):
		subject = self.request.get("subject")
		content = self.request.get("content")
		creator = "Ryan"
		# put newpost into db redirect to permalink if valid subject and content, otherwise prompt for such
		if subject and content:
			np = HiddenPosts(subject=subject, content=content, creator=creator)
			blog_key = np.put()

			self.redirect("/ryanshiddenblog")
			global newPost
			newPost = True