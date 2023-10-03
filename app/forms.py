from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, TextAreaField, DateTimeField 
from flask_wtf import FlaskForm
from wtforms.validators import ValidationError, Email, EqualTo, InputRequired, Length, DataRequired
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_verify = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
        
class EventForm(FlaskForm):
#     id = StringField('Event ID', validators=[DataRequired()])

    event_name = StringField('Event Name', validators=[DataRequired()])

    event_street = StringField('Event Street', validators=[DataRequired()])
        
    event_city = StringField('Event City', validators=[DataRequired()])
    
    event_state = StringField('Event State', validators=[DataRequired()])
   
    event_country = SelectField(
        u'Event Country',
        choices = [('Canada', 'Canada'), ('United States', 'United States')],
        validators=[InputRequired()]
    )

    event_postalcode = StringField('Event Postal Code', validators=[DataRequired()])   

    event_type = StringField('Event Type', validators=[DataRequired()])  

    event_date = DateField('Event Date', format='%Y-%m-%d')

    event_duration = StringField('Event Duration', validators=[DataRequired()]) 

    adding = SubmitField(label = 'Add Event')

    updating = SubmitField(label = 'Update Event')