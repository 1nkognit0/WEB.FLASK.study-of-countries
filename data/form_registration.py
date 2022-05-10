from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердить пароль', validators=[DataRequired()])
    description = StringField('Описание(статус) профиля (необязательно)')
    avatar = FileField("Фото вашего профиля (необязательно)")
    submit = SubmitField('Регистрация')
