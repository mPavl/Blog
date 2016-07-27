import os
from flask import Flask, render_template, redirect, url_for, flash, session, abort, request, Markup
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Required, Length, EqualTo
from datetime import datetime
from markdown import markdown
from werkzeug.contrib.cache import MemcachedCache
from flask.ext.uploads import UploadSet, configure_uploads, IMAGES
from flask_wtf.file import FileField
from PIL import Image
from resizeimage import resizeimage


# create application instance
app = Flask(__name__)
app.config.from_object('config')
cache = MemcachedCache('0.0.0.0')

# initialize extensions
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
lm = LoginManager(app)
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
configure_uploads(app, photos)

# create database tables
db.create_all()

# create class
class PhotoForm(Form):
    photo = FileField('Your photo')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    otp_secret = db.Column(db.String(16))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category %r>' % self.name

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_totp_uri(self):
        return 'otpauth://totp/2FA-Demo:{0}?secret={1}&issuer=2FA-Demo' \
            .format(self.username, self.otp_secret)

    @lm.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


class RegisterForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required()])
    password_again = PasswordField('Password again', validators=[Required(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Login')

# create router
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    try:    
        myname = None  
        if request.method == "POST":  
            myname = request.form.get('username', None)       
            return render_template('index.html', name=myname)
        else:
            return render_template('index.html')
    except:
        abort(500)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    try:
        if request.method == 'POST' and 'photo' in request.files:
            img = Image.open(request.files['photo'])
            filename = resizeimage.resize_crop(img, [400, 400])
            filename = photos.save(request.files['photo']) 
            return render_template('upload.html', filename=filename)
        else:
            return render_template('index.html')
    except:
        abort(404)

@app.route('/post', methods=['GET', 'POST'])
def post():
    try:
        if request.method == 'POST':
            post = request.form.get('text', None)   
            post = photos.save(request.files('/templates/posts')) 
            return render_template('post.html', post=post)
        else:
            return render_template('upload.html')
    except:
        abort(404)

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = RegisterForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is not None:
                flash('Username already exists.')
                return redirect(url_for('register'))
            user = User(username=form.username.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            session['username'] = user.username
            return redirect(url_for('register'))
        return render_template('register.html', form=form)
    except:
        abort(404)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.verify_password(form.password.data):
                flash('Invalid username or password.')
                return redirect(url_for('login'))
            login_user(user)
            flash('You are now logged in!')
            return redirect(url_for('index'))
        return render_template('login.html', form=form)
    except:
        abort(404)

@app.route('/logout')
def logout():
    try:
        logout_user()
        return redirect(url_for('index'))
    except:
        abort(404)

# initialize errors
@app.errorhandler(404)
def _404(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def _500(e):
    return render_template('errors/500.html'), 404

# setting posts
def format_post(item):
    bits = item.split('_', 1)
    date = datetime.strptime(bits[0], '%Y%m%d')
    title = bits[1].replace('_', ' ').replace('.md', '').title()
    slug = title.lower().replace(' ', '-')
    return {'date': date, 'title': title, 'slug': slug}

def get_post_dir():
    return os.path.dirname(os.path.abspath(__file__)) + '/templates/posts'

def get_post_items():
    items = os.listdir(get_post_dir())
    items.sort(reverse=True)
    return items
   
def get_posts():
    posts = []
    for item in get_post_items():
        if item[0] == '.' or item[0] == '_':
            continue
        post = format_post(item)
        posts.append(post)
    return posts

@app.template_filter('date_format')
def date_format(timestamp):
    def suffix(d):
        return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')
    def custom_format(format, t):
        return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))
    return custom_format('%B {S}, %Y', timestamp)

@app.route('/posts')
def posts():
    try:
        return render_template('posts.html', posts=get_posts())
    except:
        abort(404)
    
@app.route('/page/<slug>')
def page(slug):
    try:
        cache_key = 'page:%s' % slug
        template = cache.get(cache_key)
        if template is None:
            clean_slug = slug.replace('-', '_')
            content = app.open_resource('templates/pages/%s.md' % clean_slug, 'r').read()
            content = Markup(markdown(content))
            title = slug.replace('-', ' ').title()
            template = render_template('page.html', content=content, page_title=title)
            cache.set(cache_key, template)
        return template
    except:
        abort(404)

@app.route('/post/<slug>')
def post(slug):
    try:
        cache_key = 'post:%s' % slug
        template = cache.get(cache_key)
        if template is None:
            clean_slug = slug.replace('-', '_')
            post = None          
            content = app.open_resource('templates/posts/%s' % post, 'r').read()
            content = Markup(markdown(content))
            title = format_post(post)['title']
            template = render_template('post.html', content=content, page_title=title)
            cache.set(cache_key, template)
        return template
    except:
        abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
