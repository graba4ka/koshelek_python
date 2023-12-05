import sqlite3

class DB:
    def __init__(self, database="database.db"):
        self.conn = sqlite3.connect(database)
        self.cur = self.conn.cursor()
        
    def close(self):
        self.conn.close()
        
    def commit(self):
        self.conn.commit()
        
    def add_user(self, username, password, full_name=None, phone=None):
        self.cur.execute("INSERT INTO users (username, password, full_name, phone) VALUES (?, ?, ?, ?)", (username, password, full_name, phone))     
        
    
    def get_user_password(self, username):
        self.cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        return self.cur.fetchone()

    def get_user_by_username(self, username):
        self.cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        return self.cur.fetchone() # (id, username, password, full_name, phone) | None
    
    def get_user_by_id(self, user_id):
        self.cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return self.cur.fetchone()
    
    def get_user_by_telegram(self, telegram_id):
        self.cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return self.cur.fetchone()
    
    def get_user_balance(self, user_id):
        # Получение общего баланса пользователя
        self.cur.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_id = ?", (user_id,)
        )
        total_amount = self.cur.fetchone()[0]
        return total_amount or 0.0


    def link_tg(self,user_id, telegram_id):
        self.cur.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (telegram_id, user_id))

    def unlink(self, telegram_id):
        self.cur.execute(
            "UPDATE users SET telegram_id = NULL where telegram_id = ?", (telegram_id,)
        )

    def create_tables(self):
        # Создание таблицы для хранения транзакций пользователей
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                transaction_type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )

    def add_transaction(self, user_id, amount, description, transaction_type):
        # Добавление транзакции в базу данных
        self.cur.execute(
            "INSERT INTO transactions (user_id, amount, description, transaction_type) VALUES (?, ?, ?, ?)",
            (user_id, amount, description, transaction_type),
        )

    def get_transactions_by_user(self, user_id):
        # Получение списка транзакций для конкретного пользователя
        self.cur.execute(
            "SELECT * FROM transactions WHERE user_id = ?", (user_id,)
        )
        return self.cur.fetchall()
