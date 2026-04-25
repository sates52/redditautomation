import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                subreddit_type TEXT NOT NULL,
                source_content TEXT,
                source_file TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_for TIMESTAMP,
                posted_at TIMESTAMP,
                reddit_post_id TEXT,
                reddit_post_url TEXT,
                post_name TEXT,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS word_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_preview TEXT,
                chunk_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                action TEXT NOT NULL,
                action_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_post(self, title: str, body: str, subreddit_type: str,
                 source_content: str = None, source_file: str = None,
                 scheduled_for: str = None, post_name: str = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO posts (title, body, subreddit_type, source_content, source_file, scheduled_for, post_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, body, subreddit_type, source_content, source_file, scheduled_for, post_name))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.log_action(post_id, "created", f"Status: pending")
        
        return post_id
    
    def get_posts_by_status(self, status: str = "pending") -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM posts WHERE status = ? ORDER BY created_at ASC
        ''', (status,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_post_status(self, post_id: int, status: str, error_message: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == "posted":
            cursor.execute('''
                UPDATE posts SET status = ?, posted_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, post_id))
        else:
            if error_message:
                cursor.execute('''
                    UPDATE posts SET status = ?, error_message = ?
                    WHERE id = ?
                ''', (status, error_message, post_id))
            else:
                cursor.execute('''
                    UPDATE posts SET status = ? WHERE id = ?
                ''', (status, post_id))
        
        conn.commit()
        conn.close()
        
        self.log_action(post_id, "status_change", f"New status: {status}")
    
    def set_reddit_info(self, post_id: int, reddit_post_id: str, reddit_post_url: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE posts 
            SET reddit_post_id = ?, reddit_post_url = ?, status = 'posted', posted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (reddit_post_id, reddit_post_url, post_id))
        
        conn.commit()
        conn.close()
        
        self.log_action(post_id, "posted", f"Reddit ID: {reddit_post_id}")
    
    def add_word_file(self, file_name: str, file_path: str, content_preview: str = None,
                      chunk_count: int = 0) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO word_files (file_name, file_path, content_preview, chunk_count)
            VALUES (?, ?, ?, ?)
        ''', (file_name, file_path, content_preview, chunk_count))
        
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return file_id
    
    def log_action(self, post_id: int, action: str, details: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO post_logs (post_id, action, details)
            VALUES (?, ?, ?)
        ''', (post_id, action, details))
        
        conn.commit()
        conn.close()
    
    def get_post(self, post_id: int) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_posts(self, limit: int = 100) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM posts ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_post(self, post_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        
        return True
