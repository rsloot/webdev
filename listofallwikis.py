import wiki
from handler import *

import logging



class list_Wiki(Handler):
	def get(self):
		dlist = wiki.WikiPost.all().order("page_name")
		#db.GqlQuery("SELECT page_name FROM WikiPost") # arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC LIMIT 10")

		duh_list = []
		duh_list += [i.page_name for i in dlist]
		# logging.error(duh_list[0])

		self.render("listwikis.html", wikilist=duh_list)

application = webapp2.WSGIApplication([
    ('/wikilist/?', list_Wiki),
], debug=True)