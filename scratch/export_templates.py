import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.ai_generator import AIGenerator
from models.database import Database
from config.settings import NVIDIA_API_KEY, NVIDIA_API_URL, NVIDIA_MODEL, DB_PATH

def main():
    load_dotenv()
    db = Database(str(DB_PATH))
    ai = AIGenerator(NVIDIA_API_KEY, NVIDIA_API_URL, NVIDIA_MODEL)
    
    # Fetch 3 oldest pending posts
    pending_posts = db.get_posts_by_status('pending')
    # Filter to ensure we only get the original posts (from CSV/Word)
    # Looking at the DB, original posts have source_content and status 'pending'
    # db.get_posts_by_status returns them ordered by created_at.
    # To be sure of ID order:
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE status = 'pending' ORDER BY id ASC LIMIT 1")
    oldest_posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not oldest_posts:
        print("No pending posts found in DB.")
        return

    output_file = "reddit_company_insight.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Reddit Post Template (Konuşarak Öğren Kurumsal Analiz)\n\n")
        f.write("Bu içerik NVIDIA AI tarafından şirket verileri ve öğrenci analizleri odaklı oluşturulmuştur.\n\n")
        
        for i, post in enumerate(oldest_posts):
            print(f"Generating post {i+1}/3: {post['title']}...")
            
            post_url = ""
            if post.get('post_name'):
                post_url = f"https://www.konusarakogren.com/blog/{post['post_name']}"
                
            result = ai.generate_post(post['title'], post['body'], post_url)
            
            if result['success']:
                f.write(f"## POST {i+1}: {post['title']}\n")
                f.write(f"**Original ID:** {post['id']}\n")
                f.write(f"**Target Subreddit:** r/KonusarakOgren veya r/IngilizceKonusma\n\n")
                f.write(f"### [REDDIT TITLE]\n{result['title']}\n\n")
                f.write(f"### [REDDIT BODY]\n{result['body']}\n\n")
                f.write("---\n\n")
                print(f"Successfully generated post {i+1}")
            else:
                print(f"Failed to generate post {i+1}: {result.get('error')}")

    print(f"\nDone! Templates saved to: {output_file}")

if __name__ == "__main__":
    main()
