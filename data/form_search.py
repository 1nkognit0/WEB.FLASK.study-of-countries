from flask_wtf import FlaskForm
from wtforms import SubmitField, SearchField


class SearchForm(FlaskForm):
    search_string = SearchField()
    search_btn = SubmitField('Искать')
