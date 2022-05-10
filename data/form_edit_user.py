from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, BooleanField
from wtforms.validators import DataRequired


class EditUserForm(FlaskForm):
    username = StringField('Новое Имя', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль')
    confirm_new_password = PasswordField('Подтвердить новый пароль')
    description = StringField('Описание(статус) профиля')
    avatar = FileField("Фото вашего профиля")
    delete_avatar = BooleanField('Удалить фото профиля')
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')
