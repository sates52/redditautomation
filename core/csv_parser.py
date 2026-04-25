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
        """Parses the CSV and returns a list of published blog posts using standard csv module."""
        posts = []
        try:
            with open(self.csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
                # WordPress CSVs often use complex escaping, DictReader handles basic cases well
                # We'll use a standard reader to be more flexible with field counts
                reader = csv.reader(f, delimiter=',', quotechar='"')
                
                # Get header
                try:
                    header = next(reader)
                except StopIteration:
                    return []

                # Find column indices
                try:
                    idx_status = header.index('post_status')
                    idx_type = header.index('post_type')
                    idx_title = header.index('post_title')
                    idx_content = header.index('post_content')
                    idx_name = header.index('post_name')
                    idx_id = header.index('ID')
                except ValueError as e:
                    self.logger.error(f"Missing required columns in CSV: {e}")
                    return []

                for row in reader:
                    # Skip empty rows or rows with missing critical fields
                    if not row or len(row) <= max(idx_status, idx_type, idx_title, idx_content):
                        continue

                    # Filter for published posts
                    if row[idx_status] == 'publish' and row[idx_type] == 'post':
                        clean_content = self.clean_html(str(row[idx_content]))
                        posts.append({
                            'id': row[idx_id],
                            'title': row[idx_title],
                            'content': clean_content,
                            'name': row[idx_name]
                        })
            
            self.logger.info(f"Successfully parsed {len(posts)} posts using robust parser.")
            return posts

        except Exception as e:
            self.logger.error(f"Error parsing CSV with robust reader: {e}")
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
