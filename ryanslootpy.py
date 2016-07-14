import cgi
import re
from handler import *

# months = ['January',
#       'February',
#       'March',
#       'April',
#       'May',
#       'June',
#       'July',
#       'August',
#       'September',
#       'October',
#       'November',
#       'December']
    
      
# def valid_month(month):
#     if month:
#         cap_month = month.capitalize()
#         if cap_month in months:
#             return cap_month
# def valid_day(day):
#     if day and day.isdigit():
#         day = int(day)
#         if day > 0 and day <= 31:
#             return day
# def valid_year(year):
#     if year and year.isdigit():
#         year = int(year)
#         if year >= 1900 and year <= 2020:
#             return year

# def escape_html(s):
#     return cgi.escape(s, quote = True)



# class MainPage(Handler):
    
#     def render_main(self, error="", month="", day="", year=""):
#         self.render("ryanslootpy.html", error=error, month=month, day=day, year=year)
    
#     def get(self):
#         self.render_main()

#     def post(self):
#         user_month = self.request.get('month')
#         user_day = self.request.get('day')
#         user_year = self.request.get('year')

#         month = valid_month(user_month)
#         day = valid_day(user_day)
#         year = valid_year(user_year)

#         if month and day and year:
#             self.redirect("/thanks")
#         else:
#             self.render_main("That doesn't look valid to me, friend.",
#                             user_month, user_day, user_year)

# class ThanksHandler(webapp2.RequestHandler):
#     def get(self):
#         self.response.out.write("thanks thats a totally valid date")




class Rot13Handler(Handler):                                        
    def get(self, rot=""):
        self.render("rot13.html", rot=rot)

    def post(self):
        rot13 = ''
        text = self.request.get('text')
        if text:
            rot13 = text.encode('rot13')

        self.render("rot13.html", rot=rot13)
                              
        
# application = webapp2.WSGIApplication([
#     # ('/', MainPage),
#     # ('/thanks', ThanksHandler),
#     ('/rot13', Rot13Handler),
# ], debug=True)
