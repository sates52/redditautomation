import os
import aiohttp
import asyncio
import logging
from typing import Dict
from pathlib import Path

# Try to handle version differences in browser-use
try:
    from browser_use import Agent, Browser, BrowserConfig
except ImportError:
    from browser_use import Agent, Browser
    # Some versions might not export BrowserConfig directly or use a different name
    BrowserConfig = None 
from langchain_nvidia_ai_endpoints import ChatNVIDIA

class BrowserUseRedditClient:
    def __init__(self, user_data_dir: str):
        self.user_data_dir = str(Path(user_data_dir).absolute())
        self.logger = logging.getLogger(__name__)
        
        # Check API key
        if not os.getenv("NVIDIA_API_KEY"):
            raise ValueError("Lütfen .env dosyasına NVIDIA_API_KEY ekleyin.")

    async def async_post(self, subreddit: str, title: str, body: str) -> dict:
        """Asenkron olarak gönderimi yapar"""
        self.logger.info("Browser-Use AI Agent başlatılıyor...")
        
        # Yapay Zeka modeli (NVIDIA üzerinden hızlı Llama modeli)
        llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct", temperature=0.0)
        
        # Kendi Chrome profilimizi kullanıyoruz (Giriş yapılmış olan)
        if BrowserConfig:
            browser_config = BrowserConfig(
                user_data_dir=self.user_data_dir,
                headless=False,
                disable_security=True
            )
            browser = Browser(config=browser_config)
        else:
            # Fallback if BrowserConfig is not available (some older/newer versions)
            browser = Browser(
                user_data_dir=self.user_data_dir,
                headless=False
            )
        
        task_instruction = f"""
        Go to https://www.reddit.com/r/{subreddit}/submit
        Wait for the page to completely load. 
        If you see any "Switch to markdown" or "Markdown Mode" button, click it.
        Fill in the Title field exactly with: "{title}"
        Fill in the Text/Body field exactly with: "{body}"
        Click the "Post" or "Submit" button to publish it.
        Wait for the success page to load and return the final URL of the created post.
        """
        
        agent = Agent(
            task=task_instruction,
            llm=llm,
            browser=browser
        )
        
        try:
            result = await agent.run()
            
            # Extract final URL from AI result if possible, or just return success
            self.logger.info(f"Browser-Use Görevi Tamamlandı! Sonuç: {result}")
            return {
                "success": True,
                "post_id": "auto-agent",
                "post_url": str(result)
            }
        except Exception as e:
            self.logger.error(f"Browser-Use Hata: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def post_to_subreddit(self, subreddit: str, title: str, body: str) -> dict:
        """Senkron olarak dışarıdan çağrılabilen köprü fonksiyon"""
        return asyncio.run(self.async_post(subreddit, title, body))
