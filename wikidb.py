import wiki
import jinja2


from google.appengine.ext import db



def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

class WikiPost(db.Model):
    page_name = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    creator = db.StringProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)


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
             'last_modified': self.last_modified.strftime(time_fmt)}
        return d