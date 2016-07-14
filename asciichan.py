import signup
import urllib2
from xml.dom import minidom
# import logging
from handler import *


helper = False

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
def gmaps_img(points):
    markers = '&'.join('markers=%s,%s' % (p.lat, p.lon)
                       for p in points)
    return GMAPS_URL + markers

    
IP_URL = "http://api.hostip.info/?ip="
def get_coords(ip):
    # ip = "4.2.2.2"
    # ip = "23.24.209.141"
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except:# URLError:
        return

    if content:
        #parse xml and find coords
        d = minidom.parseString(content)
        coords = d.getElementsByTagName("gml:coordinates")
        if coords and coords[0].childNodes[0].nodeValue:
            lon, lat = coords[0].childNodes[0].nodeValue.split(',')
            return db.GeoPt(lat, lon)
        

##defining an entity in GAE
class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()

def top_arts(update = False):
    key = 'top'
    arts = memcache.get(key)
    if arts is None or update:
        # logging.error("DB QUERRY")
        arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC LIMIT 10")
        #prevent the running of multiple queries
        arts = list(arts)
        memcache.set(key, arts)
        
    return arts


class MainPage(Handler):
    def render_front(self, title="", art="", error="", arts=""):
        arts = top_arts()
        global helper
        if helper:
            arts = top_arts(True)
            helper = False

        #find which arts have coords
        points = filter(None, (a.coords for a in arts))
        
        #if we have arts coords, make an image url
        img_url = None
        if points:
            img_url = gmaps_img(points)

        #display the image url


        self.render("asciichan.html", title=title, art=art, error=error, 
                    arts=arts, img_url = img_url)
            

    
    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")
        #ignore google security scan writes!!!
        if title and art:
            if title == "skipfish":
                self.redirect("/asciichan")
                return None
            a = Art(title = title, art = art)
            coords = get_coords(self.request.remote_addr)
            if coords:
                a.coords = coords
            
            a.put()
            #rerun query and update the cache
            top_arts(True)
            global helper
            helper = True

            self.redirect("/asciichan")
        else:
            error = "we need both a title and some artwork!"
            self.render_front(title, art, error)

                    
                            
        
# application = webapp2.WSGIApplication([
#     ('/asciichan/?', MainPage),
#     ('/signup/?', signup.Register)
# ], debug=True)
