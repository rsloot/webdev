import signup
from handler import *
from secrets import sg_username, sg_password
# import wikidb as db
from datetime import datetime
# from dateutil.tz import tzutc, tzlocal

from google.appengine.api import memcache
from google.appengine.api import mail

import pytz


class WikiPost(db.Model):
    page_name = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    creator = db.StringProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    modifiers = db.ListProperty(str, indexed=False, default=[])


    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("wikipost.html", p = self)

    @classmethod
    def by_name(cls, name):
        return WikiPost.all().filter('page_name =', name).get()
    # @classmethod
    # def update_content(cls, new_content, db_entry):
    #     name.content = new_content
    
    def as_dict(self):
        time_fmt = '%c'
        d = {'content': self.content,
             'creator': self.creator,
             'created': self.created.strftime(time_fmt),
             'last_modified': self.last_modified.strftime(time_fmt),
             'modifiers': self.modifiers }
        return d

def get_mod_time(key, update=False):
    time = memcache.get(key)
    if time is None or update:
        time =  WikiPost.by_name(key[:len(key)-1]).last_modified
        memcache.set(key, time)
    return time


def get_page(key, update=False):
    # key = page_id
    page = memcache.get(key)
    if page is None or update:
        # logging.error("DB QUERRY")
        # logging.error(str(key))
        page = WikiPost.by_name(key)
        memcache.set(key, page)

    return page


class WikiPage(signup.Handler, Handler):
    def get(self, page_id): 
        page_id = page_id.lower()
        page = get_page(page_id)
        if page_id and not page:
            if page_id == '/logout':
                self.redirect('/')
            elif page_id == '/login':
                self.redirect('/login/welcome')
            elif page_id == "/_edit":
                self.redirect('/_edit%s' % '/')
            else:
                self.redirect('/_edit%s' % page_id)

        if page_id and page:
            page = get_page(page_id)#, update=True)
            content = page.content

            lm = page.last_modified

            last_modified = lm#.astimezone(tzlocal())           

            modifiers = page.modifiers
            creator = page.creator
            page_id = page_id[1:2].upper() + page_id[2:]
            if self.user:
                # logging.error(last_modified.tzinfo)
                self.render("wiki.html", page_title=page_id, content=content,
                            username="%s" % self.user.name,
                            logout=" (Sign Out)", edit="Edit", signup="",
                            login="", USER_ID=self.user.name,
                            last_modified=last_modified, modifiers=modifiers,
                            creator=creator)
            else: 
                self.render("wiki.html", page_title=page_id, content=content,
                            username="", logout="", edit="", signup="Sign up",
                            login="Sign in", last_modified=last_modified,
                            modifiers=modifiers, creator=creator)
        # self.redirect('/_edit%s' % '/')


class EditPage(signup.Handler, Handler):
    def get(self, edit_id):
        edit_id = edit_id.lower()
        if not self.user and edit_id:
            self.redirect('/login%s' % edit_id)
        page=get_page(edit_id)
        if page:
            content = page.content.replace('<br />', '\n')
            last_modified = get_mod_time(edit_id+"t", update=True)
            pacific = pytz.timezone('US/Mountain')
            last_modified = pacific.localize(last_modified, is_dst=False)
            self.render("edit.html", edit_id=edit_id[1:], content=content,
                        last_modified=last_modified, creator=page.creator,
                        modifiers=page.modifiers)
        else:
            self.render("edit.html", edit_id=edit_id[1:])

    def post(self, edit_id):
        edit_id = edit_id.lower()
        page = get_page(edit_id)
        u = signup.User.by_lower_name(self.user.name)
        modifiers = []
        if not page:
            page_name = edit_id
            creator =  self.user.name
            modifiers.append(creator)
            # u.contributions.append(str(page_name))
        creator = self.user.name
        content = self.request.get("content")
        content = content.replace('\n', '<br>')
        # if creator is not me santize html
        if creator != "Ryan":
            content = sanitize_html(content)

        if content and not page:
            np = WikiPost(page_name=edit_id, content=content, creator=creator,
                          modifiers=modifiers)
            wiki_key = np.put()
            memcache.set(edit_id, np)
            memcache.set(edit_id+"t", np.last_modified)
            u.contributions.append(str(page_name))
            email_followers(u.name, u.followers, edit_id)
            u.put()

            self.redirect("..%s" % edit_id)
        elif content and page:
            page.content = content
            if str(self.user.name) not in page.modifiers:
                page.modifiers.append(str(self.user.name))
                u.contributions.append(str(edit_id))

            email_followers(u.name, u.followers, edit_id)
            u.put()
            page.put()
            memcache.set(edit_id, page)
            memcache.set(edit_id+"t", page.last_modified)

            self.redirect("..%s" % edit_id)
        else:
            error = "Nice try %s we need some CONTENT!!!" % self.user.name
            self.render('edit.html', edit_id=edit_id[1:], current="",
                        content="", error=error)


import sendgrid


def email_followers(user, followers, edit_id):
    
    sg = sendgrid.SendGridClient(sg_username, sg_password)
    message = sendgrid.Mail()
    
    for i in followers:
        end_user_email = signup.User.by_lower_name(i).email
        if end_user_email:
            message.set_from("Ryan Sloot <admin@ryanslootpy.appspotmail.com>") #sendgrid

            # sender_address = "Ryan Sloot py <admin@ryanslootpy.appspotmail.com>"
            # user_address = "%s <%s>" % (i, end_user_email)
            message.add_to("%s" % end_user_email) #sendgrid


            message.set_subject("New post by %s" % user) #Sendgrid
            # subject = "New post by %s" % user
            # body = """Dear %s:
            #     https://ryanslootpy.appspot.com/%s was edited or created by %s! You are recieving this email because you followed this user, to unsubscribe to update emails go to the following link and click unfollow https://ryanslootpy.appspot.com/rsp/%s!
            #     Thanks, Ryan <admin@ryanslootpy.appspotmail.com>""" % (i, edit_id[1:], user, user)
            message.set_html("""<html><head></head><body>
        Dear %s:<br><br>
        <a href='https://ryanslootpy.appspot.com/%s'>%s</a> was edited or created by %s!<br>
         You are recieving this email because you followed this user.
         <br>To unsubscribe to update emails go to the following link and click 
         <a href='https://ryanslootpy.appspot.com/strike/%s'>unfollow</a>
         -You may need to <a href='https://ryanslootpy.appspot.com/login'>Login</a>!<br><br>
         Thanks,<br>Ryan<br>admin@ryanslootpy.appspotmail.com </body></html> """ 
                 % (i, edit_id[1:], edit_id[1:], user, user))

            # mail.send_mail(sender_address, user_address, subject, html)
            sg.send(message)
        else:
            continue
    return

# class Special(Handler):
#     def get(self):
#         self.redirect('/_edit')

# q = "SELECT modifiers FROM WikiPost WHERE page_name = name"