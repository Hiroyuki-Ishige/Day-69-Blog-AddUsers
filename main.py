from flask import Flask, render_template, redirect, url_for, flash, request, g
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, table
from sqlalchemy.orm import relationship, Session, declarative_base
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, Form_NewUserReg, User_login, Comment_Form
from flask_gravatar import Gravatar
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL
from flask_migrate import Migrate
from functools import wraps
import hashlib
import os

app = Flask(__name__)
#This SECRET_KEY is used at local development
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

#This SECRET_KEY is used at HEROKU deployment
# app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config["WTF_CSRF_ENABLED"] = True
ckeditor = CKEditor(app)
Bootstrap(app)

# Create SQLite database (this is used at local only)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

#Set database after HEROKU deployment
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///blog.db")
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://zahxfbxoaztmvs:ff36dcf61ca45eee12247ee2a4093bdc4cf3990aaeaced3f2e5610c36e93e7ca@ec2-34-197-84-74.compute-1.amazonaws.com:5432/d6p4ujefhed2pe"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db.init_app(app)

Base = declarative_base()


# Create TABLES in DB
# Table for user registration. "UserMixin" is used for log in session control.
class Users(UserMixin, db.Model, Base):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)

    # Create parent relationship with Class "BlogPost" The "posts" isn't shown as column name in data table.
    posts = relationship("BlogPost", back_populates="author")
    # Create parent relationship with Class "Comment" The "comments" isn't shown as column name in data table.
    comments = relationship("Comment", back_populates="comment_author")


# Table for blogs
class BlogPost(db.Model, Base):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, ForeignKey('Users.id'))

    # Create child relationship to the Users object, the "posts" refers to the posts property in the Users class.
    # The "author" isn't shown as column name in data table.
    author = relationship("Users", back_populates="posts")

    # Create parent relationship with Class "Comment" The "comments" isn't shown as column name in data table.
    comments = relationship("Comment", back_populates="parent_post")


# Table for comment
class Comment(db.Model, Base):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    # Create Foreign Key, "users.id" the users refers to the table name of User.
    author_id = db.Column(db.Integer, ForeignKey('Users.id'))

    # Create Foreign Key to "blog_posts.id" referring to table "blog_posts".
    post_id = db.Column(db.Integer, ForeignKey('blog_posts.id'))

    # *********Add child relationthip**********#
    # Create child relationship to the Users object, the "comments" refers to the comment property in the Users class.
    # The "author" isn't shown as column name in data table.
    comment_author = relationship("Users", back_populates="comments")

    # Create child relationship to the BlogPost object, the "comments" refers to the comments property in BlogPost class.
    # "comments" isn't shown as column name in data table.
    parent_post = relationship("BlogPost", back_populates="comments")


# Create data table
with app.app_context():
    db.create_all()

##Set up login status control
# to tie up flask login with app
login_manager = LoginManager()
login_manager.init_app(app)


# Create @admin_only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id == 1:
            return f(*args, **kwargs)
            # posts = BlogPost.query.all()
        return redirect(url_for("get_all_posts"))
        # return render_template('404.html'), 404

    return decorated_function


# To get info of user in login status
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#Create Avatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# Ensure templates are auto-reloaded
# app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route('/')
def get_all_posts():
    if current_user == True:
        posts = BlogPost.query.all()
        users = Users.query.all()
        return render_template("index.html", all_posts=posts, all_users=users, user_name=current_user.name)
    else:
        posts = BlogPost.query.all()
        users = Users.query.all()
        return render_template("index.html", all_posts=posts, all_users=users, )


@app.route('/register', methods=["GET", "POST"])
def register():
    form_NewUserReg = Form_NewUserReg()

    if request.method == "GET":
        return render_template('register.html', form=form_NewUserReg, )

    if request.method == "POST":
        if form_NewUserReg.validate_on_submit():

            # Judge if there is same email registration
            email = form_NewUserReg.email.data

            # if email exist
            if Users.query.filter_by(email=email).first():
                return render_template("login.html", form=User_login(),
                                       error="This email already exist. Please longin or register by another email")


            else:
                # hash password
                hash_and_salted_password = generate_password_hash(
                    form_NewUserReg.password.data,
                    method='pbkdf2:sha256',
                    salt_length=8
                )

                new_user = Users(
                    email=form_NewUserReg.email.data,
                    password=hash_and_salted_password,
                    name=form_NewUserReg.name.data,
                )

                db.session.add(new_user)
                db.session.commit()

                # Bring newly registered user into home page
                login_user(new_user)
                # posts = BlogPost.query.all()
                return redirect(url_for("get_all_posts"))


@app.route('/login', methods=["GET", "POST"])
def login():
    form = User_login()

    if request.method == "GET":
        return render_template("login.html", form=form)

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # get data from DB, which matches email
        user = Users.query.filter_by(email=email).first()

        # if email doesn't esist
        if user == None:
            return render_template("login.html", form=User_login(), error="Your email doesn't exist")

        # Check password and if ok
        elif check_password_hash(user.password, password):
            login_user(user)
            posts = BlogPost.query.all()
            # user_id = user.id
            # user_name = user.name
            return render_template("index.html", all_posts=posts, user_id=user.id, user_name=current_user.name)

        # if password doesn't match
        else:
            return render_template("login.html", form=User_login(), error="Your password incorrect. Please try again!")

    # else:
    #     return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id, ):
    requested_post = BlogPost.query.get(post_id)
    form = Comment_Form()
    all_comments = Comment.query.filter_by(post_id=post_id)

    if request.method == "GET":

        return render_template("post.html", post=requested_post, user_id=current_user, form=form,
                               all_comments=all_comments)

    if request.method == "POST":
        try:
            if form.validate_on_submit():
                # author_name = Users.query.filter_by(email=current_user.name).first()
                new_comment = Comment(
                    text=form.text.data,
                    author_id=current_user.id,
                    post_id=requested_post.id,
                )

                db.session.add(new_comment)
                db.session.commit()
                return redirect(url_for("get_all_posts"))


        except:
            flash("Please log in before sending comment!!")
            return redirect(url_for("login", ))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()

    if request.method == "POST":
        if form.validate_on_submit():
            author_name = Users.query.filter_by(email=current_user.name).first()
            new_post = BlogPost(
                title=form.title.data,
                subtitle=form.subtitle.data,
                date=date.today().strftime("%B %d, %Y"),
                body=form.body.data,
                img_url=form.img_url.data,
                author_id=current_user.id,

            )
            print(form.title.data)
            print(date.today().strftime("%B %d, %Y"))
            print(current_user.name)

            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form, user_name=current_user.name)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if request.method == "POST":
        if edit_form.validate_on_submit():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            # post.author = edit_form.author.data
            post.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
