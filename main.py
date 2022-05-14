from flask import Flask, render_template, url_for, redirect, request, jsonify
from random import choice, randint
import datetime
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data.users import User

import os
from shutil import copy, rmtree

from data import db_session
from data.country import Country

from data.form_button import ButtonForm
from data.form_search import SearchForm
from data.form_registration import RegisterForm
from data.form_login import LoginForm
from data.form_edit_user import EditUserForm


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

# ключ
app.config['SECRET_KEY'] = 'some_key'

# переменные нужные для правильной работы викторины
score_quiz = 0
win_score_quiz = 0
progress_on_quiz = ['black' for _ in range(10)]
progress_on_quiz_copy = progress_on_quiz.copy()
PARTS_OF_WORLD = ['Все', 'Африка', 'Северная Америка', 'Южная Америка', 'Европа', 'Австралия и Океания', 'Азия']
select_option = 'Все'
wrong_options = []
correct_options = []

FORM_GOVERNMENT = ['Конституционная монархия', 'Парламентская республика', 'Президентская республика',
                   'Смешанная республика', 'Абсолютная монархия', 'Социалистическая республика', 'Исламская республика']

# подключение к базе
db_session.global_init('db/CountryDB.db')
session = db_session.create_session()
ALL_COUNTRIES = session.query(Country).all()


@app.route('/http-api')
def database_return():
    return jsonify(
        {
            'counties':
                [county.as_dict() for county in ALL_COUNTRIES[:10]]

        }
    )


@app.route('/leaderboard')
def leaderboard():
    reset_data()
    users = session.query(User.login, User.amount_quiz, User.correct_answers).all()

    sorted_users = [user for user in users if user[1] != 0]
    leaders = sorted(sorted_users, key=lambda x: (x[2], x[1]))

    for place, user in enumerate(leaders[::-1]):
        leaders[place] = (place + 1, user[0], user[1], user[2])

    return render_template('leaderboard.html', leaders=leaders)


@app.route('/country/<string:name>')
def certain_country(name):
    reset_data()
    country = session.query(Country).filter(Country.name == name).first()

    return render_template('country.html', data=country)


@app.route('/sorting/<string:sort>')
def parts_country(sort):
    reset_data()

    if sort in PARTS_OF_WORLD:
        countries = session.query(Country).filter(Country.parts_of_world == sort).all()
    elif sort in FORM_GOVERNMENT:
        countries = session.query(Country).filter(Country.form_government == sort).all()
    else:
        countries = session.query(Country).filter(Country.language == sort).all()

    return render_template('part_selection.html', data=countries, name=sort)


@app.route('/profile/<nickname>')
def profile_page(nickname):
    reset_data()

    info = session.query(User).filter(User.login == nickname).first()
    wins = '-'

    days = (datetime.datetime.now() - info.created_date).days
    if info.amount_quiz != 0:
        wins = str(int((info.correct_answers / (info.amount_quiz * 10)) * 100)) + '%'

    return render_template('profile.html', data=info, days=days, wins=wins)


@app.route('/edit/<nickname>',  methods=['GET', 'POST'])
def edit_user(nickname):
    reset_data()
    form = EditUserForm()
    if request.method == "GET":
        user = session.query(User).filter(User.login == nickname).first()
        if user:
            form.username.data = user.login
            form.description.data = user.description

    if form.validate_on_submit():
        user = session.query(User).filter(User.login == nickname).first()
        user.description = form.description.data
        img = form.avatar.data

        if not user.check_password(form.password.data):
            return render_template('edit_user.html', message='Неверный пароль', form=form)

        if form.new_password.data and form.confirm_new_password.data:
            if form.new_password.data != form.confirm_new_password.data:
                return render_template('edit_user.html', form=form, pas_err='Пароли не совпадают')
            user.set_password(form.new_password.data)

        if user.login != form.username.data:
            if session.query(User).filter(User.login == form.username.data).first():
                return render_template('edit_user.html', form=form, user_err='Такой пользователь уже существует')
            dir_img = f'static/img/avatar/{form.username.data}'
            if img.filename or form.delete_avatar.data:
                rmtree(f'static/img/avatar/{user.login}')
                os.makedirs(dir_img)
        else:
            dir_img = f'static/img/avatar/{user.login}'
            if img.filename or form.delete_avatar.data:
                os.remove(user.avatar[3:])
        if img.filename or form.delete_avatar.data:
            if form.delete_avatar.data:
                copy('static/img/avatar/default/default.jpg', f'{dir_img}/default.jpg')
                full_path_img = f'{dir_img}/default.jpg'
            else:
                full_path_img = f'{dir_img}/{img.filename}'
                img.save(full_path_img)
            user.avatar = f'../{full_path_img}'

        user.login = form.username.data
        session.commit()

        return redirect(f'../profile/{form.username.data}')

    return render_template('edit_user.html', form=form)


@app.route('/', methods=['GET', 'POST'])
def main_page():
    reset_data()

    form = SearchForm()
    if request.method == 'POST':
        post = [name for name in request.form.items()]
        countries = session.query(Country).filter(Country.name.contains(post[0][1])).all()
    else:
        countries = ALL_COUNTRIES

    return render_template('index.html', form=form, data=countries)


@app.route('/quizzes', methods=['GET', 'POST'])
def quizzes():
    reset_data()

    global select_option

    if request.method == 'POST':
        select_option = [name for name in request.form.items()][0][1]
    return render_template('quizzes.html', select=select_option, parts=PARTS_OF_WORLD)


@app.route('/quizzes/capital', methods=['GET', 'POST'])
def quiz_capitals():
    info = form_for_quizzes()
    if info[0] == 'run':
        return render_template('quiz-capital.html',
                               form=info[1], correct=info[2], buttons=info[3], progress=progress_on_quiz)
    else:
        return render_template('results.html', win=info[1])


@app.route('/quizzes/government', methods=['GET', 'POST'])
def quiz_governments():
    info = form_for_quizzes()
    if info[0] == 'run':
        return render_template('quiz-government.html',
                               form=info[1], correct=info[2], buttons=info[3], progress=progress_on_quiz)
    else:
        return render_template('results.html', win=info[1])


@app.route('/quizzes/flag', methods=['GET', 'POST'])
def quiz_flags():
    info = form_for_quizzes()
    if info[0] == 'run':
        return render_template('quiz-flag.html',
                               form=info[1], correct=info[2], buttons=info[3], progress=progress_on_quiz)
    else:
        return render_template('results.html', win=info[1])


@app.route('/quizzes/survive-capital', methods=['GET', 'POST'])
def quiz_survive_capitals():
    info = form_for_survive()
    if info[0] == 'run':
        return render_template('survive-capital.html',
                               form=info[1], correct=info[2], buttons=info[3], progress=progress_on_quiz)
    else:
        return render_template('survive-result.html', win=info[1])


@app.route('/quizzes/survive-flag', methods=['GET', 'POST'])
def quiz_survive_flag():
    info = form_for_survive()
    if info[0] == 'run':
        return render_template('survive-flag.html',
                               form=info[1], correct=info[2], buttons=info[3], progress=progress_on_quiz)
    else:
        return render_template('survive-result.html', win=info[1])


def form_for_survive():
    form = ButtonForm()
    global score_quiz, win_score_quiz, progress_on_quiz, wrong_options, correct_options

    if not bool(wrong_options):
        search_options()

    if request.method == 'POST':
        answer = [name for name in request.form]
        win = win_score_quiz
        if answer[0] == 'correct_option':
            win_score_quiz += 1
        else:
            return ['end', win]
        if score_quiz >= 100:
            win = win_score_quiz
            reset_data()
            if current_user.is_authenticated:
                user = session.query(User).filter(User.login == current_user.login).first()
                user.amount_quiz += 1
                user.correct_answers += win
                session.commit()

    form.correct_option.label.text = correct_options[score_quiz].name
    form.option2.label.text = wrong_options[score_quiz][0].name
    form.option3.label.text = wrong_options[score_quiz][1].name
    form.option4.label.text = wrong_options[score_quiz][2].name

    # randint используется чтобы сделать рандомную последоватльность вывода кнопок
    buttons = randint(1, 4)
    score_quiz += 1
    return ['run', form, correct_options[score_quiz - 1], buttons]


def form_for_quizzes():
    form = ButtonForm()
    global score_quiz, win_score_quiz, progress_on_quiz, wrong_options, correct_options

    if not bool(wrong_options):
        search_options()

    if request.method == 'POST':
        answer = [name for name in request.form]
        if answer[0] == 'correct_option':
            win_score_quiz += 1
            progress_on_quiz[score_quiz - 1] = 'green'
        else:
            progress_on_quiz[score_quiz - 1] = 'red'
        if score_quiz >= 10:
            win = win_score_quiz
            reset_data()
            if current_user.is_authenticated:
                user = session.query(User).filter(User.login == current_user.login).first()
                user.amount_quiz += 1
                user.correct_answers += win
                session.commit()

            return ['end', win]

    form.correct_option.label.text = correct_options[score_quiz].name
    form.option2.label.text = wrong_options[score_quiz][0].name
    form.option3.label.text = wrong_options[score_quiz][1].name
    form.option4.label.text = wrong_options[score_quiz][2].name


    # randint используется чтобы сделать рандомную последоватльность вывода кнопок
    buttons = randint(1, 4)
    score_quiz += 1
    return ['run', form, correct_options[score_quiz - 1], buttons]


# функция для генерации вопросов на викторине
def search_options():
    global wrong_options, correct_options, select_option

    if select_option == 'Все':
        countries = ALL_COUNTRIES
    else:
        countries = session.query(Country).filter(Country.parts_of_world == select_option).all()

    for count in range(10):
        while True:
            correct_options.append(choice(countries))
            if correct_options[-1] not in correct_options[0:len(correct_options) - 1]:
                break
            else:
                del correct_options[-1]
        wrong_options.append([])
        while len(wrong_options[count]) < 3:
            opt = choice(countries)
            if opt != correct_options[count]:
                wrong_options[count].append(opt)


@app.route('/reg', methods=['GET', 'POST'])
def register_page():
    reset_data()
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            return render_template('registration.html', form=form, pas_err='Пароли не совпадают')

        if session.query(User).filter(User.login == form.username.data).first():
            return render_template('registration.html', form=form, user_err='Такой пользователь уже существует')
        user = User()
        user.login = form.username.data
        user.set_password(form.password.data)
        user.description = form.description.data

        img = form.avatar.data
        dir_img = f'static/img/avatar/{form.username.data}'
        if not os.path.isdir(dir_img):
            os.makedirs(dir_img)
        if img:
            full_path_img = f'{dir_img}/{img.filename}'
            img.save(full_path_img)
        else:
            copy('static/img/avatar/default/default.jpg', f'{dir_img}/default.jpg')
            full_path_img = f'{dir_img}/default.jpg'
        user.avatar = f'../{full_path_img}'

        session.add(user)
        session.commit()
        return redirect(url_for('login_page'))
    return render_template('registration.html', form=form)


@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    reset_data()
    form = LoginForm()
    if form.validate_on_submit():
        user = session.query(User).filter(User.login == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message='Неверный логин или пароль', form=form)
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect('/')


def reset_data():
    global score_quiz, win_score_quiz, progress_on_quiz, wrong_options, correct_options
    score_quiz = 0
    win_score_quiz = 0
    progress_on_quiz = progress_on_quiz_copy.copy()
    wrong_options = []
    correct_options = []


port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port, debug=True)
