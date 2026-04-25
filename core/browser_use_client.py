# -*- coding: utf-8 -*-
"""Browser-Use LOKAL AI Agent ile Reddit'e post atar.

Senin bilgisayarindaki Chrome profilini kullanir (login durumu korunur).
LLM olarak ChatOpenAI'yi NVIDIA endpoint'ine yonlendirir.
Boylece browser-use Pydantic uyumluluk sorunu ortadan kalkar.
"""
import os
import asyncio
import logging
from pathlib import Path

# browser-use imports - versiyon farkliliklarini yakala
from browser_use import Agent, Browser

# BrowserConfig vs BrowserProfile farki
try:
    from browser_use import BrowserConfig
except ImportError:
    BrowserConfig = None
try:
    from browser_use import BrowserProfile
except ImportError:
    BrowserProfile = None
try:
    from browser_use import BrowserContextConfig
except ImportError:
    BrowserContextConfig = None

from langchain_openai import ChatOpenAI


class BrowserUseRedditClient:
    def __init__(self, user_data_dir: str):
        self.user_data_dir = str(Path(user_data_dir).absolute())
        self.logger = logging.getLogger(__name__)

        self.api_key = os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY .env dosyasinda bulunamadi.")

    def _make_browser(self):
        """Versiyon farkliliklarini handle ederek Browser olusturur."""
        # Yeni versiyonlar: BrowserConfig + BrowserContextConfig
        if BrowserConfig and BrowserContextConfig:
            try:
                config = BrowserConfig(
                    headless=False,
                    disable_security=True,
                    new_context_config=BrowserContextConfig(
                        user_data_dir=self.user_data_dir,
                        no_viewport=True
                    )
                )
                return Browser(config=config)
            except Exception:
                pass

        # Eski versiyonlar: BrowserConfig basit
        if BrowserConfig:
            try:
                config = BrowserConfig(
                    headless=False,
                    user_data_dir=self.user_data_dir
                )
                return Browser(config=config)
            except Exception:
                pass

        # BrowserProfile varsa
        if BrowserProfile:
            try:
                return Browser(
                    profile=BrowserProfile(
                        user_data_dir=self.user_data_dir
                    ),
                    headless=False
                )
            except Exception:
                pass

        # Son care: parametresiz
        return Browser()

    async def async_post(self, subreddit: str, title: str, body: str) -> dict:
        self.logger.info("Browser-Use LOKAL AI Agent baslatiliyor...")

        # ChatOpenAI'yi NVIDIA'nin OpenAI-uyumlu endpoint'ine yonlendiriyoruz
        # browser-use ChatOpenAI'yi %100 destekler, Pydantic sorunu olmaz
        llm = ChatOpenAI(
            model="meta/llama-3.3-70b-instruct",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
            temperature=0.0
        )

        browser = self._make_browser()

        task = (
            f"Go to https://www.reddit.com/r/{subreddit}/submit\n"
            f"Wait for the page to load.\n"
            f'If you see a "Switch to markdown" button, click it.\n'
            f"Type the following text in the Title field: {title}\n"
            f"Type the following text in the Body/Text field: {body}\n"
            f"Click the Post button.\n"
            f"After posting, return the URL of the newly created post."
        )

        agent = Agent(task=task, llm=llm, browser=browser)

        try:
            result = await agent.run()
            self.logger.info(f"Browser-Use tamamlandi: {result}")
            return {
                "success": True,
                "post_id": "browser-use-local",
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
            except Exception:
                pass

    def post_to_subreddit(self, subreddit: str, title: str, body: str) -> dict:
        """Senkron kopru - CLI tarafindan cagrilir."""
        return asyncio.run(self.async_post(subreddit, title, body))

    def close(self):
        """Temizlik (cli.py tarafindan cagrilir)."""
        pass
