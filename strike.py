import signup
import userBlog
import re
from datetime import datetime, timedelta
import urllib2
import logging
from handler import *

from xml.dom import minidom


# class StrikePostDB(db.Model):
#     #TODO
#     return None

class Strike(signup.Handler, Handler):
    def get(self, user=False,q=None):
        # if signed in get personal timeline
        # if not signed in get twenty latest strikes
        # allow filter by topic
        q = self.request.get('q')
        posts = []
        postsCount = 0
        if self.user:
            u = signup.User.by_lower_name(self.user.name)
            following = u.profiles_following
            for i in following:
                    current_user = userBlog.UserBlogPost.by_lower_name(i, 
                                                update=userBlog.check_newPost())
                    for j in current_user:
                        postsCount+=1
            # ''' get each user post that following
            #     if people following have no posts
            #     get 20 latest allow filter by topic'''
            if q:
                # logging.error(str(q))
                p = userBlog.UserBlogPost.by_category(str(q), 
                                        update=userBlog.check_newCat(str(q)))
                for i in p:
                    posts.append(i)
            elif postsCount > 0:
                # logging.error(str(len(following)))
                for i in following:
                    current_user = userBlog.UserBlogPost.by_lower_name(i, 
                                                update=userBlog.check_newPost())
                    for j in current_user:
                        posts.append(j)
                pass
            else:
                # logging.error(str('six'))
                p = userBlog.UserBlogPost.get_latest()#default gets 20 latest
                for i in p:
                    posts.append(i)
            # logging.error(str(posts[0]))
        else:
            if q:
                p = userBlog.UserBlogPost.by_category(str(q), 
                                        update=userBlog.check_newCat(str(q)))
                # logging.error
                for i in p:
                    posts.append(i)
            else:
                p = userBlog.UserBlogPost.get_latest()
                for i in p:
                    posts.append(i)
        if len(posts) == 0:
            posts=''
        self.render("strikebase.html", posts = posts)

class d3tryHandler(Handler):
    def get(self):
        self.render('d3try.html')

application = webapp2.WSGIApplication([
    ('/d3try/?', d3tryHandler),
], debug=True)