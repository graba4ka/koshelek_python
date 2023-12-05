import sqlite3
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from flask_login import LoginManager, current_user, login_required, login_user
from db import DB
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
app = Flask(__name__)
app.secret_key = "123"
login_manager = LoginManager(app)




class UserLogin:
    def fromDB(self, username):
        db = DB("database.db")
        self.user = db.get_user_by_username(username)
        db.close()
        return self

    def fromDBid(self, user_id):
        db = DB("database.db")
        self.user = db.get_user_by_id(user_id)
        db.close()
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user[0])


@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDBid(user_id)


@app.route("/")
def index():
    return render_template("index.html")


@app.route()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not (username and password):
            flash("Введіть логін та пароль!!!")
        else:
            db = DB("database.db")
            user = db.get_user_by_username(username)
            db.close()
            if user:
                user_password = user[2]
                if check_password_hash(pwhash=user_password, password=password):
                    login_user(UserLogin().fromDB(username))
                    print("залогилилось")
                    return redirect(url_for("wallet"))
            flash("Неправильний логін або пароль")
    return render_template("login.html")

@app.route("/transfer_money", methods=["POST"])
@login_required
def transfer_money():
    if request.method == "POST":
        username = request.form.get("username")
        transfer_amount = request.form.get("transfer_amount")

        if not (username and transfer_amount):
            flash("Введіть користувача та суму переказу")
        else:
            try:
                transfer_amount = float(transfer_amount)
            except ValueError:
                flash("Введіть коректну суму")
            else:
                db = DB("database.db")
                sender_balance = db.get_user_balance(current_user.user[0])
                receiver = db.get_user_by_username(username)

                if receiver is None:
                    flash("Користувача з таким ім'ям не знайдено")
                else:
                    receiver_id = receiver[0]

                    if sender_balance >= transfer_amount:
                        db.add_transaction(
                            user_id=current_user.user[0],
                            amount=-transfer_amount,
                            description=f"Переказ користувачу {username}",
                            transaction_type="expense",
                        )

                        db.add_transaction(
                            user_id=receiver_id,
                            amount=transfer_amount,
                            description=f"Отримано від користувача {current_user.user[1]}",
                            transaction_type="income",
                        )

                        db.commit()
                        db.close()
                        flash(f"Успішно переказано {transfer_amount} грн. користувачу {username}")
                    else:
                        db.close()
                        flash("Недостатньо коштів для переказу")

    return redirect(url_for("wallet"))




@app.route("/transfer_money_tg", methods=["POST"])
def transfer_money2():
    data = request.json  

    if "username" in data and "transfer_amount" in data and "telegram_id" in data:
        username = data["username"]
        transfer_amount = data["transfer_amount"]
        telegram_id = data["telegram_id"]

        try:
            transfer_amount = float(transfer_amount)
        except ValueError:
            return jsonify({"message": "Введіть коректну суму"})

        db = DB("database.db")
        sender = db.get_user_by_telegram(telegram_id)
        sender_id = sender[0]
        sender_balance = db.get_user_balance(sender_id)
        receiver = db.get_user_by_username(username)

        if receiver is None:
            return jsonify({"message": "Користувача з таким ім'ям не знайдено"})

        receiver_id = receiver[0]

        if sender_balance >= transfer_amount:
            db.add_transaction(
                user_id=sender_id,
                amount=-transfer_amount,
                description=f"Переказ користувачу {username}",
                transaction_type="expense",
            )

            db.add_transaction(
                user_id=receiver_id,
                amount=transfer_amount,
                description=f"Отримано від користувача {sender[1]}",
                transaction_type="income",
            )

            db.commit()
            db.close()
            return jsonify({"message": f"Успішно переказано {transfer_amount} грн. користувачу {username}"})
        else:
            db.close()
            return jsonify({"message": "Недостатньо коштів для переказу"})
    else:
        return jsonify({"message": "Не вдалося здійснити переказ. Перевірте дані."})






@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_rep = request.form.get("password-rep")
        print(username, password, password_rep)
        if not (username and password and (password == password_rep)):
            flash("Введіть логін та пароль правильно!!!")
        else:
            db = DB("database.db")
            pwhash = generate_password_hash(password)
            try:
                db.add_user(username=username, password=pwhash)
                db.commit()
                print("Добавилось")
            except sqlite3.IntegrityError:
                flash(f"Ім'я {username} вже зайнято, оберіть інше")
            else:
                return redirect(url_for("login"))
            finally:
                db.close()
    return render_template("register.html")





@app.route("/wallet", methods=["GET"])
@login_required
def wallet():
    db = DB("database.db")
    transactions = db.get_transactions_by_user(current_user.user[0])
    balance = db.get_user_balance(current_user.user[0])
    db.close()
    return render_template("wallet.html", transactions=transactions, balance=balance)

@app.route("/wallet_tg")
def wallet_tg():
    telegram_id = request.args.get("telegram_id")
    db = DB()
    user = db.get_user_by_telegram(telegram_id)
    user_id = user[0]
    balance = db.get_user_balance(
        user_id
    )  # [(1, 'fasdf', 'adfasd'), (2, 'asdfasdfasd', 'asdf')]
    db.close()
    return jsonify({"balance": balance})

@app.route("/add_money", methods=["POST"])
@login_required
def add_money():
    amount = request.form.get("amount")
    if not amount:
        flash("Введіть суму для додавання на рахунок")
    else:
        try:
            amount = float(amount)
        except ValueError:
            flash("Введіть коректну суму")
        else:
            db = DB("database.db")
            db.add_transaction(
                user_id=current_user.user[0],
                amount=amount,
                description="Поповнення кошелька",
                transaction_type="income",
            )   
            db.commit()
            db.close()
            flash(f"Успішно поповнено на {amount} грн.")
    return redirect(url_for("wallet"))

@app.route("/add_tg", methods=['POST'])
def add_tg():
    data = request.get_json()

    if "amount" not in data or "telegram_id" not in data:
        return jsonify({"error": "Недостаточно данных"})

    amount = data["amount"]
    telegram_id = data["telegram_id"]

    if not amount:
        return jsonify({"error": "Введіть суму для додавання на рахунок"})
    else:
        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"error": "Введіть коректну суму"})
        else:
            db = DB("database.db")

            user = db.get_user_by_telegram(telegram_id)
            if not user:
                return jsonify({"error": "Пользователь с таким Telegram ID не найден"})

            db.add_transaction(
                user_id=user[0],
                amount=amount,
                description="Поповнення кошелька",
                transaction_type="income",
            )
            db.commit()
            db.close()
            return jsonify({"message": f"Успішно поповнено на {amount} грн."})


@app.route("/spend_money", methods=["POST"])
@login_required
def spend_money():
    amount = request.form.get("amount")
    description = request.form.get("description")
    if not (amount and description):
        flash("Введіть суму та опис для витрати")
    else:
        try:
            amount = float(amount)
        except ValueError:
            flash("Введіть коректну суму")
        else:
            db = DB("database.db")
            balance = db.get_user_balance(current_user.user[0])
            if balance >= amount:  # Проверка на отрицательный баланс
                db.add_transaction(
                    user_id=current_user.user[0],
                    amount=-amount,
                    description=description,
                    transaction_type="expense",
                )
                db.commit()
                db.close()
                flash(f"Успішно витрачено {amount} грн. на {description}")
            else:
                db.close()
                flash("Недостатньо коштів на рахунку!")
    return redirect(url_for("wallet"))


@app.route("/spend_tg", methods=["POST"])
def spend_mone2y():
    data = request.get_json()  # Получаем данные из JSON тела запроса
    amount = data.get("amount")
    description = data.get("description")
    telegram_id = data.get("telegram_id")

    if not (amount and description and telegram_id):
        return jsonify({"error": "Не вказано достатньо даних"})
    
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"error": "Введіть коректну суму"})
    
    db = DB("database.db")
    user = db.get_user_by_telegram(telegram_id)
    if not user:
        return jsonify()
    user_id = user[0]
    balance = db.get_user_balance(user_id)


    if balance >= amount:
        db.add_transaction(
            user_id=user_id,
            amount=-amount,
            description=description,
            transaction_type="expense",
        )
        db.commit()
        db.close()
        return jsonify({"message": f"Успішно витрачено {amount} грн. на {description}"})
    else:
        db.close()
        return jsonify({"error": "Недостатньо коштів на рахунку!"})




@app.route("/tran")
def wallet_tg3():
    telegram_id = request.args.get("telegram_id")
    db = DB()
    user = db.get_user_by_telegram(telegram_id)
    user_id = user[0]
    tran = db.get_transactions_by_user(
        user_id
    )  # [(1, 'fasdf', 'adfasd'), (2, 'asdfasdfasd', 'asdf')]
    db.close()
    return jsonify({"tran": tran})


@app.route("/unlink")
def unlink():
    telegram_id = request.args.get("telegram_id")
    db = DB()
    db.unlink(telegram_id)
    db.commit()
    db.close()
    return jsonify({"status": "OK"})


@app.route("/check_tg")
def check_tg():
    telegram_id = request.args.get("telegram_id")
    db = DB()
    user = db.get_user_by_telegram(telegram_id)
    db.close()
    if user:
        return jsonify({"status": True})
    return jsonify({"status": False})


@app.route("/link_tg", methods=["POST"])
def link_tg():
    print(request.form)
    username = request.form.get("username", None)
    password = request.form.get("password", None)
    telegram_id = request.form.get("telegram_id", None)
    if username and password and telegram_id:
        db = DB()
        user = db.get_user_by_username(username)
        if user:
            pw_hash = user[2]
            if check_password_hash(pw_hash, password):
                db.link_tg(user[0], telegram_id)
                db.commit()
                db.close()
                return jsonify({"message": "Successfully linked"})
        db.close()
        return jsonify({"error": "Not valid username or password"})
    return jsonify({"error": "Not provided username or password or telegram_id"})




if __name__ == "__main__":
    db = DB("database.db")
    db.create_tables()
    app.run()
