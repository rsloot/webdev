import os
import webapp2
import json
import jinja2

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import vendor

# Add any libraries installed in the "lib" folder.
vendor.add('lib')
import scrubber
import feedparser

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

global newPost
newPost = False

# save the html from xss
def sanitize_html(text):
    return jinja2.Markup(scrubber.Scrubber().scrub(text))

jinja_env.filters['sanitize_html'] = sanitize_html

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        # params['user'] = self.user
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_json(self, d):
        json_txt = json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

    # def read_secure_cookie(self, name):
    #     cookie_val = self.request.cookies.get(name)
    #     return cookie_val and signup.check_secure_val(cookie_val)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        # uid = self.read_secure_cookie('user_id')
        # self.user = uid and signup.User.by_id(int(uid))
        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'