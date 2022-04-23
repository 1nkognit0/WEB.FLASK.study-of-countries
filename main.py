from flask import Flask, render_template, request
from data import db_session
from data.country import Country
from data.form_button import ButtonForm
from random import choice, randint
from data.form_search import SearchForm
import os

app = Flask(__name__)

# ключ
app.config['SECRET_KEY'] = 'some_key'

# переменные для викторины(Обнуляются во всех обработчиках, чтобы исключить возможное сохраниние прогресса)
score_quiz = 0
win_score_quiz = 0
progress_on_quiz = ['black' for _ in range(10)]
progress_on_quiz_copy = progress_on_quiz.copy()

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


@app.route('/quizzes')
def quiz():
    global score_quiz, win_score_quiz, progress_on_quiz
    score_quiz = 0
    win_score_quiz = 0
    progress_on_quiz = progress_on_quiz_copy.copy()
    return render_template('quizzes.html')


@app.route('/quizzes/capital', methods=['GET', 'POST'])
def quiz_capitals():
    info = form_for_quizzes()
    if info[0] == 'run':
        return render_template('quiz-capital.html',
                               form=info[1], correct=info[2][0], buttons=info[3], progress=progress_on_quiz)
    else:
        return render_template('results.html', win=info[1])


@app.route('/quizzes/flag', methods=['GET', 'POST'])
def flag_page():
    info = form_for_quizzes()
    if info[0] == 'run':
        return render_template('quiz-flag.html',
                               form=info[1], correct=info[2][0], buttons=info[3], progress=progress_on_quiz)
    else:
        return render_template('results.html', win=info[1])


def form_for_quizzes():
    form = ButtonForm()
    countries = session.query(Country).all()
    options = [choice(countries) for _ in range(4)]

    form.correct_option.label.text = options[0].name
    form.option2.label.text = options[1].name
    form.option3.label.text = options[2].name
    form.option4.label.text = options[3].name

    if request.method == 'POST':
        global score_quiz, win_score_quiz, progress_on_quiz
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
    return ['run', form, options, buttons]


port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port, debug=True)
