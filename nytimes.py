import urllib2
import logging
from handler import *
from secrets import *

from twilio import twiml
from twilio.rest import TwilioRestClient


url = 'https://api.nytimes.com/svc/books/v3/lists.json?api-key=%s&list=%s'
fields = ['title', 'author']
class nytimes(Handler):
	def get(self):
		sections = ['hardcover-nonfiction','combined-print-and-e-book-nonfiction']
		new_bests = {}
		for section in sections:
			new_bests[section] = {}
			books_url = url % (nytimes_BOOKS_API_KEY, section)
			## limit to top 15 books as only they have weeks_on_list field
			# data = requests.get(books_url, timeout=60).json()['results'][:15]
			content = urllib2.urlopen(books_url).read()#, timeout=60)
			# logging.error(type(content.read(100)))
			data = json.loads(content)
			data = data['results'][:15]
			# if book recent addition to best seller list add to new_bests dict
			for book in data:
				# if a book has been on list 2 weeks or less
				if book['weeks_on_list'] <= 2:
					book_details = book['book_details'][0]
					title = book_details['title']
					new_bests[section][title] = \
							(book_details['author'], book['weeks_on_list'])
		books = {}
		i = 0
		text_body = ''
		## loop through sections and get unique books for each
		for section in sections:
			for (title, author_weeks) in new_bests[section].items():
				if title in books:
					continue
				else:
					# first line print header
					if i == 0:
						text_body +=\
						'\nNew books on NY Times best sellers list:\n- %s by %s (%d)'\
							% (title, author_weeks[0], author_weeks[1])
						i = 1
					else: 
						text_body += '\n- %s by %s (%d)' % \
								(title, author_weeks[0], author_weeks[1])
					books[title] = author_weeks[0]

		client = TwilioRestClient(twilio_account_sid, twilio_auth_token)
		# replace "to" and "from_" with real numbers
		rv = client.messages.create(to=my_phone,
									from_=twilio_number,
									body=text_body)
		logging.error
		


application = webapp2.WSGIApplication([
    ('/tasks/nytimes/?', nytimes),
], debug=True)