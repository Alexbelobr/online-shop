import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for,\
    abort, render_template, flash

import datetime


# конфигурация
#DATABASE = 'data_.db'
#DEBUG = True
#SECRET_KEY = 'development key'
#USERNAME = 'admin'
#PASSWORD = 'default'

#алее, мы должны создать наше текущее приложение и инициализировать
# его в помощью конфигурации из того же файла, т. е. flaskr.py:
# создаём наше маленькое приложение :)

app = Flask(__name__)
#wsgi_app = app.wsgi_app
app.config.from_object(__name__)

# Загружаем конфиг по умолчанию и переопределяем в конфигурации часть
# значений через переменную окружения
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'data_.db'),
    DEBUG=True,
    SECRET_KEY='development key'
    #USERNAME='admin',
    #PASSWORD='admin'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
#Объект Config работает подобно словарю, поэтому мы можем обновлять его с помощью новых значений.

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

    #with app.app_context():
        #db = get_db()
    with app.open_resource('shema.sql', mode='r') as f:

        db.cursor().executescript(f.read())
        db.commit()
    print('Initialized the database.')

    """ Метод open_resource() объекта приложения является удобной функцией-помощником, 
которая откроет ресурс, обеспечиваемый приложением. Эта функция открывает файл из 
места расположения ресурсов (в нашем случае папка flaskr_n), и позволяет вам из него читать """
# Всё, что вам надо знать на этот момент - это то,
# что вы можете безопасно сохранять информацию в объекте g.

def get_db():
    """Если ещё нет соединения с базой данных, открыть новое - для
    текущего контекста приложения"""
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

"""Функция представления передаёт записи в виде словаря шаблону show_entries.html
и возвращает сформированное отображение:"""
@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute(
        'select * from products '
        'order by id desc')
    products = cur.fetchall()

    if not session.get('logged_in'):
        return render_template('show_entries.html', products=products, basket=[])
    cur = db.execute(
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
        [session['userId']])
    basket = cur.fetchall()

    for row in basket:
        for x in range(len(row)):
          print(row[x])

    return render_template('show_entries.html', products=products, basket=basket)




"""Это представление позволяет пользователю, если он осуществил вход, добавлять
новые записи. Оно реагирует только на запросы типа POST, а фактическая форма
отображается на странице show_entries."""
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute(
        'insert into products(name, model, price, quantity)'
        ' values (?, ?, ?, ?)',
        [request.form['name'], request.form['model'],
         request.form['price'], request.form['quantity']])

    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))



@app.route('/delete-product', methods=['POST'])
def delete_product():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute(
        'delete from products '
        'where id=?', [request.form['id']])
    db.commit()
    return redirect(url_for('show_entries'))


@app.route('/add_basket', methods=['POST'])
def add_basket():
    print("add_basket")

    if not session.get('logged_in'):
        return render_template('show_entries.html', products=[], basket=[])
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
        return redirect(url_for('show_entries'))


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
    return redirect(url_for('show_entries'))


@app.route('/delete_basket', methods=['POST'])
def delete_basket():
    print("delete_basket")
    if not session.get('logged_in'):
        return render_template('show_entries.html', basket=[], products=[])
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
    return redirect(url_for('show_entries'))

@app.route('/buy')
def bay():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    cur = db.execute(
        'select p.name, p.model, p.price, b.quantity, (p.price * b.quantity) as cost '
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
        #'sum (p.price * b.quantity) as sum,'
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
       # 'c.sum as sum, '
        'c.customer as customer, '
        'u.login_ as custom_login,'
        'u.name as custom_name, '
        'c.date as date '
        'from customers c, users u '
        'where c.customer = u.id')

    customers = cur.fetchall()



    return render_template('customers.html', customers=customers)


"""Это представление позволяет пользователю, если он осуществил вход, добавлять
новые записи. Оно реагирует только на запросы типа POST, а фактическая форма
отображается на странице show_entries."""
""""@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)
"""
@app.route('/add_users', methods=['GET', 'POST'])
def add_users():
    if request.method == 'POST':
        login = request.form['login_']
        password = request.form['password']
        if login == '' or password == '':
            return render_template('add_users.html', error='Invalid registration, the field must be filled!')
        else:
            db = get_db()
            cur = db.execute(
                'select login_ '
                'from users '
                'where login_ = ?',
                [login])
            log = cur.fetchone()

            if log is not None:
                return render_template('add_users.html', error='Invalid registration, a user with this log already exists!')

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

    return render_template('add_users.html', error=None)

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

        if user == None:
            error = 'Invalid username or password!'
        else:
            session['logged_in'] = True
            session['is_admin'] = user['is_admin']
            session['userId'] = user['id']
            flash('You were logged in')

            return redirect(url_for('show_entries'))

    return render_template('login.html', error=error)

"""Функция выхода, с другой стороны, удаляет обратно этот ключ из сессии. """

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('is_admin', None)
    flash('You where logged out')
    return redirect(url_for('show_entries'))




"""Наконец, мы просто добавляем строчку в конце файла, которая запускает сервер, если 
мы хотим запустить этот файл как отдельное приложение:"""



if __name__ == '__main__':

    app.run()

