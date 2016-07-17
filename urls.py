import webapp2
import asciichan
import play
import blog
import signup
import ryanslootpy
import wiki
import openingday
import userBlog
import profile
import strike
import hiddenBlog
# from ryanslootpy.views import *

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
class google_var(signup.Handler):
    def get(self):
        self.render('google224fe30fcbac0a15.html')


application = webapp2.WSGIApplication([
    ('/ryanshiddenblog/?',  hiddenBlog.BlogHandler),
    ('/ryanshiddenblog/?(?:\.json)?', hiddenBlog.BlogHandler),
    ('/ryanshiddenblog/newpost/?', hiddenBlog.NewPost),
    ('/strike/?', strike.Strike),
    ('/d3try/?', strike.d3tryHandler),
    ('/rsp/edit/?' + PAGE_RE, profile.EditProfile),
    ('/strike/?' + PAGE_RE, profile.Profile),
    ('/blog/?(?:\.json)?', blog.MainPage),
    ('/blog/newpost/?', blog.NewPostHandler),
    ('/blog/(\d+)(?:\.json)?', blog.Permalink),
    ('/blog/newpost/?' + PAGE_RE, userBlog.NewPost),
    ('/blog/?' + PAGE_RE, userBlog.MainPage),
    ('/blog/?' + PAGE_RE + '(?:\.json)', userBlog.MainPage),
    ('/flush/?', blog.Flush),
    ('/blog/sitemap', blog.Sitemap),
    ('/play/?', play.MainPage),
    ('/rot13', ryanslootpy.Rot13Handler),
    # ('/_edit/?', wiki.Special),
    ('/images/?' + PAGE_RE, profile.ImageHandler),
    ('/google224fe30fcbac0a15.html/?', google_var),
    ('/openingday/?', openingday.opening_day),
    ('/signup/?', signup.Register),
    ('/welcome/?', signup.WelcomeHandler),
    ('/login/?' + PAGE_RE, signup.Login),
    ('/logout/?' + PAGE_RE, signup.Logout),
    # ('/logout/blog/? + PAGE_RE', signup.Logout),
    ('/asciichan/?', asciichan.MainPage),
    ('/_edit/?' + PAGE_RE, wiki.EditPage),
    (PAGE_RE, wiki.WikiPage),
], debug=True)