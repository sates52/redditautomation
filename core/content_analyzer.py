from typing import List, Dict
from .word_parser import WordParser


class ContentAnalyzer:
    def __init__(self, max_chunk_size: int = 500):
        self.max_chunk_size = max_chunk_size
    
    def analyze(self, parsed_content: Dict) -> List[Dict]:
        chunks = []
        
        title = parsed_content.get("title", "")
        
        for section in parsed_content.get("sections", []):
            chunk = {
                "title": title,
                "content": section["text"],
                "type": section["type"],
                "source": "section"
            }
            chunks.append(chunk)
        
        for i, q in enumerate(parsed_content.get("questions", [])):
            chunk = {
                "title": title,
                "content": f"{q['question']}\n{q.get('answer', '')}",
                "type": "question",
                "source": f"question_{i}"
            }
            chunks.append(chunk)
        
        for i, lst in enumerate(parsed_content.get("lists", [])):
            list_text = "\n".join(lst)
            chunk = {
                "title": title,
                "content": list_text,
                "type": "list",
                "source": f"list_{i}"
            }
            chunks.append(chunk)
        
        return chunks
    
    def chunk_by_size(self, text: str, max_size: int = None) -> List[str]:
        if max_size is None:
            max_size = self.max_chunk_size
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 <= max_size:
                current_chunk.append(word)
                current_size += len(word) + 1
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
