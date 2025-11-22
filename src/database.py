import sqlite3
import datetime
import os

class Database:
    def __init__(self, db_path="deals.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Table to track sent deals
            # Dropping table to apply schema changes (Dev only)
            # cursor.execute('DROP TABLE IF EXISTS sent_deals') 
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_deals (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    source TEXT,
                    price REAL,
                    original_price REAL,
                    discount INTEGER,
                    rating REAL,
                    seller TEXT,
                    link TEXT,
                    image TEXT,
                    sent_at DATE
                )
            ''')
            
            # Check if new columns exist, if not, we might need to migrate or drop
            # For simplicity in this session, we'll catch the error on insert or user can delete db
            try:
                cursor.execute('SELECT source FROM sent_deals LIMIT 1')
            except sqlite3.OperationalError:
                print("Migrating DB: Dropping old table to update schema...")
                cursor.execute('DROP TABLE sent_deals')
                cursor.execute('''
                    CREATE TABLE sent_deals (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        source TEXT,
                        price REAL,
                        original_price REAL,
                        discount INTEGER,
                        rating REAL,
                        seller TEXT,
                        link TEXT,
                        image TEXT,
                        sent_at DATE
                    )
                ''')
            
            conn.commit()

    def is_deal_sent_today(self, deal_id: str) -> bool:
        today = datetime.date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT sent_at FROM sent_deals WHERE id = ?', (deal_id,))
            row = cursor.fetchone()
            
            if row:
                sent_date = row[0]
                if sent_date == today:
                    return True
                else:
                    return False 
            return False

    def mark_deal_as_sent(self, deal: dict):
        today = datetime.date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Upsert
            cursor.execute('''
                INSERT INTO sent_deals (id, title, source, price, original_price, discount, rating, seller, link, image, sent_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET sent_at = ?
            ''', (
                deal['id'], deal['title'], deal.get('source', ''), deal['price'], deal.get('original_price', 0),
                deal['discount'], deal.get('rating', 0), deal.get('seller', ''), deal['link'], deal.get('image', ''),
                today, today
            ))
            conn.commit()

    def get_today_deals_count(self) -> int:
        today = datetime.date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM sent_deals WHERE sent_at = ?', (today,))
            return cursor.fetchone()[0]

    def get_recent_deals(self, limit=50):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sent_deals ORDER BY sent_at DESC, rowid DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
