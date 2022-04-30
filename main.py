from flask import Flask, render_template, url_for, redirect, request
from random import choice, randint
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data.form_registration import RegisterForm
from data.form_login import LoginForm
from data.users import User

import os

from data import db_session
from data.country import Country

from data.form_button import ButtonForm
from data.form_search import SearchForm

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
parts_of_world = ['Все', 'Африка', 'Северная Америка', 'Южная Америка', 'Европа', 'Австралия и Океания', 'Азия']
select_option = 'Все'
wrong_options = []
correct_options = []

form_government = ['Конституционная монархия', 'Парламентская республика', 'Президентская республика',
                   'Смешанная республика', 'Абсолютная монархия', 'Социалистическая республика', 'Исламская республика']

# подключение к базе
db_session.global_init('db/CountryDB.db')
session = db_session.create_session()


@app.route('/<string:name>')
def certain_country(name):
    if name == 'favicon.ico':
        return
    global score_quiz, win_score_quiz, progress_on_quiz
    score_quiz = 0
    win_score_quiz = 0
    progress_on_quiz = progress_on_quiz_copy.copy()
    country = session.query(Country).filter(Country.name == name).first()

    return render_template('country.html', data=country)


@app.route('/sorting/<string:sort>')
def parts_country(sort):
    global score_quiz, win_score_quiz, progress_on_quiz
    score_quiz = 0
    win_score_quiz = 0
    progress_on_quiz = progress_on_quiz_copy.copy()

    if sort in parts_of_world:
        countries = session.query(Country).filter(Country.parts_of_world == sort).all()
    elif sort in form_government:
        countries = session.query(Country).filter(Country.form_government == sort).all()
    else:
        countries = session.query(Country).filter(Country.language == sort).all()

    return render_template('part_selection.html', data=countries, name=sort)


@app.route('/', methods=['GET', 'POST'])
def main_page():
    global score_quiz, win_score_quiz, progress_on_quiz
    score_quiz = 0
    win_score_quiz = 0
    progress_on_quiz = progress_on_quiz_copy.copy()

    form = SearchForm()
    if request.method == 'POST':
        post = [name for name in request.form.items()]
        countries = session.query(Country).filter(Country.name.contains(post[0][1])).all()
    else:
        countries = session.query(Country).all()

    return render_template('index.html', form=form, data=countries)


@app.route('/quizzes', methods=['GET', 'POST'])
def quizzes():
    global score_quiz, win_score_quiz, progress_on_quiz, select_option
    score_quiz = 0
    win_score_quiz = 0
    progress_on_quiz = progress_on_quiz_copy.copy()

    if request.method == 'POST':
        select_option = [name for name in request.form.items()][0][1]
    return render_template('quizzes.html', select=select_option, parts=parts_of_world)


@app.route('/quizzes/capital', methods=['GET', 'POST'])
def quiz_capitals():
    info = form_for_quizzes()
    if info[0] == 'run':
        return render_template('quiz-capital.html',
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


def form_for_quizzes():
    form = ButtonForm()
    global score_quiz, win_score_quiz, progress_on_quiz

    options, correct = search_options()

    form.correct_option.label.text = correct[score_quiz].name
    form.option2.label.text = options[score_quiz][0].name
    form.option3.label.text = options[score_quiz][1].name
    form.option4.label.text = options[score_quiz][2].name

    if request.method == 'POST':
        answer = [name for name in request.form]
        if answer[0] == 'correct_option':
            win_score_quiz += 1
            progress_on_quiz[score_quiz] = 'green'
        else:
            progress_on_quiz[score_quiz] = 'red'
        score_quiz += 1
        if score_quiz == 10:
            score_quiz = 0
            win = win_score_quiz
            win_score_quiz = 0
            progress_on_quiz = progress_on_quiz_copy.copy()
            return ['end', win]
    # использую randint чтобы сделать рандомную последоватльность вывода кнопок(способа лучше не нашёл)
    buttons = randint(1, 4)
    return ['run', form, correct[score_quiz], buttons]


# функция для генерации вопросов на викторине
def search_options():
    global wrong_options, correct_options, select_option
    if select_option == 'Все':
        countries = session.query(Country).all()
    else:
        countries = session.query(Country).filter(Country.parts_of_world == select_option).all()

    for count in range(10):
        correct_options.append(choice(countries))
        wrong_options.append([])
        while len(wrong_options[count]) < 3:
            opt = choice(countries)
            if opt != correct_options[count]:
                wrong_options[count].append(opt)
    return wrong_options, correct_options


@app.route('/reg', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            return render_template('reg.html', form=form, pas_err='Пароли не совпадают')

        if session.query(User).filter(User.login == form.username.data).first():
            return render_template('reg.html', form=form, user_err='Такой пользователь уже существует')
        user = User(login=form.username.data)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect(url_for('login_page'))
    return render_template('registration.html', form=form)


@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
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


port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port, debug=True)
