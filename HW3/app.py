from types import MethodDescriptorType
from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import and_
from datetime import datetime

app=Flask(__name__)
app.secret_key = "hahaha"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://<username>:<passwd>@127.0.0.1:3306/<DBname>"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

works=db.Table('works', 
	db.Column('uid', db.Integer, db.ForeignKey('user.uid')),
	db.Column('sid', db.Integer, db.ForeignKey('shop.sid'))
)

decisions=db.Table('decisions',
	db.Column('uid', db.Integer, db.ForeignKey('user.uid')),
	db.Column('oid', db.Integer, db.ForeignKey('order.oid'))
)

class User(UserMixin, db.Model):
	__tablename__ = 'user'
	uid = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=True, nullable=False)
	password = db.Column(db.String(128), nullable=False)
	email = db.Column(db.String(80), nullable=False)
	phone = db.Column(db.String(10), nullable=False)
	own_shop = db.relationship('Shop', backref='user', uselist=False)
	work_at = db.relationship('Shop', secondary=works, backref='work_place', lazy='dynamic')
	orders = db.relationship('Order', backref='buyer')
	make_decision = db.relationship('Order', secondary=decisions, backref='finisher', lazy='dynamic')

	def __init__(self, name, password, email, phone):
		self.name = name
		self.email = email
		self.phone = phone
		self.password = password

	def check_password(self, password):
		return check_password_hash(self.password, password)
	
	def get_id(self): #for /remove function to replace get_id function in UserMixin
		return (self.uid)



class Shop(db.Model):
	__tablename__ = 'shop'
	sid = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=True, nullable=False)
	city = db.Column(db.String(80), nullable=False)
	phone = db.Column(db.String(10), nullable=False)
	price = db.Column(db.Integer, nullable=False)
	amount = db.Column(db.Integer, nullable=False)
	owner = db.Column(db.Integer, db.ForeignKey('user.uid'), unique=True)
	orders = db.relation('Order', backref='order_oid')

	def __init__(self, name, city, phone, price, amount, owner):
		self.name=name
		self.city=city
		self.phone=phone
		self.price=price
		self.amount=amount
		self.owner=owner


class Order(db.Model):
	__tablename__ = 'order'
	oid = db.Column(db.Integer, primary_key=True)
	status = db.Column(db.String(15), nullable=False)
	startt = db.Column(db.DateTime, nullable=False)
	endt = db.Column(db.DateTime)
	customer = db.Column(db.Integer, db.ForeignKey('user.uid'), nullable=False)
	cname = db.Column(db.String(80), nullable=False)
	shopid = db.Column(db.Integer, db.ForeignKey('shop.sid'))
	shopname = db.Column(db.String(80), nullable=False)
	ender = db.Column(db.String(80))
	amount = db.Column(db.Integer, nullable=False)
	price = db.Column(db.Integer, nullable=False)

	def __init__(self, status, startt, customer, cname, shopid, shopname, amount, price):
		self.status = status
		self.startt = startt
		self.customer = customer
		self.cname = cname
		self.shopid = shopid
		self.shopname = shopname
		self.amount = amount
		self.price = price



@app.route("/")
def index():
	return redirect(url_for("login"))

@app.route("/login", methods=["POST", "GET"])
def login():
	if request.method == "GET":
		return render_template("index.html")
	name = request.form["Uname"]
	paw = request.form["Pass"]
	flag = User.query.filter_by(name=name).first() #test whether name exists
	if not flag:
		return render_template("index.html", key = 1)
	elif not flag.check_password(paw):
		return render_template("index.html", key = 1)

	session["user"] = name
	return redirect(url_for("home"))

@app.route("/register")
def register():
	return render_template("register.html")

@app.route("/add_user", methods=["POST"])
def add_user():
	name = request.form["Uname"]
	paw = request.form["Pass"]
	con = request.form["Con"]
	phone = request.form["Phone"]
	email = request.form["Email"]
	new_user  = User(name=name, password=generate_password_hash(paw, method='sha256'), phone=phone, email=email)
	db.session.add(new_user)
	db.session.commit()
	return render_template("index.html", key = 2)
		

@app.route("/home")
def home():
	if "user" in session:
		user = session["user"]
		datas=User.query.filter_by(name=user).first()
		print(datas.name)
		shops = Shop.query.all()
		return render_template("home.html", datas=datas, list=shops)
	else:
		return redirect(url_for("login"))

@app.route("/create_order/<id>", methods=["POST"])
def create_order(id):
	if "user" in session:
		usr_name=session["user"]
		buy=request.form["Buy"]
		print(id)
		if not buy:
			return redirect(url_for("home"))
		usr=User.query.filter_by(name=usr_name).first()
		shop=Shop.query.filter_by(sid=id).first()
		amount = shop.amount
		if not buy.isdigit() or int(buy) <= 0:
			shops = Shop.query.all()
			return render_template("home.html", key = 1, datas = usr, list = shops)
		elif int(buy) > amount:
			shops = Shop.query.all()
			return render_template("home.html", key = 2, datas = usr, list = shops)
		else:
			nowtime = datetime.now()
			new_order = Order(status = "not finished", startt = nowtime, customer = usr.uid, cname = usr.name, shopid = shop.sid, shopname = shop.name, amount = buy, price = shop.price)
			shop.amount = amount - int(buy)
			db.session.add(new_order)
			db.session.commit()
			shops = Shop.query.all()
			return render_template("home.html", key = 3, datas = usr, list = shops)
	else:
		return redirect(url_for("login"))

@app.route("/shop")
def shop():
	if "user" in session:
		user = session["user"]
		print(user)
		datas=User.query.filter_by(name=user).first()
		if datas.own_shop:
			for i in datas.work_at:
				print(i.name)
			shop=Shop.query.filter_by(name=datas.own_shop.name).first()
			return render_template("shop_owner.html", datas=shop)
		else:
			return render_template("shop_create.html")
	else:
		return redirect(url_for("login"))

@app.route("/add_employees", methods=["POST"])
def add_employees():
	if "user" in session:
		name = request.form["Uname"]
		employee = User.query.filter_by(name=name).first() #test whether user exist
		if employee:
			owner_name=session["user"]
			owner=User.query.filter_by(name=owner_name).first()
			shop=Shop.query.filter_by(name=owner.own_shop.name).first()
			j = shop.work_place
			for i in j:
				if name == i.name:
					flash("This employee has already existed!!!")
					return redirect(url_for("shop"))
			shop.work_place.append(employee)
			db.session.commit()
			return redirect(url_for("shop"))
		else:
			flash("This user does not exist")
			return redirect(url_for("shop"))
	else:
		return redirect(url_for("login"))


@app.route("/remove/<id>")
def remove(id):
	if "user" in session:
		owner_name=session["user"]
		owner=User.query.filter_by(name=owner_name).first()
		shop=Shop.query.filter_by(name=owner.own_shop.name).first()
		print(id)
		if owner.uid == int(id):
			print(1)
			return redirect(url_for("shop"))
		dissmiss = User.query.filter_by(uid=id).first()
		print(dissmiss)
		shop.work_place.remove(dissmiss)
		db.session.commit()
		return redirect(url_for("shop"))
	else:
		return redirect(url_for("login"))
	

@app.route("/logout")
def logout():			
	session.pop("user", None)
	return render_template("index.html")


@app.route("/add_shop", methods=["POST"])
def add_shop():
	if "user" in session:
		print(session["user"])
		usr_name=session["user"]
		shop=request.form["Name"]
		city=request.form["City"]
		phone=request.form["Phone"]
		price=request.form["Price"]
		amount=request.form["Amount"]
		usr=User.query.filter_by(name=usr_name).first()
		owner=usr.uid
		new_shop=Shop(name=shop, city=city, phone=phone, price=price, amount=amount, owner=owner)
		db.session.add(new_shop)
		db.session.commit()
		print("success")
		datas=User.query.filter_by(name=usr_name).first()
		shop=Shop.query.filter_by(name=datas.own_shop.name).first()
		shop.work_place.append(datas)
		db.session.commit()
		return render_template("shop_owner.html", key = 1, datas=shop)
	else:
		return redirect(url_for("login"))
		

@app.route("/update_price", methods=["POST"])
def update_price():
	if "user" in session:
		usr_name=session["user"]
		newprice=request.form["NewPrice"]
		newamount=request.form["NewAmount"]
		datas=User.query.filter_by(name=usr_name).first()
		shop=Shop.query.filter_by(name=datas.own_shop.name).first()
		if not newprice and not newamount:
			price = shop.price
			amount = shop.amount
		elif not newamount:
			amount = shop.amount
			price = int(newprice)
		elif not newprice:
			price = shop.price
			amount = int(newamount)
		else:
			price = int(newprice)
			amount = int(newamount)

		shop.price = price
		shop.amount = amount
		db.session.commit()
		return render_template("shop_owner.html", datas=shop)
	else:
		return redirect(url_for("login"))

@app.route("/search", methods=["POST"])
def search():
	if "user" in session:
		users = session["user"]
		datas = User.query.filter_by(name=users).first()
		shopt = datas.work_at
		sname = request.form["Sname"]
		sear = "%{}%".format(sname)
		city = request.form["City"]
		minprice = request.form["MinPrice"]
		maxprice = request.form["MaxPrice"]
		amount = request.form["Amount"]
		chk = request.form.get("Chk", False)
		if minprice and maxprice:
			if not minprice.isdigit() or not maxprice.isdigit() or int(minprice) < 0 or int(maxprice) < 0 or int(maxprice) < int(minprice):
				flash("input of price is invalid")
				shops = Shop.query.all()
				return render_template("home.html", datas = datas, list = shops)
			else:
				if amount == "0":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.price >= int(minprice), Shop.price <= int(maxprice))).filter(Shop.amount == 0).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.price >= int(minprice), Shop.price <= int(maxprice))).filter(Shop.amount == 0).all()
						return render_template("home.html", datas = datas, list = shops)
				elif amount == "1":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.price >= int(minprice), Shop.price <= int(maxprice))).filter(and_(Shop.amount >= 1, Shop.amount <= 99)).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.price >= int(minprice), Shop.price <= int(maxprice))).filter(and_(Shop.amount >= 1, Shop.amount <= 99)).all()
						return render_template("home.html", datas = datas, list = shops)
				elif amount == "2":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.price >= int(minprice), Shop.price <= int(maxprice))).filter(Shop.amount >= 100).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.price >= int(minprice), Shop.price <= int(maxprice))).filter(Shop.amount >= 100).all()
						return render_template("home.html", datas = datas, list = shops)
				else:
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.price >= int(minprice), Shop.price <= int(maxprice))).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.price >= int(minprice), Shop.price <= int(maxprice))).all()
						return render_template("home.html", datas = datas, list = shops)
		elif minprice:
			if not minprice.isdigit() or int(minprice) < 0:
				flash("input of price is invalid")
				shops = Shop.query.all()
				return render_template("home.html", datas = datas, list = shops)
			else:
				if amount == "0":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price >= int(minprice)).filter(Shop.amount == 0).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price >= int(minprice)).filter(Shop.amount == 0).all()
						return render_template("home.html", datas = datas, list = shops)
				elif amount == "1":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price >= int(minprice)).filter(and_(Shop.amount >= 1, Shop.amount <= 99)).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price >= int(minprice)).filter(and_(Shop.amount >= 1, Shop.amount <= 99)).all()
						return render_template("home.html", datas = datas, list = shops)
				elif amount == "2":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price >= int(minprice)).filter(Shop.amount >= 100).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price >= int(minprice)).filter(Shop.amount >= 100).all()
						return render_template("home.html", datas = datas, list = shops)
				else:
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price >= int(minprice)).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price >= int(minprice)).all()
						return render_template("home.html", datas = datas, list = shops)
		elif maxprice:
			if not maxprice.isdigit() or int(maxprice) < 0:
				flash("input of price is invalid")
				shops = Shop.query.all()
				return render_template("home.html", datas = datas, list = shops)
			else:
				if amount == "0":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price <= int(maxprice)).filter(Shop.amount == 0).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price <= int(maxprice)).filter(Shop.amount == 0).all()
						return render_template("home.html", datas = datas, list = shops)
				elif amount == "1":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price <= int(maxprice)).filter(and_(Shop.amount >= 1, Shop.amount <= 99)).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price <= int(maxprice)).filter(and_(Shop.amount >= 1, Shop.amount <= 99)).all()
						return render_template("home.html", datas = datas, list = shops)
				elif amount == "2":
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price <= int(maxprice)).filter(Shop.amount >= 100).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price <= int(maxprice)).filter(Shop.amount >= 100).all()
						return render_template("home.html", datas = datas, list = shops)
				else:
					if not chk:
						shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price <= int(maxprice)).all()
						return render_template("home.html", datas = datas, list = shops)
					else:						
						tmp = datas.work_at
						shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.price <= int(maxprice)).all()
						return render_template("home.html", datas = datas, list = shops)
		else:
			if amount == "0":
				if not chk:
					shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.amount == 0).all()
					return render_template("home.html", datas = datas, list = shops)
				else:						
					tmp = datas.work_at
					shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.amount == 0).all()
					return render_template("home.html", datas = datas, list = shops)
			elif amount == "1":
				if not chk:
					shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.amount >= 1, Shop.amount <= 99)).all()
					return render_template("home.html", datas = datas, list = shops)
				else:						
					tmp = datas.work_at
					shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(and_(Shop.amount >= 1, Shop.amount <= 99)).all()
					return render_template("home.html", datas = datas, list = shops)
			elif amount == "2":
				if not chk:
					shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.amount >= 100).all()
					return render_template("home.html", datas = datas, list = shops)
				else:						
					tmp = datas.work_at
					shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).filter(Shop.amount >= 100).all()
					return render_template("home.html", datas = datas, list = shops)
			else:
				if not chk:
					shops = Shop.query.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).all()
					return render_template("home.html", datas = datas, list = shops)
				else:						
					tmp = datas.work_at
					shops = tmp.filter(Shop.name.contains(sname)).filter(Shop.city.contains(city)).all()
					return render_template("home.html", datas = datas, list = shops)
	else:
		return redirect(url_for("login"))

@app.route("/chk_username", methods=["POST"])
def chk():
	name = request.form["Uname"]
	if User.query.filter_by(name=name).first():
		return jsonify(False)
	else:
		return jsonify(True)

@app.route("/chk_shopname", methods=["POST"])
def chk_shopname():
	name = request.form["Name"]
	if Shop.query.filter_by(name=name).first():
		return jsonify(False)
	else:
		return jsonify(True)

@app.route("/search_myorder", methods=["POST"])
def search_myorder():
	status = request.form["Status"]
	if not status:
		return redirect(url_for("myorder"))
	user = session["user"]
	usr = User.query.filter_by(name=user).first()
	orders = Order.query.filter_by(customer=usr.uid).filter_by(status=status).all()
	return render_template("myorder.html", orders=orders)

@app.route("/myorder")
def myorder():
	if "user" in session:
		users = session["user"]
		usr = User.query.filter_by(name=users).first()
		orders = Order.query.filter_by(customer=usr.uid).all()
		return render_template("myorder.html", orders=orders)
	else:
		return redirect(url_for("login"))

@app.route("/cancel/<id>")
def cancel(id):
	name = session["user"]
	usr = User.query.filter_by(name=name).first()
	order = Order.query.filter_by(oid=id).first()
	if(order.status != "not finished"):
		orders = Order.query.filter_by(customer=usr.uid).all()
		return render_template("myorder.html", orders=orders, key=1)
	else:
		order.status = "cancelled"
		time = datetime.now()
		order.endt = time
		order.finisher.append(usr)
		order.ender = usr.name
		shop = Shop.query.filter_by(sid=order.shopid).first()
		shop.amount = (shop.amount + order.amount)
		db.session.commit()
		orders = Order.query.filter_by(customer=usr.uid).all()
		return render_template("myorder.html", orders=orders)

@app.route("/shoporder")
def shoporder():
	if "user" in session:
		users = session["user"]
		usr = User.query.filter_by(name=users).first()
		shops = usr.work_at
		worklist = []
		for i in shops:
			worklist.append(i.sid)
		orderlist = Order.query.filter(Order.shopid.in_(worklist)).all()
		return render_template("shoporder.html", lists=shops, orders=orderlist)
	else:
		return redirect(url_for("login"))


@app.route("/scancel/<id>")
def scancel(id):
	name = session["user"]
	usr = User.query.filter_by(name=name).first()
	order = Order.query.filter_by(oid=id).first()
	if(order.status != "not finished"):
		shops = usr.work_at
		worklist = []
		for i in shops:
			worklist.append(i.sid)
		orders = Order.query.filter(Order.shopid.in_(worklist)).all()
		return render_template("shoporder.html", lists=shops, orders=orders, key=1)
	else:
		order.status = "cancelled"
		time = datetime.now()
		order.endt = time
		order.finisher.append(usr)
		order.ender = usr.name
		shop = Shop.query.filter_by(sid=order.shopid).first()
		shop.amount = (shop.amount + order.amount)
		db.session.commit()
		return redirect(url_for("shoporder"))

@app.route("/finish/<id>")
def finish(id):
	name = session["user"]
	usr = User.query.filter_by(name=name).first()
	order = Order.query.filter_by(oid=id).first()
	if(order.status != "not finished"):
		shops = usr.work_at
		worklist = []
		for i in shops:
			worklist.append(i.sid)
		orders = Order.query.filter(Order.shopid.in_(worklist)).all()
		return render_template("shoporder.html", lists=shops, orders=orders, key=1)
	else:
		order.status = "finished"
		time = datetime.now()
		order.endt = time
		order.finisher.append(usr)
		order.ender = usr.name
		db.session.commit()
		return redirect(url_for("shoporder"))

@app.route("/search_shoporder", methods=["POST"])
def search_shoporder():
	status = request.form["Status"]
	ch = request.form["Choose"]
	name = session["user"]
	usr = User.query.filter_by(name=name).first()
	shops = usr.work_at
	if not status and not ch:
		return redirect(url_for("shoporder"))
	elif not status and ch:
		orders = Order.query.filter_by(shopid=int(ch)).all()
		return render_template("shoporder.html", lists=shops, orders=orders)
	elif status and not ch:
		worklists = []
		for i in shops:
			worklists.append(i.sid)
		orders = Order.query.filter(Order.shopid.in_(worklists)).filter_by(status=status).all()
		return render_template("shoporder.html", lists=shops, orders=orders)
	else:
		orders = Order.query.filter_by(shopid=int(ch)).filter_by(status=status).all()
		return render_template("shoporder.html", lists=shops, orders=orders)


if __name__ == "__main__":
	db.create_all()
	app.run(host='0.0.0.0', port=3000, debug = True)
