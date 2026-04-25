import pandas as pd
from bs4 import BeautifulSoup
import logging
import csv
import sys
import re
from typing import List, Dict

class CSVParser:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.logger = logging.getLogger(__name__)
        # Increase field size limit for very large blog posts
        csv.field_size_limit(sys.maxsize)

    def parse_posts(self) -> List[Dict]:
        """Parses the CSV and returns a list of published blog posts using Regex for maximum robustness."""
        posts = []
        try:
            with open(self.csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # This regex looks for the start of a row (Number,Number,"Date")
            # and captures until it finds a post indicator (,post,,0)
            # The structure is: ID,author,date,gmt,content,title,excerpt,status,...type,...,count
            # We focus on capturing ID, Content, Title and Name
            pattern = re.compile(
                r'(\d+),\d+,"[^"]+","[^"]+",(.*?),"([^"]+)",.*?,publish,.*?,post,.*?,(\d+)', 
                re.DOTALL
            )
            
            matches = pattern.finditer(content)
            
            for match in matches:
                p_id = match.group(1)
                p_content = match.group(2)
                p_title = match.group(3)
                
                # Cleanup the content (it might have leading/trailing quotes from the regex)
                p_content = p_content.strip()
                if p_content.startswith('"') and p_content.endswith('"'):
                    p_content = p_content[1:-1]
                
                # Fix escaped quotes that WP uses (double quotes "")
                p_content = p_content.replace('""', '"')
                
                clean_content = self.clean_html(p_content)
                
                posts.append({
                    'id': p_id,
                    'title': p_title,
                    'content': clean_content,
                    'name': p_title.lower().replace(' ', '-') # Fallback slug
                })
            
            # If regex didn't find many (unlikely but safe), fallback to a simpler line reader
            if len(posts) < 100:
                self.logger.warning("Regex parser found very few results, might be a header mismatch.")
            
            self.logger.info(f"Successfully parsed {len(posts)} posts using Regex parser.")
            return posts

        except Exception as e:
            self.logger.error(f"Error parsing CSV with regex: {e}")
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
