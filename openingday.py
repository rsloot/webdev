# import oauth2 as oauth
# from urllib2 import quote
from handler import *

class opening_day(Handler):
	def get(self):
		self.render("openingday.html", team_name="MLB")

	def post(self):
		team = self.request.get("team_name")
		if team:
			self.render("openingday.html", team_name=team)
		else:
			self.render("openingday.html", team_name="MLB")
		# search = quote(team)

		# team_tweets = "https://api.twitter.com/1.1/search/tweets.json?q=%s&count=10&result_type=popular" % search
		# response, data = client.request(team_tweets)

		# tweets = json.loads(data)

# for tweet in tweets:
#     print tweet['text']
    # i += 1
# print tweets




# print json.dumps({'4': 5, '6': 7}, sort_keys=True, indent=4, separators=(',', ': '))

application = webapp2.WSGIApplication([
    ('/openingday/?', opening_day),
], debug=True)