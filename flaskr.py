import os
import sqlite3
import re
from typing import Optional, Match
import random
import string

from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime




UPLOAD_FOLDER = '\\Progects\\flaskr_n\\img\\'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


# конфигурация
# DATABASE = 'data_.db'
# DEBUG = True
# SECRET_KEY = 'development key'
# USERNAME = 'admin'
# PASSWORD = 'default'

# далее, мы должны создать наше текущее приложение и инициализировать
# его в помощью конфигурации из того же файла, т. е. flaskr.py:
# создаём наше маленькое приложение :)

app = Flask(__name__)
#wsgi_app = app.wsgi_app
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Загружаем конфиг по умолчанию и переопределяем в конфигурации часть
# значений через переменную окружения
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'data_.db'),
    DEBUG=True,
    SECRET_KEY='development key'))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)


# Объект Config работает подобно словарю, поэтому мы можем обновлять его с помощью новых значений.

"""обавим также метод, который позволяет простым способом соединиться с указанной базой данных.
 Он может быть использован для открытия соединения по запросу, а также из интерактивной командной 
 оболочки Python или из скрипта. Это пригодится в дальнейшем. Мы создаём простое соединение 
 с базой данных SQLite и далее просим его использовать для представления строк объект sqlite3.Row.
  Это позволит нам рассматривать строки, как если бы они были словарями, а не кортежами."""


def connect_db():
    print("connect_db")
    print(app.config['DATABASE'])
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


"""функцию с именем init_db, которая инициализирует базу данных. Позвольте, я сперва покажу вам код. 
Просто добавьте в flaskr.py эту функцию после функции connect_db:"""


def init_db(db):
    with app.open_resource('shema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()
    print('Initialized the database.')

    """ Метод open_resource() объекта откроет ресурс, обеспечиваемый приложением. 
    Эта функция открывает файл из места расположения ресурсов 
    (в нашем случае папка flaskr_n), и позволяет вам из него читать """


# Всё, что вам надо знать на этот момент - это то,
# что вы можете безопасно сохранять информацию в объекте g.


def get_db():
    """Если ещё нет соединения с базой данных, открыть новое - для
    текущего контекста приложения
    :rtype: object"""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
        init_db(g.sqlite_db)
    return g.sqlite_db


"""Flask обеспечил нас декоратором teardown_appcontext(). Он выполняется каждый раз, 
когда происходит разрыв контекста приложения:"""


@app.teardown_appcontext
def close_db(error):
    """Функция, обозначенная как teardown_appcontext() вызывается каждый раз при разрыве контекста приложения."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


"""Функция представления передаёт записи в виде словаря шаблону list_product.html
и возвращает сформированное отображение:"""


@app.route('/', methods=["GET"])
def list_product():
    products = get_products()

    if not session.get('logged_in'):
        return render_template('list_product.html', products=products, basket=[])

    product_list = []

    for i in products:
        print(i['id'])
        im = i['id']
        db = get_db()
        existingImage = db.execute(
            'select img '
            'from image '
            'where product_id=? ', [im])

        one_product = {}
        one_product['id'] = i['id']
        one_product['name'] = i['name']
        one_product['model'] = i['model']
        one_product['price'] = i['price']
        one_product['quantity'] = i['quantity']
        one_product['img'] = existingImage.fetchone()['img']

        product_list.append(one_product)

    return render_template('list_product.html', products=product_list, basket=get_basket(), error=None)

""" def product_list():
    products = get_products()
    product_list=[]

    for i in products:
        print(i['id'])
        im = i['id']
        db = get_db()
        existingImage = db.execute(
            'select img '
            'from image '
            'where product_id=? ', [im])

        one_product = {}
        one_product['id'] = i['id']
        one_product['name'] = i['name']
        one_product['model'] = i['model']
        one_product['price'] = i['price']
        one_product['quantity'] = i['quantity']
        one_product['img'] = existingImage.fetchone()['img']

        product_list.append(one_product)
"""


def get_basket():

    return get_db().execute(
        'select '
        'p.name as name, '
        'p.model as model, '
        'b.quantity as quantity, '
        'b.id as basket_Id, '
        'p.price as price, '
        '(p.price * b.quantity) as cost '
        'from basket b, products p '
        'where b.productsId = p.id '
        'and b.userId=?',
        [session['userId']]).fetchall()


def get_products(): #-> object:
    return get_db().execute(
        'select * from products '
        'order by id desc').fetchall()


def allowed_file(filename):

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_random_alphanumeric_str(length):
    leters_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(leters_digits) for i in range(length)))


    print(result_str)
    return result_str


@app.route('/', methods=["GET", "POST"])
def add_super_product():
    if not session.get('logged_in'):

        abort(401)

    if request.method == 'POST':
        filename = None

        # check if the post request has the file part
        if 'img' not in request.files:

            flash('No file part')
            #return redirect(request.url)
            return render_template('list_product.html', products=get_products(), basket=get_basket(), error="No file part")

        file = request.files['img']
        # if user does not select file, browser also
        # submit an empty part without filename

        if file.filename == '':
            flash('No select file')
            #return redirect(request.url)
            return render_template('list_product.html', products=get_products(), basket=get_basket(), error="No select file")

        if file and allowed_file(file.filename):

            filename = get_random_alphanumeric_str(5) + '_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        price = request.form['price']
        result = re.match(r"^\d+\.\d{2}$", price)
        quantity = request.form['quantity']
        result1 = re.match(r"\d+$", quantity)
        model = request.form['model']
        result2 = re.match(r"^\w+$", model)
        name = request.form['name']
        result3 = re.match(r"^\w+$", name)

        if result:
            print("ok")
        else:
            print("error")

        error = None

        if not result or not result1 or not result2 or not result3:
            flash("Please enter valid data")

            return render_template('list_product.html', products=get_products(), basket=get_basket(), error="Please enter valid data")

        db = get_db()

        cur = db.cursor()  # створюємо змінну cursor і присвоюємо значення функції db.cursor() для курсора
        cur.execute(
            'insert into products(name, model, price, quantity)'
            ' values (?, ?, ?, ?)',
            [name, model, price, quantity])



        # db.commit()

        qqq = cur.lastrowid  # lastrowid - атрибут обєкта cursor, щоб повернути останній згенерований ідентифікатор id.
                                        # створюємо змінну product_id і присвоюємо значення cursor.lastrowid
        print(qqq)

        db = get_db()
        cur = db.cursor()
        cur.execute(
            'insert into image(product_id, img)'
            'values (?, ?)', [qqq, filename])
        db.commit()


    return redirect(url_for('list_product'))

"""Это представление позволяет пользователю, если он осуществил вход, добавлять
новые записи. Оно реагирует только на запросы типа POST, а фактическая форма
отображается на странице list_product."""


"""@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    db.execute(
        'insert into products(name, model, price, quantity)'
        ' values (?, ?, ?, ?)',
        [request.form['name'], request.form['model'],
         request.form['price'], request.form['quantity']])
    price = request.form['price']
    result = re.fullmatch(r"^\d+\.\d{2}$", price)

    if not result:
        return redirect(url_for('list_product', e="Please enter valid data"))
    else:
        db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('list_product'))
"""


@app.route('/picture/<xyz>', methods=['GET'])
def get_image(xyz):

    filename = xyz

    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        abort(404)
    return redirect(url_for('list_product'))

@app.route('/delete-product', methods=['POST'])
def delete_product():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute(
        'delete from products '
        'where id=?', [request.form['id']])
    db.execute(
        ' delete from image'
        ' where product_id=?', [request.form['id']])
    db.commit()
    return redirect(url_for('list_product'))


@app.route('/add_basket', methods=['POST'])
def add_basket():
    if not session.get('logged_in'):
        return render_template('list_product.html', products=[], basket=[])
    db = get_db()
    cur = db.execute(
        'select quantity '
        'from products where id = ?',
        [request.form['id']])
    quantityInStock = int(cur.fetchone()[0])
    print('quantiytInStock = ' + str(quantityInStock))
    quantityToBuy = int(request.form['quantity'])
    print('quantityToBuy = ' + str(quantityToBuy))

    if quantityInStock < quantityToBuy:
        flash('There are not enough goods stock!')
        return redirect(url_for('list_product'))

    quantityInStock = quantityInStock - quantityToBuy

    print('quantityInStock = ' + str(quantityInStock))

    db.execute(
        'update products '
        'set quantity = ? '
        'where id = ?',
        [quantityInStock, request.form['id']])

    existingProduct = db.execute(
        'select id '
        'from basket '
        'where userId = ? and productsId = ?',
        [session['userId'], request.form['id']])

    bask = existingProduct.fetchone()

    if bask:
        db.execute(
            'update basket '
            'set quantity = quantity + ? '
            'where id = ? ', [quantityToBuy, bask['id']])
    else:
        db.execute(
            'insert into basket ('
            'productsId, quantity, userId) '
            'values (?, ?, ?)',
            [request.form['id'], request.form['quantity'],
             session['userId']])

    db.commit()
    return redirect(url_for('list_product'))


@app.route('/delete_basket', methods=['POST'])
def delete_basket():
    if not session.get('logged_in'):
        return render_template('list_product.html', basket=[], products=[])
    db = get_db()
    cur = db.execute(
        'select productsId, quantity '
        'from basket where id=?',
        [request.form['id']])
    row = cur.fetchone()
    productsId = int(row[0])
    returnQty = int(row[1])

    db.execute(
        'delete from basket '
        'where id = ?', [request.form['id']])
    db.execute(
        'update products set quantity = quantity + ? '
        'where id = ?',
        [returnQty, productsId])

    db.commit()
    return redirect(url_for('list_product'))


@app.route('/del_bask', methods=['GET', 'POST'])
def del_bask():
    if not session.get('logged_in'):
        return render_template('list_product.html.html', basket=[], products=[])
    db = get_db()

    history = []

    if request.form:

        historCard = db.execute('select id '
                                'from cards '
                                'where number = ? and userId = ?',
                                [request.form['number'], session['userId']])
        card = historCard.fetchone()

        if not card:
            db.execute('insert into cards(number, valid , svv, userId )'
                       ' VALUES (?, ?, ?, ? )',
                       [request.form['number'], request.form['valid'],
                        request.form['svv'], session['userId']])

        now = datetime.now()

        db.execute(
            'insert into history('
            'productId, quantity, price, date, userId, cardId, basketId) '
            'select '
            'b.productsId, '
            'b.quantity, '
            'p.price, '
            '?, '
            'u.id, '
            'c.id, '
            'b.id '
            'from products p , cards c, basket b, users u '
            'where p.id=b.productsId '
            'and u.id=b.userId  '
            'and c.userId=u.id '
            'and c.number=?'
            'and u.id=?',
            [now, request.form['number'], session['userId']])

        db.execute(
            'delete from basket '
            'where userId=?', [session['userId']])

        db.commit()

        cur = get_db().execute(
            'select p.name as name, '
            'p.model as model, '
            'h.quantity as quantity, '
            'p.price as price,'
            'u.name as customer, '
            'h.date as date '
            'from  products p, users u, history h '
            'where h.userId = ? '
            'and h.productId = p.id '
            'and u.id = h.userId', [session['userId']])

        history = cur.fetchall()

    return render_template('add_bank.html', history=history)


@app.route('/basket_user', methods=['GET'])
def basket_user():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    cur = db.execute('select p.name, p.model, p.price, b.quantity, (p.price * b.quantity) '
                     'as cost '
                     'from basket b, products p '
                     'where b.productsId = p.id and b.userId=?', [session['userId']])

    basket = cur.fetchall()
    cur = db.execute('select sum (p.price * b.quantity) '
                     'as sum from basket b, products p '
                     'where p.id=b.productsId '
                     'and b.userId=?', [session['userId']])
    sum = (cur.fetchone()[0])
    db.commit()

    return render_template('basket_user.html', basket=basket, sum=sum)



@app.route('/shopping_history', methods=['GET'])
def shopping_history():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()

    cur = db.execute('select '                                           
                     'h.date as date, '
                     'p.name as p_name, '
                     'p.model as p_model, '
                     'p.price as price, '
                     'h.quantity as quantity '
                     'from users u, history h, products p '
                     'where p.id = h.productId '
                     'and u.id = h.userId '
                     'and u.id = ? order by h.date desc ',
                     [session['userId']])

    shopping_h = cur.fetchall()

    history = {}

    for h in shopping_h:
        date = datetime.fromisoformat(h['date']).strftime("%Y-%m-%d %H:%M")
        if date in history:
            history[date].append(h)
        else:
            history[date] = []
            history[date].append(h)


    print(history)

    return render_template('shopping_history.html', shopping_h=history)


@app.route('/buy')
def buy():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    cur = db.execute(
        'select p.name, p.model, p.price, b.quantity, (p.price * b.quantity)'
        ' as cost '
        'from basket b, products p '
        'where b.productsId = p.id '
        'and b.userId=?', [session['userId']])

    basket = cur.fetchall()
    cur = db.execute(
        'select sum (p.price * b.quantity) as sum '
        'from products p, basket b '
        'where p.id=b.productsId and b.userId=?',
        [session['userId']])

    sum = (cur.fetchone()[0])

    db.execute(
        'insert into customers('
        'name, model, price, quantity, customer, date ) '
        'select p.name, p.model, p.price, b.quantity, '
        ' b.userId, datetime() '
        'from products p, basket b '
        'where p.id=b.productsId and b.userId=? ',
        [session['userId']])

    db.commit()
    return render_template('bay_products.html', basket=basket, sum=sum)


@app.route('/customers', methods=['GET'])
def customers():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()

    cur = db.execute(
        'select c.name as name, '
        'c.model as model, '
        'c.price as price, '
        'c.quantity as quantity, '
        'c.customer as customer, '
        'u.login_ as custom_login,'
        'u.name as custom_name, '
        'c.date as date '
        'from customers c, users u '
        'where c.customer = u.id')

    customers = cur.fetchall()

    return render_template('customers.html', customers=customers)


@app.route('/add_bank', methods=['GET'])
def add_bank():
    if not session.get('logged_in'):
        abort(401)

    return render_template('add_bank.html', add_bank=add_bank)


"""Это представление позволяет пользователю, если он осуществил вход, добавлять
новые записи. Оно реагирует только на запросы типа POST, а фактическая форма
отображается на странице list_product."""


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        login = request.form['login_']
        password = request.form['password']
        if login == '' or password == '':
            return render_template('add_user.html', error='Invalid registration, the field must be filled!')
        else:
            db = get_db()
            cur = db.execute(
                'select login_ '
                'from users '
                'where login_ = ?',
                [login])
            log = cur.fetchone()

            if log is not None:
                return render_template('add_user.html',
                error='Invalid registration, a user with this log already exists!')

            flash('You where registered')

            db = get_db()
            db.execute(
                'insert into users (login_, password, name, surname, tel, email, is_admin) '
                'values (?, ?, ?, ?, ?, ?, 0)',
                [login, password,
                 request.form['name'],
                 request.form['surname'],
                 request.form['tel'],
                 request.form['email']])
            db.commit()

    return render_template('add_user.html', error=None)


@app.route('/add_bank')
def to_buy():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    cur = db.execute(
        'select sum(p.price * b.quantity) as sum '
        'from products p, basket b '
        'where p.id=b.productsId and b.userId=?',
        [session['userId']])
    sum = cur.fetchall()

    return render_template('add_bank.html', sum=sum)


@app.route('/login', methods=['GET', 'POST'])
def login():
    print('login')
    error = None
    if request.method == 'POST':
        db = get_db()
        cur = db.execute(
            'select id, login_, password, is_admin '
            'from users '
            'where login_ = ? and password = ?',
            [request.form['username'],
             request.form['password']])
        user = cur.fetchone()

        if user is None:
            error = 'Invalid username or password!'
        else:
            session['logged_in'] = True
            session['is_admin'] = user['is_admin']
            session['userId'] = user['id']
            flash('You were logged in')

            return redirect(url_for('list_product'))

    return render_template('login.html', error=error)


"""Функция выхода, с другой стороны, удаляет обратно этот ключ из сессии. """


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('is_admin', None)
    flash('You where logged out')
    return redirect(url_for('list_product'))


"""Наконец, мы просто добавляем строчку в конце файла, которая запускает сервер, если 
мы хотим запустить этот файл как отдельное приложение:"""

if __name__ == '__main__':
    app.run()
