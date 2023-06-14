from flask import Flask, render_template, request, flash, redirect, session, url_for, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import os
from hashlib import md5
import csv


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['UPLOAD_FOLDER'] = 'static/images/upload'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
db = SQLAlchemy(app)
ckeditor = CKEditor(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


class Client(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    secondname = db.Column(db.String(100))
    phone = db.Column(db.Integer,unique=True)
    order_id = db.relationship('Orders', backref='client', lazy='dynamic')
    
    def __repr__(self):
        return 'Client %r' % self.id 
    
class Worker(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    secondname = db.Column(db.String(100))
    phone = db.Column(db.Integer,unique=True)
    pasport = db.Column(db.Integer,unique=True)
    job = db.Column(db.String(100))
    password = db.Column(db.String(100))
    root = db.Column(db.Integer, default=0)
    order_id = db.relationship('Orders', backref='worker', lazy='dynamic')

    def __repr__(self):
        return 'Worker %r' % self.id 


class Tur(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100))
    price = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    order_id = db.relationship('Orders', backref='tur', lazy='dynamic')

    def __repr__(self):
        return 'Tur %r' % self.id 
    

class Orders(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    id_client = db.Column(db.Integer, db.ForeignKey('client.id'))
    id_tur = db.Column(db.Integer, db.ForeignKey('tur.id'))
    id_worker = db.Column(db.Integer, db.ForeignKey('worker.id'))
    date = db.Column(db.String(100))

    def __repr__(self):
        return 'Order %r' % self.id 
    

@app.route('/', methods=['GET', 'POST'])
def index():
    turs = Tur.query.all()
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            surname = request.form.get('surname')
            secondname = request.form.get('secondname')
            phone = request.form.get('phone')
            date = request.form.get('date')
            tur = request.form.get('tur')
            today = datetime.now()
            result = (today - datetime.strptime(date, '%Y-%m-%d')).total_seconds()

            if result>0:
                flash("Дата выбрана неправильно, так как этот день уже прошел!", category="bad")
                return redirect(url_for("index", _anchor='form'))
            
            seach_client = Client.query.filter_by(phone=phone).first()
            print(seach_client)
            if seach_client:
                order = Orders(id_client=seach_client.id,id_tur=tur,date=date)
                db.session.add(order)
                db.session.commit()
                flash("Клиент уже есть в системе, бронирование будет оформлено на его!", category="ok")
                return redirect(url_for("index") + '#form')
            client = Client(name=name, surname=surname,secondname=secondname,phone=phone)
           
            

            clients = Client.query.all()
            order = Orders(id_client=len(clients)+1,id_tur=tur,date=date)
            db.session.add(client)
            db.session.add(order)
            db.session.commit()
            flash("Успешно!", category="ok")
            return redirect(url_for("index", _anchor="form"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("index", _anchor="form"))
    return render_template("index.html",turs=turs)


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if 'name' in session:
        return redirect('/tur')
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        worker = Worker.query.filter_by(phone=phone,password=password).first()
        if worker:
            session['name'] = Worker.query.filter_by(phone=phone).first().phone
            return redirect(url_for("tur"))
        else:
            flash("Неправильный номер телефона или пароль!", category="bad")
            return redirect(url_for("auth"))
    return render_template("auth.html")


@app.route('/clients', methods=['GET', 'POST'])
def clients():
    if 'name' not in session:
        abort(401)
    clients = Client.query.all()
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            surname = request.form.get('surname')
            secondname = request.form.get('secondname')
            phone = request.form.get('phone')
            client = Client(name=name, surname=surname,secondname=secondname,phone=phone)
            db.session.add(client)
            db.session.commit()
            flash("Запись добавлена!", category="ok")
            return redirect(url_for("clients"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("clients"))
    return render_template("clients.html",clients=clients)


@app.route('/edit-client/<int:id>',methods=['GET','POST'])
def edit_client(id):
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            surname = request.form.get('surname')
            secondname = request.form.get('secondname')
            phone = request.form.get('phone')
            client = Client.query.filter_by(id=id).first()
            client.name = name
            client.surname = surname
            client.secondname = secondname
            client.phone = phone
            db.session.commit()
            flash("Запись обновлена!", category="ok")
            return redirect(url_for("clients"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("clients"))


@app.route('/delete_client/<int:id>')
def delete_client(id):
    client = Client.query.get(id)
    db.session.delete(client)
    db.session.commit()
    return redirect('/clients')

@app.route('/my-orders-to-csv', methods=['GET', 'POST'])
def my_orders_to_pdf():
    if 'name' not in session:
        abort(401)
    worker = Worker.query.filter_by(phone=session['name']).first()
    orders = Orders.query.filter_by(id_worker = worker.id).all()
    turs = Tur.query.all()
    clients = Client.query.all()
    
    clients_list = []
    worker_list = []
    tur_list = []
    for order in orders:
        q_client = Client.query.filter_by(id=order.id_client).first()
        clients_list.append(q_client)

        q_worker = Worker.query.filter_by(id=order.id_worker).first()
        worker_list.append(q_worker)

        q_tur = Tur.query.filter_by(id=order.id_tur).first()
        tur_list.append(q_tur)

    FILENAME = "static/orders.csv"
    with open(FILENAME, "w", newline="") as file:
        columns = ["Клиент", "Тур", "Дата", "Длительность"]
        writer = csv.DictWriter(file, fieldnames=columns, delimiter = ",")
        writer.writeheader()
        for order,client,tur,worker in zip(orders,clients_list,tur_list,worker_list):
            fullname = client.surname + " " + client.name
            writer.writerow({
                "Клиент": fullname, 
                "Тур": tur.title,
                "Дата": order.date,
                "Длительность": tur.duration
            })

    return redirect('/' + FILENAME)

@app.route('/my-orders', methods=['GET', 'POST'])
def my_orders():
    if 'name' not in session:
        abort(401)
    worker = Worker.query.filter_by(phone=session['name']).first()
    orders = Orders.query.filter_by(id_worker = worker.id).all()
    turs = Tur.query.all()
    clients = Client.query.all()
    
    clients_list = []
    worker_list = []
    tur_list = []
    for order in orders:
        q_client = Client.query.filter_by(id=order.id_client).first()
        clients_list.append(q_client)

        q_worker = Worker.query.filter_by(id=order.id_worker).first()
        worker_list.append(q_worker)

        q_tur = Tur.query.filter_by(id=order.id_tur).first()
        tur_list.append(q_tur)
    return render_template("my-orders.html",turs=turs,clients=clients,orders=orders,zip=zip,clients_list=clients_list,worker_list=worker_list, tur_list= tur_list)
    
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    if 'name' not in session:
        abort(401)
    orders = Orders.query.all()
    turs = Tur.query.all()
    clients = Client.query.all()
    worker = Worker.query.filter_by(phone=session['name']).first()

    clients_list = []
    worker_list = []
    tur_list = []
    for order in orders:
        q_client = Client.query.filter_by(id=order.id_client).first()
        clients_list.append(q_client)

        q_worker = Worker.query.filter_by(id=order.id_worker).first()
        worker_list.append(q_worker)

        q_tur = Tur.query.filter_by(id=order.id_tur).first()
        tur_list.append(q_tur)

    if request.method == 'POST':
        try:
            
            tur = request.form.get('tur')
            client = request.form.get('client')
            date = request.form.get('date')
            today = datetime.now()
            result = (today - datetime.strptime(date, '%Y-%m-%d')).total_seconds()
            if result>0:
                flash("Дата выбрана неправильно, так как этот день уже прошел!", category="bad")
                return redirect(url_for("orders"))
            order = Orders(id_client=client, id_tur=tur, id_worker=worker.id, date=date)
            db.session.add(order)
            db.session.commit()
            flash("Запись добавлена!", category="ok")
            return redirect(url_for("orders"))
        except:
            flash("Запись на это время невозможна!", category="bad")
            db.session.rollback()
            return redirect(url_for("orders"))
    return render_template("orders.html",turs=turs,clients=clients,orders=orders,zip=zip,clients_list=clients_list,worker_list=worker_list, tur_list= tur_list)

@app.route('/delete_order/<int:id>')
def delete_order(id):
    order = Orders.query.get(id)
    db.session.delete(order)
    db.session.commit()
    return redirect('/orders')


@app.route('/tur', methods=['GET', 'POST'])
def tur():
    if 'name' not in session:
        abort(401)
    turs = Tur.query.all()
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            duration = request.form.get('duration')
            price = request.form.get('price')
            tur = Tur(title=title, duration=duration, price=price)
            db.session.add(tur)
            db.session.commit()
            flash("Запись добавлена!", category="ok")
            return redirect(url_for("tur"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("tur"))
    return render_template("tur.html",turs=turs)


@app.route('/delete_tur/<int:id>')
def delete_tur(id):
    tur = Tur.query.get(id)
    db.session.delete(tur)
    db.session.commit()
    return redirect('/tur')

@app.route('/edit-tur/<int:id>',methods=['GET','POST'])
def edit_tur(id):
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            duration = request.form.get('duration')
            price = request.form.get('price')
            tur = Tur.query.filter_by(id=id).first()
            tur.title = title
            tur.duration = duration
            tur.price = price
            db.session.commit()
            flash("Запись обновлена!", category="ok")
            return redirect(url_for("tur"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("tur"))


@app.route('/workers', methods=['GET', 'POST'])
def workers():
    if 'name' not in session:
        abort(401)
    workers = Worker.query.all()
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            surname = request.form.get('surname')
            secondname = request.form.get('secondname')
            phone = request.form.get('phone')
            pasport = request.form.get('pasport')
            job = request.form.get('job')
            password = request.form.get('password')
            root = 0
            if job=="Администратор":
                root = 1
            worker = Worker(name=name, surname=surname,secondname=secondname,phone=phone,pasport=pasport,job=job,root=root,password=password)
            db.session.add(worker)
            db.session.commit()
            flash("Запись добавлена!", category="ok")
            return redirect(url_for("workers"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("workers"))
    return render_template("workers.html",workers=workers)


@app.route('/edit-worker/<int:id>',methods=['GET','POST'])
def edit_worker(id):
    print(id)
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            surname = request.form.get('surname')
            secondname = request.form.get('secondname')
            phone = request.form.get('phone')
            pasport = request.form.get('pasport')
            job = request.form.get('job')
            print(name,surname,secondname,phone,pasport,job)
            root = 0
            if job=="Администратор":
                root = 1
            worker = Worker.query.filter_by(id=id).first()
            worker.name = name
            worker.surname = surname
            worker.secondname = secondname
            worker.phone = phone
            worker.pasport = pasport
            worker.job = job
            worker.root = root
            db.session.commit()
            flash("Запись обновлена!", category="ok")
            return redirect(url_for("workers"))
        except:
            flash("Произошла ошибка!", category="bad")
            return redirect(url_for("workers"))

@app.route('/delete_worker/<int:id>')
def delete_worker(id):
    total_worker = Worker.query.filter_by(phone=session['name']).first()
    worker = Worker.query.get(id)
    if total_worker.id == worker.id:
        flash("Произошла ошибка!", category="bad")
        return redirect(url_for("workers"))
    db.session.delete(worker)
    db.session.commit()
    return redirect('/workers')


@app.context_processor
def inject_user():
    def get_user_name():
        if 'name' in session:
            return Worker.query.filter_by(phone=session['name']).first()
    return dict(active_user=get_user_name())


@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect('/')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidded(e):
    return render_template('403.html'), 403

@app.errorhandler(401)
def forbidded(e):
    return render_template('401.html'), 401

if __name__ == '__main__':
    app.run(debug=True)