# import signup
# import wiki
from handler import *
import blog
import re
import urllib2
import logging



curl = "https://finance.yahoo.com/webservice/v1/symbols/%s/quote?format=json&view=detail"
def get_quote(ticker):
    url = curl % str(ticker)
    content = None
    content = urllib2.urlopen(url)#urllib2.urlopen(url)#.read()
    if content:
        j = json.load(content)
        logging.error(content)
        j = j['list']['resources'][0]['resource']['fields']
        name =  j['issuer_name']
        last_price = '%.2f' % float(j['price'])
        change = '%.2f' % float(j['change'])
        range_52 = '%.2f - %.2f' % (float(j['year_low']), float(j['year_high']))
        return name, float(last_price), float(change), range_52

class WatchListHandler(Handler):
	quotes = ['tsla', 'nflx', 'twtr']
	company = []
	price = []
	change = []
	fifty_two_range = []

	bad_quotes = ['yhoo','hpq', 'ebay']
	x_company = []
	x_price = []
	x_change = []
	x_fifty_two_range = []
        
	for q in quotes:
		quote = get_quote(q)

		company.append(quote[0])
		price.append(quote[1])
		change.append(quote[2])
		fifty_two_range.append(quote[3])

	for bq in bad_quotes:
		bad_quote = get_quote(bq)
		x_company.append(bad_quote[0])
		x_price.append(bad_quote[1])
		x_change.append(bad_quote[2])
		x_fifty_two_range.append(bad_quote[3])

	
	def get(self):
		quotes = self.quotes
		company = self.company
		price = self.price
		change = self.change
		fifty_two_range = self.fifty_two_range

		bad_quotes = self.bad_quotes
		x_company = self.x_company
		x_price = self.x_price
		x_change = self.x_change
		x_fifty_two_range = self.x_fifty_two_range

		# if len(quotes) > 0: 
		self.render("watchlist.html", quotes=quotes, company=company, 
					price=price, change=change, 
					fifty_two_range=fifty_two_range,
					bad_quotes=bad_quotes, x_company=x_company, 
					x_price=x_price, x_change=x_change,
					x_fifty_two_range=x_fifty_two_range)
		# else:
			# self.redirect("/failedconnection")


application = webapp2.WSGIApplication([
    ('/watchlist/?', WatchListHandler),
], debug=True)