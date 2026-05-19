import sqlite3
import bcrypt
import os
from datetime import datetime
import pytz

turkey_tz = pytz.timezone('Europe/Istanbul')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'finansiq.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            age INTEGER,
            city TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            monthly_income REAL,
            monthly_expenses REAL,
            total_savings REAL,
            financial_goal TEXT,
            goal_amount REAL,
            goal_years INTEGER,
            risk_profile TEXT,
            literacy_score INTEGER,
            communication_level TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT,
            amount REAL,
            description TEXT,
            date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            alarm_type TEXT,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_key TEXT UNIQUE NOT NULL,
            data_value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# --- KULLANICI İŞLEMLERİ ---

def register_user(name, surname, email, password, age, city):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT INTO users (name, surname, email, password_hash, age, city)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, surname, email, password_hash, age, city))
        conn.commit()
        return {"success": True, "user_id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Bu e-posta adresi zaten kayıtlı."}
    finally:
        conn.close()

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return {"success": True, "user": dict(user)}
    return {"success": False, "error": "E-posta veya şifre hatalı."}

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

# --- PROFİL İŞLEMLERİ ---

def save_profile(user_id, data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM profiles WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute('''
            UPDATE profiles SET
                monthly_income=?, monthly_expenses=?, total_savings=?,
                financial_goal=?, goal_amount=?, goal_years=?,
                risk_profile=?, literacy_score=?, communication_level=?,
                updated_at=?
            WHERE user_id=?
        ''', (
            data.get('monthly_income'), data.get('monthly_expenses'),
            data.get('total_savings'), data.get('financial_goal'),
            data.get('goal_amount'), data.get('goal_years'),
            data.get('risk_profile'), data.get('literacy_score'),
            data.get('communication_level'), datetime.now(turkey_tz).isoformat(),
            user_id
        ))
    else:
        cursor.execute('''
            INSERT INTO profiles (user_id, monthly_income, monthly_expenses,
                total_savings, financial_goal, goal_amount, goal_years,
                risk_profile, literacy_score, communication_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, data.get('monthly_income'), data.get('monthly_expenses'),
            data.get('total_savings'), data.get('financial_goal'),
            data.get('goal_amount'), data.get('goal_years'),
            data.get('risk_profile'), data.get('literacy_score'),
            data.get('communication_level')
        ))
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,))
    profile = cursor.fetchone()
    conn.close()
    return dict(profile) if profile else None

# --- HARCAMA İŞLEMLERİ ---

def save_expenses(user_id, expenses_list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
    for exp in expenses_list:
        cursor.execute('''
            INSERT INTO expenses (user_id, category, amount, description, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, exp.get('category'), exp.get('amount'),
              exp.get('description', ''), exp.get('date', '')))
    conn.commit()
    conn.close()

def get_expenses(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,))
    expenses = cursor.fetchall()
    conn.close()
    return [dict(e) for e in expenses]

# --- ALARM İŞLEMLERİ ---

def save_alarm(user_id, alarm_type, message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO alarms (user_id, alarm_type, message)
        VALUES (?, ?, ?)
    ''', (user_id, alarm_type, message))
    conn.commit()
    conn.close()

def get_alarms(user_id, unread_only=False):
    conn = get_connection()
    cursor = conn.cursor()
    if unread_only:
        cursor.execute('SELECT * FROM alarms WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC', (user_id,))
    else:
        cursor.execute('SELECT * FROM alarms WHERE user_id = ? ORDER BY created_at DESC LIMIT 20', (user_id,))
    alarms = cursor.fetchall()
    conn.close()
    return [dict(a) for a in alarms]

def mark_alarms_read(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE alarms SET is_read = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# --- MARKET CACHE İŞLEMLERİ ---

def save_market_cache(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO market_cache (data_key, data_value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(data_key) DO UPDATE SET
            data_value = excluded.data_value,
            updated_at = excluded.updated_at
    ''', (key, value, datetime.now(turkey_tz).isoformat()))
    conn.commit()
    conn.close()

def get_market_cache(key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM market_cache WHERE data_key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None