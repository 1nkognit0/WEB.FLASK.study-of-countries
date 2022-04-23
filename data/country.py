import sqlalchemy
from .db_session import SqlAlchemyBase


class Country(SqlAlchemyBase):
    __tablename__ = 'info'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    capital = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    language = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    form_government = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    territory = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    population = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    density = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    flag = sqlalchemy.Column(sqlalchemy.String, nullable=True)
