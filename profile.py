import signup
import wiki
import blog
import re
import urllib2
import logging
import cgi
from handler import *


from google.appengine.api import memcache
from google.appengine.ext import db,ndb, blobstore
from google.appengine.api import images
from google.appengine.api import urlfetch


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        # params['user'] = self.user
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_prof(self, template, **kw):
    	self.response.headers['Content-Type'] = 'image/png'
    	self.write(self.render_str(template, **kw))

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)


# display profile of user requested
class Profile(Handler, signup.Handler):
	def get(self, user):
		if self.request.referer:
			if 'edit' in self.request.referer:
				self.write("<script>alert('Profile Updated!')</script>")
		# pic_key = ndb.Key(urlsafe=self.request.get('img_id')
		# u is current profile looking at
		u = signup.User.by_lower_name(user[1:])
		# get avatar if there
		# a = signup.AvatarDB.get_by_userID(u.name)
		if u:
			if u.avatar is not None:
				idex = self.request.url.find('/',8)
				avatar = self.request.url[:idex]+ '/images/%s.jpeg' % u.name
				# avatar = urlfetch.Fetch(avatar+'/images/%s'%u.name).content

				logging.error(avatar)
			else:
				avatar = ''
		else:
			avatar = None
		# if logged in check if going to own profile
		if self.user and u:
			current_user = signup.User.by_lower_name(self.user.name)
			if u.name == current_user.name:
				# logging.error(get_followers(u.name))
				# logging.error
				self.render("profile.html", user=u.name, email=u.email, 
					contributions=u.contributions, edit="Edit Profile", 
					followers=get_followers(u.name), 
					following=get_following(u.name), avatar=avatar)
			elif u and u.name not in current_user.profiles_following:
				self.render("profile.html", user=u.name, email=u.email, 
					contributions=u.contributions, edit="", follow=True, 
					followers=get_followers(u.name), 
					following=get_following(u.name), avatar=avatar)
			elif u and u.name in current_user.profiles_following:
				self.render("profile.html", user=u.name, email=u.email,
					contributions=u.contributions, edit="", unfollow=True,
					followers=get_followers(u.name),
					following=get_following(u.name), avatar=avatar)
			else:
				self.render("failedconnection.html", user=user[1:])
		else:
			if u:
				self.render("profile.html", user=u.name, email=u.email,
					contributions=u.contributions, edit="", follow=False,
					followers=get_followers(u.name),
					following=get_following(u.name), avatar=avatar)
			else:
				self.render("failedconnection.html", user=user[1:])
	def post(self, user):
		u = signup.User.by_lower_name(user[1:])
		# logging.error(u.name)
		# self.user.name is current user, where user passed 
		# through url is the profile to follow
		if self.request.get("follow-button"):
			follow_profile(self.user.name, u.name)
			self.render("profile.html", user=u.name, email=u.email,
				contributions=u.contributions, edit="", unfollow=True,
				alert="<script>alert('You will now be emailed when " +
				 "%s makes a new contribution')</script>" % u.name, 
				 followers=get_followers(u.name), 
				 following=get_following(u.name))
		else:
			unfollow_profile(self.user.name, u.name)
			self.render("profile.html", user=u.name, email=u.email, 
				contributions=u.contributions, edit="", follow=True,
				followers=get_followers(u.name),
				following=get_following(u.name))


class EditProfile(Handler, signup.Handler):
	def get(self, user):
		u = signup.User.by_lower_name(user[1:])
		if self.user:
			if self.user.name == str(u.name):
				self.render("edit_profile.html", user=u.name, email=u.email)
			else:
				self.redirect('/welcome')
				# self.render('welcome.html', alert=\
				# 	"<script>alert('Not your profile! Cannot edit')"+"</script>")
		else:
			self.redirect("/login")
	def post(self, user):
		# helper bools
		up_user = False
		up_email = False
		up_img = False
		# logging.error(user)
		# get username and email from form check values
		username = self.request.get("username")
		u = signup.User.by_lower_name(user[1:])
		alreadyUser = signup.User.by_lower_name(username)
		w = wiki.WikiPost.all().get()
		email = self.request.get('email')

		#get image db
		img = self.request.get('img')
		logging.error(img)

		if img:
			new_avatar = images.resize(img, 32, 32)
			u.avatar = db.Blob(img)
			# u.avatar_key = blobstore.BlobInfo(blobstore.BlobKey(str(u.key())))
			# u.avatar = str(new_avatar)
			
		# if username entered is different update check for errors
		if str(u.name) != username:
			if alreadyUser:
				self.render("edit_profile.html", user=username, email=email,
					userTakenError="Username Already Exists")
				return
			elif signup.valid_username(username):
				u.name = username
				u.lowerName = username.lower()
				up_user = True
				if w.creator == user[1:]:
					w.creator = username
				for i in range(len(w.modifiers)):
					if w.modifiers[i] == user[1:]:
						w.modifiers[i] = username
			else:
				self.render("edit_profile.html", user=username, email=email,
					invalidUsername="Invalid Username")
				return
		# check if email was changed update if it was
		if u.email != email:
			if signup.valid_email(email):
				u.email = email
				up_email = True
			else:
				self.render("edit_profile.html", user=username, email=email,
					emailError="Invalid Email")
				return
		if up_user or up_email or not up_user and not up_email:
			w.put()
			u.put()
			# self.write("<script>alert('Profile Updated!')</script>")
			self.redirect('/strike/%s' % username)
			# self.render("thanks_updated.html", username=username, email=email)
			memcache.flush_all()

class ImageHandler(Handler):
	def get(self, user):
		u = signup.User.by_lower_name(user[1:])
		if u:
			# self.response.headers['Content-Type'] = 'image/jpeg'
			# self.render('images.html', u.avatar)
			logging.error(u.avatar)
			self.response.out.write(u.avatar)
		else:
			self.redirect('/')



def follow_profile(user, follow):
	# add profile to following list of current user
	u = signup.User.by_lower_name(user)
	u.profiles_following.append(follow)
	# add user to followers of profile
	p = signup.User.by_lower_name(follow)
	p.followers.append(user)
	# commit to db and memcache
	memcache.set(str(follow)+"followers", p.followers)
	memcache.set(str(user)+"following", u.profiles_following)
	p.put()
	u.put()
	return

def unfollow_profile(user, unfollow):
	# remove profile from following list of current user
	u = signup.User.by_lower_name(user)
	u.profiles_following.remove(unfollow)
	# remove current user from profile user's followers list
	p = signup.User.by_lower_name(unfollow)
	p.followers.remove(user)
	# commit to db and memcach
	memcache.set(str(unfollow)+"followers", p.followers)
	memcache.set(str(user)+"following", u.profiles_following)
	p.put()
	u.put()
	return

def get_followers(user):
	followers = memcache.get(str(user)+"followers")
	if followers is None:
		u = signup.User.by_lower_name(user)
		followers = u.followers
	return followers

def get_following(user):
	following = memcache.get(str(user)+"following")
	if following is None:
		u = signup.User.by_lower_name(user)
		following = u.profiles_following
	return following



PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
application = webapp2.WSGIApplication([
	('/rsp/edit/?' + PAGE_RE, EditProfile),
	('/strike/?' + PAGE_RE, Profile),
	('images/?' + PAGE_RE, ImageHandler)
], debug=True)