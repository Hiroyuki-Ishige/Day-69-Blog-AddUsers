from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


##WTForms
#Blog form
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


#User registration form
class Form_NewUserReg(FlaskForm):
    email = StringField(label="email", validators=[DataRequired()])
    password = StringField(label="Password", validators=[DataRequired()])
    name = StringField(label="Name", validators=[DataRequired()])
    add_user = SubmitField(label='SIGN Me UP!')

#User login form
class User_login(FlaskForm):
    email = StringField(label="email", validators=[DataRequired()])
    password = StringField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label='Log in')

#Comment form
class Comment_Form(FlaskForm):
    text = CKEditorField("comment", validators=[DataRequired()])
    submit = SubmitField(label='Submit comment')
