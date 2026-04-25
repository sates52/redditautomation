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
        
        # Yama: ChatNVIDIA objesine browser-use'un beklediği 'provider' özelliğini ekliyoruz
        if not hasattr(llm, 'provider'):
            setattr(llm, 'provider', 'nvidia')
        
        # Kendi Chrome profilimizi kullanıyoruz
        if BrowserConfig:
            browser_config = BrowserConfig(
                user_data_dir=self.user_data_dir,
                headless=False
            )
            browser = Browser(config=browser_config)
        else:
            browser = Browser(
                user_data_dir=self.user_data_dir,
                headless=False
            )
        
        task_instruction = f"""
        Go to https://www.reddit.com/r/{subreddit}/submit. 
        Wait for the page to load. 
        If you see any "Switch to markdown" button, click it. 
        Enter Title: "{title}"
        Enter Text: "{body}"
        Click the Post/Submit button.
        Verify that the post was created and output the current URL.
        """
        
        agent = Agent(
            task=task_instruction,
            llm=llm,
            browser=browser
        )
        
        try:
            result = await agent.run()
            # Kapatma işlemleri (Browser-use Browser nesnesi kendisi yönetir ama temiz bırakalım)
            await browser.close()
            
            return {
                "success": True,
                "post_id": "auto-agent",
                "post_url": str(result)
            }
        except Exception as e:
            self.logger.error(f"Browser-Use Hata: {str(e)}")
            await browser.close()
            return {
                "success": False,
                "error": str(e)
            }
            
    def post_to_subreddit(self, subreddit: str, title: str, body: str) -> dict:
        """Senkron olarak dışarıdan çağrılabilen köprü fonksiyon"""
        return asyncio.run(self.async_post(subreddit, title, body))

    def close(self):
        """Temizlik (Cli.py tarafından çağrılır)"""
        pass
