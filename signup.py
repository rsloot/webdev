import os
import webapp2
import jinja2
import re
import hashlib
import hmac
import random
import logging
from string import letters
from webob import Request
from secrets import *

from google.appengine.ext import db, ndb, blobstore
from google.appengine.api import mail

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(pw_hash_secret, val).hexdigest())

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

def render_str(template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))
        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'

    
###user stuff
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

# def pic_key(user):
#     return ndb.key

class AvatarDB(ndb.Model):
    userID = ndb.StringProperty()
    avatar = ndb.BlobProperty()

#     @classmethod
#     def store_pic(cls, userID, avatar):
#         return cls(userID = userID, avatar = avatar)
#     @classmethod
#     def get_by_userID(cls, userID, avatar=None):
#         return cls.query(cls.userID == userID).get()

#     def render_img(self):
#         avatar = self.avatar
#         # self._response.headers['Content-Type'] = 'image/png'
#         return avatar

class User(db.Model):
    name = db.StringProperty(required = True)
    lowerName = db.StringProperty(required = False)
    pname = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    contributions = db.ListProperty(str, indexed=False, default=[])
    profiles_following = db.ListProperty(str, indexed=False, default=[])
    followers = db.ListProperty(str, indexed=False, default=[])
    subscribe = db.BooleanProperty()
    avatar = db.BlobProperty(default=None)
    avatar_key = blobstore.BlobReferenceProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_lower_name(cls, nameCheck):
        u = User.all().filter('lowerName =', nameCheck.lower()).get()
        return u

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pname, pw, lowerName, email=None, subscribe=False):
        pw_hash = make_pw_hash(lowerName, pw)
        return User(parent = users_key(),
                    name = name,
                    lowerName = lowerName,
                    pname = pname,
                    pw_hash = pw_hash,
                    email = email,
                    subscribe = subscribe)

    @classmethod
    def login(cls, name, pname, pw):
        u = cls.by_lower_name(name)
        if u and valid_pw(pname, pw, u.pw_hash):
            # u = cls.by_name(name)
            return u
        # else: return check
    

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)
PASS_RE = re.compile(r"^.{6,20}$")
def valid_password(password):
    return PASS_RE.match(password)
EMAIL_RE = re.compile(r"^[\w]+@[\w]+\.[a-zA-Z]{1,3}$$")
def valid_email(email):
    return EMAIL_RE.match(email)

class SignupHandler(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')
        if self.request.get('subscribe'):
            self.subscribe = True
        else:
            self.subscribe = False
        # self.subscribe = self.request.get('subscribe')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] =\
                "That wasn't a valid password. Must be at least 6 characters long"
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if self.email and not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(SignupHandler):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_lower_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup.html', error_username = msg)
        else:
            lower=self.username.lower()
            u = User.register(name=self.username, pname = lower, 
                              pw=self.password, lowerName=lower, 
                              email=self.email, subscribe=self.subscribe)
            signup_email(self.username, self.email)
            # a = signup.AvatarDB()
            # a.userID = username
            # a.put()
            u.put()

            self.login(u)
            self.redirect('../welcome')


class Login(Handler):
    def get(self, loginId):
        if self.user:
            self.redirect('/welcome')
        else:
            self.render('login.html')

    def post(self, loginId):      
        username = self.request.get('username')
        password = self.request.get('password')
        lower_name = username.lower()

        logging.error(str(loginId))
        user = User.by_lower_name(username)
        if user is None:
            msg = 'Invalid login'
            self.render('login.html', error = msg)
        else:
            pname = user.pname

            u = User.login(lower_name, pname, password)
            if u and loginId:
                self.login(u)
                referer = self.request.referer
                referer = str(referer).replace('/login','')
                self.redirect(str(referer))
            elif u:
                self.login(u)
                # logging.error(str(loginID))
                self.redirect('/welcome')
            else:
                msg = 'Invalid login'
                self.render('login.html', error = msg)


class Logout(Handler):
    def get(self, logid):
        # path = self.request.get(path)
        self.logout()
        if logid == None:
            self.redirect("../welcome")
        else:
            # self.login(u)
            self.logout()
            referer = self.request.referer.replace('/logout','')
            logging.error(str(referer))
            self.redirect(referer)


class WelcomeHandler(Handler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.render('welcome.html', username="")

def signup_email(user, email):
    if not mail.is_email_valid(email):
        return
    else:
        # user = "Ryan"
        # email = "slootryan@gmail.com"
        # confirmation_url = createNewUserConfirmation(self.request)
        sender_address = "Ryan Sloot py <admin@ryanslootpy.appspotmail.com>"
        user_address = "%s <%s>" % (user, email)
        subject = "Thanks, %s, for registration to Blog" % user
        body = "Thank you for creating an account!"

        mail.send_mail(sender_address, user_address, subject, body)

# class Email_Handler(Handler):


# application = webapp2.WSGIApplication([
#     ('/blog/signup/?', Register),
#     ('/blog/welcome/?', WelcomeHandler),
#     ('/blog/login/?', Login),
#     ('/blog/logout/?', Logout),
# ], debug=True)
