import wsgiref.handlers
import cgi
from google.appengine.api.memcache import Client
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import webapp2
import time, os
import urlparse
import hashlib, base64

class StaticLinks(db.Model):
	email = db.StringProperty()
	iosURL = db.StringProperty()
	androidURL = db.StringProperty()
	mobileURL = db.StringProperty()
	webURL = db.StringProperty()
	hashURL = db.StringProperty()
	timestamp = db.DateTimeProperty(auto_now_add=True)

class HomeHandler(webapp2.RequestHandler):
    def get(self):
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path,{}))

class NewStaticLinkHandler(webapp2.RequestHandler):
    def post(self):
		currentTime = time.strftime("%a,%Y %H:%M:%S", time.gmtime())
		hash_key = hashlib.md5()
		hash_key.update(currentTime + self.request.get('email'))
		#base64_hash_key = base64.urlsafe_b64encode(hash_key.digest()).rstrip('\n=').replace('+' , 'z').replace('/' , 'z').replace('=' , 'z')
		base64_hash_key = base64.urlsafe_b64encode(hash_key.digest()).rstrip('\n=').replace('+' , 'z').replace('/' , 'z').replace('=' , 'z')
		hashURL = base64_hash_key[::2]
		newStaticLink = StaticLinks()

		if self.request.get('mobileURL') is None or len(self.request.get('mobileURL')) == 0:
			mobileURL = self.request.get('webURL')
		else:
			mobileURL = self.request.get('mobileURL')

		if self.request.get('iosURL') is None or len(self.request.get('iosURL')) == 0:
			iosURL = mobileURL
		else:
			iosURL = self.request.get('iosURL')

		if self.request.get('androidURL') is None or len(self.request.get('androidURL')) == 0:
			androidURL = mobileURL
		else:
			androidURL = self.request.get('androidURL')

		newStaticLink.iosURL = unescape(iosURL)
		newStaticLink.androidURL = unescape(androidURL)
		newStaticLink.mobileURL = unescape(mobileURL)
		newStaticLink.webURL = unescape(self.request.get('webURL'))
		newStaticLink.hashURL = hashURL
		newStaticLink.email = self.request.get('email')
		newStaticLink.put()
		#self.response.write('Your Link is: <a href="/(' + base64_hash_key + ')">www.plungr.com/(' + base64_hash_key +')</a>')
		template_values = {'iosURL':iosURL,
						'androidURL':androidURL,
						'mobileURL':mobileURL,
						'webURL':self.request.get('webURL'),
						'hashURL':hashURL,
						'email':self.request.get('email')}

		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))
		return None

def unescape(s):
	s = s.replace("&lt;", "<")
	s = s.replace("&gt;", ">")
	s = s.replace("&amp;", "&")
	return s

class StaticRedirectHandler(webapp2.RequestHandler):
	def get(self,hashURL):
		#self.response.write('Your Link is: ' + hashURL[1:][:-1])
		q = db.GqlQuery("SELECT * "
								"FROM StaticLinks WHERE hashURL = :1 LIMIT 1", hashURL[1:][:-1])
		
		for deepLink in q:
			template_values = {'iosURL':unescape(deepLink.iosURL),
						'androidURL':unescape(deepLink.androidURL),
						'mobileURL':unescape(deepLink.mobileURL),
						'webURL':unescape(deepLink.webURL),
						'hashURL':deepLink.hashURL}

			path = os.path.join(os.path.dirname(__file__), 'redirect.html')
			self.response.out.write(template.render(path, template_values))


class RedirectHandler(webapp2.RequestHandler):
    def get(self, appURL, webURL):
		template_values = {'appURL':appURL[1:][:-1],'webURL':webURL[1:][:-1]}
		path = os.path.join(os.path.dirname(__file__), 'redirect.html')
		self.response.out.write(template.render(path, template_values))

app = webapp2.WSGIApplication([
    webapp2.Route(r'/', handler=HomeHandler, name='home'),
    #webapp2.Route(r'/products/<product_id:\d+>', handler=RedirectHandler, name='product'),
	#webapp2.Route(r'/redirect/<appURL:\#.*?\#><domain:\#.*?\#><appname:\#.*?\#>', handler=RedirectHandler, name='redirect')	    
	webapp2.Route(r'/redirect/<appURL:\(.*?\)>/<webURL:\(.*?\)>', handler=RedirectHandler, name='redirect'),
	webapp2.Route(r'/<hashURL:\(.*?\)>', handler=StaticRedirectHandler, name='redirect'),
	webapp2.Route(r'/new', handler=NewStaticLinkHandler, name='new-link')	    
])


