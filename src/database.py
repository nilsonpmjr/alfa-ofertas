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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_deals (
                    id TEXT PRIMARY KEY,
                    title TEXT,
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
                    # If sent on a previous day, we can technically resend it today if it's still a deal?
                    # User said "never deliver the same offer more than one time per day".
                    # This implies if it was sent yesterday, it CAN be sent today.
                    # But to be safe and avoid spam, let's update the date if we resend.
                    return False 
            return False

    def mark_deal_as_sent(self, deal_id: str, title: str):
        today = datetime.date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Upsert: if exists, update date; if not, insert
            cursor.execute('''
                INSERT INTO sent_deals (id, title, sent_at) 
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET sent_at = ?
            ''', (deal_id, title, today, today))
            conn.commit()

    def get_today_deals_count(self) -> int:
        today = datetime.date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM sent_deals WHERE sent_at = ?', (today,))
            return cursor.fetchone()[0]
