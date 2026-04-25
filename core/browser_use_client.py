# -*- coding: utf-8 -*-
import os
import asyncio
import logging
from pathlib import Path

from browser_use import Agent, Browser, BrowserConfig, BrowserContextConfig
from langchain_openai import ChatOpenAI

class BrowserUseRedditClient:
    """Browser-Use AI Agent ile Reddit'e post atan istemci.
    
    NVIDIA API'yi OpenAI uyumlu endpoint üzerinden kullanır,
    böylece browser-use'un beklediği ChatOpenAI arayüzü sağlanır.
    """

    def __init__(self, user_data_dir: str):
        self.user_data_dir = str(Path(user_data_dir).absolute())
        self.logger = logging.getLogger(__name__)
        
        self.api_key = os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY .env dosyasinda bulunamadi.")

    async def async_post(self, subreddit: str, title: str, body: str) -> dict:
        self.logger.info("Browser-Use AI Agent baslatiliyor...")
        
        # ChatOpenAI'yi NVIDIA'nin OpenAI-uyumlu endpoint'ine yonlendiriyoruz
        # Bu sayede browser-use'un Pydantic uyumluluk sorunu ortadan kalkiyor
        llm = ChatOpenAI(
            model="meta/llama-3.3-70b-instruct",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
            temperature=0.0
        )
        
        browser = Browser(
            config=BrowserConfig(
                headless=False,
                disable_security=True,
                new_context_config=BrowserContextConfig(
                    user_data_dir=self.user_data_dir,
                    no_viewport=True
                )
            )
        )
        
        # Escape any quotes in title/body to avoid breaking the prompt
        safe_title = title.replace('"', '\\"')
        safe_body = body.replace('"', '\\"')
        
        task = f"""Go to https://www.reddit.com/r/{subreddit}/submit
Wait for the page to fully load.
If you see a "Switch to markdown" or "Markdown Mode" button, click it.
Type "{safe_title}" in the Title field.
Type the following text in the Body/Text field: "{safe_body}"
Click the Post button to submit.
After posting, return the URL of the newly created post."""
        
        agent = Agent(task=task, llm=llm, browser=browser)
        
        try:
            result = await agent.run()
            self.logger.info(f"Browser-Use gorevi tamamlandi: {result}")
            return {
                "success": True,
                "post_id": "browser-use-agent",
                "post_url": str(result)
            }
        except Exception as e:
            self.logger.error(f"Browser-Use hata: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            try:
                await browser.close()
            except:
                pass

    def post_to_subreddit(self, subreddit: str, title: str, body: str) -> dict:
        """Senkron kopru fonksiyon - CLI tarafindan cagrilir."""
        return asyncio.run(self.async_post(subreddit, title, body))

    def close(self):
        """Temizlik (cli.py tarafindan cagrilir)."""
        pass
