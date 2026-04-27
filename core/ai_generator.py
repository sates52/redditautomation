import os
import random
from typing import Dict, List, Optional
from openai import OpenAI
from pathlib import Path
import logging

from core.prompt_templates import VARIATIONS, SYSTEM_PROMPT_BASE

class AIGenerator:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        if not api_key:
            raise ValueError("NVIDIA API key is required")
        
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

    def generate_post(self, post_title: str, post_content: str, post_url: str) -> Dict:
        # Pick a random variation to keep content fresh
        variation = random.choice(VARIATIONS)
        system_prompt = SYSTEM_PROMPT_BASE.format(angle_description=variation['angle'])
        
        user_content = f"Blog Yazısı Özeti:\n\nBaşlık: {post_title}\n\nİçerik:\n{post_content}\n\nLink: {post_url}"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    self.logger.info(f"Generating Reddit post (Variation: {variation['name']}) for: {post_title}")
                else:
                    import time
                    wait_time = (attempt + 1) * 10
                    self.logger.info(f"Retrying API call (Attempt {attempt+1}/{max_retries}) after {wait_time}s wait...")
                    time.sleep(wait_time)
                
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.4, # Slightly higher for more variety
                    top_p=0.8,
                    max_tokens=2048,
                    stream=True
                )
                
                full_response = ""
                for chunk in completion:
                    if not chunk.choices:
                        continue
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                
                # Split title and body
                title, body = self._parse_reddit_response(full_response)
                
                # Check if URL is in body, if not (though prompt asks for it), append it safely with standard Markdown
                if post_url not in body:
                    body = f"{body}\n\n[Devamı için blog yazımızı inceleyebilirsiniz]({post_url})"
                
                return {
                    "success": True,
                    "title": title,
                    "body": body,
                    "variation_used": variation['name']
                }
                
            except Exception as e:
                error_str = str(e)
                self.logger.error(f"Error generating post: {error_str}")
                
                # If it's the last attempt or an error we shouldn't retry, break.
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": error_str
                    }

    def _parse_reddit_response(self, response_text: str) -> (str, str):
        """Parses the response to separate title and body."""
        lines = response_text.strip().split('\n')
        
        title = ""
        body_start_idx = 0
        
        # Look for title markers or just use the first non-empty line
        found_title = False
        for i, line in enumerate(lines):
            clean_line = line.strip()
            if not clean_line:
                continue
            
            # Remove common prefixes the model might add
            prefixes = ["1. Başlık:", "Başlık:", "Title:", "1. Title:"]
            for prefix in prefixes:
                if clean_line.startswith(prefix):
                    title = clean_line[len(prefix):].strip()
                    body_start_idx = i + 1
                    found_title = True
                    break
            
            if found_title:
                break
            
            # If no prefix found, the first line is the title
            title = clean_line.lstrip('#').lstrip('*').strip()
            body_start_idx = i + 1
            break
            
        body = '\n'.join(lines[body_start_idx:]).strip()
        
        # Fallback if parsing fails
        if not title:
            title = "İngilizce Öğrenme Yolculuğunuzda Yeni Bir Bakış"
            
        return title, body
