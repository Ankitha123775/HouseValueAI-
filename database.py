import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "homevalue.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            total_sqft REAL NOT NULL,
            bhk INTEGER NOT NULL,
            bath INTEGER NOT NULL,
            age INTEGER NOT NULL,
            predicted_price_lakhs REAL NOT NULL,
            predicted_price_inr REAL NOT NULL,
            price_per_sqft REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_name TEXT NOT NULL,
            location TEXT NOT NULL,
            total_sqft REAL NOT NULL,
            bhk INTEGER NOT NULL,
            bath INTEGER NOT NULL,
            age INTEGER NOT NULL,
            predicted_price_lakhs REAL NOT NULL,
            price_per_sqft REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def add_prediction(location, total_sqft, bhk, bath, age, price_lakhs, price_inr, pps):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (location, total_sqft, bhk, bath, age, predicted_price_lakhs, predicted_price_inr, price_per_sqft)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (location, total_sqft, bhk, bath, age, price_lakhs, price_inr, pps))
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id

def get_recent_predictions(limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_prediction_by_id(pred_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def clear_prediction_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions")
    conn.commit()
    conn.close()

def add_favorite(name, location, total_sqft, bhk, bath, age, price_lakhs, pps):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO favorites (property_name, location, total_sqft, bhk, bath, age, predicted_price_lakhs, price_per_sqft)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, location, total_sqft, bhk, bath, age, price_lakhs, pps))
    fav_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return fav_id

def get_favorites():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favorites ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_favorite(fav_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE id = ?", (fav_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")