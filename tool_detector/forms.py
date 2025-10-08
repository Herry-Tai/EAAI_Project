from wtforms import Form, StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional

class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])

class UserForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=128)])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    active = BooleanField('Active')
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])

class RoleForm(Form):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
