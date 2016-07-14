import logging
import webapp2

from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
# from google.appengine.ext.webapp.mail_handlers import InboundEmailMessage


class MailHandler(InboundMailHandler):
	def receive(self, message):
		logging.error("Message from " + message.sender)
		logging.info("+++++++++++++++++++++++++++++++++")
		# logging.info("Body of the message" + message.body)

		plaintext_bodies = message.bodies('text/plain')
    	html_bodies = message.bodies('text/html')

    	for content_type, body in html_bodies:
        	decoded_html = body.decode()
        	logging.info("Message")

application = webapp2.WSGIApplication([
	MailHandler.mapping()
	], debug=True)
