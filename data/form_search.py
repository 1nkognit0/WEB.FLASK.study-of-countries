from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.fields.html5 import SearchField


class SearchForm(FlaskForm):
    search_string = SearchField()
    search_btn = SubmitField('Искать')
