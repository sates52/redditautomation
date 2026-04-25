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
        """Parses the CSV by merging multiline rows based on row-start patterns."""
        posts = []
        try:
            with open(self.csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines:
                return []

            # Identify row start: ID,Author,"Date" (e.g., 2201,1,"2023-...)
            row_start_pattern = re.compile(r'^(\d+),(\d+),"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"')
            
            rows_raw = []
            current_row = ""
            
            for line in lines[1:]: # Skip header
                if row_start_pattern.match(line):
                    if current_row:
                        rows_raw.append(current_row)
                    current_row = line
                else:
                    current_row += line
            
            if current_row:
                rows_raw.append(current_row)

            # Now parse each merged row using standard csv reader
            for raw_text in rows_raw:
                reader = csv.reader([raw_text.strip()])
                try:
                    row = next(reader)
                    # Standard WordPress export column indices:
                    # ID(0), post_author(1), post_date(2), post_date_gmt(3), post_content(4), post_title(5), ...
                    if len(row) > 7:
                        p_id = row[0]
                        p_content = row[4]
                        p_title = row[5]
                        p_status = row[7]
                        p_type = row[20] if len(row) > 20 else ""
                        p_name = row[11] if len(row) > 11 else ""

                        if p_status == 'publish' and p_type == 'post':
                            clean_content = self.clean_html(p_content)
                            posts.append({
                                'id': p_id,
                                'title': p_title,
                                'content': clean_content,
                                'name': p_name
                            })
                except Exception as e:
                    continue
            
            self.logger.info(f"Successfully parsed {len(posts)} posts using line-merging parser.")
            return posts

        except Exception as e:
            self.logger.error(f"Error parsing CSV with line-merging: {e}")
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
