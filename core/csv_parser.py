import pandas as pd
from bs4 import BeautifulSoup
import logging
import csv
from typing import List, Dict

class CSVParser:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.logger = logging.getLogger(__name__)

    def parse_posts(self) -> List[Dict]:
        """Parses the CSV and returns a list of published blog posts."""
        try:
            # More robust CSV reading for multiline HTML content
            df = pd.read_csv(
                self.csv_path, 
                sep=',',
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
                escapechar='\\',
                on_bad_lines='warn',
                encoding='utf-8'
            )
            
            # Filter for published posts
            published_posts = df[(df['post_status'] == 'publish') & (df['post_type'] == 'post')]
            
            posts = []
            for _, row in published_posts.iterrows():
                clean_content = self.clean_html(str(row['post_content']))
                posts.append({
                    'id': row['ID'],
                    'title': row['post_title'],
                    'content': clean_content,
                    'name': row['post_name'],
                    'url': f"https://www.konusarakogren.com/blog/{row['post_name']}"
                })
            
            self.logger.info(f"Successfully parsed {len(posts)} posts from {self.csv_path}")
            return posts

        except Exception as e:
            self.logger.error(f"Error parsing CSV: {e}")
            return []

    def clean_html(self, html_content: str) -> str:
        """Removes HTML tags and cleans up the text content."""
        if not html_content or html_content == 'nan':
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove scripts and styles
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            
            # Get text and handle whitespace
            text = soup.get_text(separator='\n')
            
            # Clean up multiple newlines and spaces
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return '\n'.join(lines)
            
        except Exception as e:
            self.logger.warning(f"Error cleaning HTML: {e}")
            return html_content # Return original if cleansing fails
