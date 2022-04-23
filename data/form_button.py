from flask_wtf import FlaskForm
from wtforms import SubmitField


class ButtonForm(FlaskForm):
    correct_option = SubmitField('1')
    option2 = SubmitField('2')
    option3 = SubmitField('3')
    option4 = SubmitField('4')
