# -*- coding: utf-8 -*-
"""Browser-Use Cloud API ile Reddit'e post atan istemci.

Bu istemci, browser-use'un bulut servisini (bu_ API key) kullanir.
Tarayici senin bilgisayarinda acilmaz, her sey bulutta doner.
Ne Playwright, ne LLM, ne lokal tarayici gerektirir.
"""
import os
import time
import logging
import requests

class BrowserUseRedditClient:
    API_BASE = "https://api.browser-use.com/api/v3"

    def __init__(self, user_data_dir: str = ""):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv("BROWSER_USE_API_KEY")
        if not self.api_key:
            raise ValueError("BROWSER_USE_API_KEY .env dosyasinda bulunamadi.")
        self.headers = {
            "X-Browser-Use-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def post_to_subreddit(self, subreddit: str, title: str, body: str) -> dict:
        """Browser-Use Cloud API ile Reddit'e post atar."""
        self.logger.info(f"Browser-Use Cloud API ile post gonderiliyor: {title[:50]}...")

        task_text = (
            f'Go to https://www.reddit.com/r/{subreddit}/submit\n'
            f'Wait for the page to load.\n'
            f'If you see a "Switch to markdown" or "Markdown Mode" button, click it.\n'
            f'Fill the Title field with: {title}\n'
            f'Fill the Body/Text field with: {body}\n'
            f'Click the Post or Submit button.\n'
            f'Wait for the post to be created and return the final URL of the new post.'
        )

        # 1. Oturum baslat (task gonder)
        try:
            resp = requests.post(
                f"{self.API_BASE}/sessions",
                json={"task": task_text},
                headers=self.headers,
                timeout=30
            )
            resp.raise_for_status()
            session = resp.json()
            session_id = session.get("id")
            self.logger.info(f"Browser-Use oturumu basladi: {session_id}")
        except Exception as e:
            self.logger.error(f"Oturum baslatma hatasi: {e}")
            return {"success": False, "error": str(e)}

        # 2. Sonucu bekle (polling)
        max_wait = 120  # saniye
        poll_interval = 5
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            try:
                status_resp = requests.get(
                    f"{self.API_BASE}/sessions/{session_id}",
                    headers=self.headers,
                    timeout=15
                )
                status_resp.raise_for_status()
                data = status_resp.json()
                status = data.get("status", "")

                self.logger.info(f"Browser-Use durum: {status} ({elapsed}s)")

                if status in ("completed", "finished", "done"):
                    output = data.get("output", data.get("result", ""))
                    self.logger.info(f"Browser-Use basarili: {output}")
                    return {
                        "success": True,
                        "post_id": "browser-use-cloud",
                        "post_url": str(output)
                    }
                elif status in ("failed", "error"):
                    error_msg = data.get("error", data.get("output", "Bilinmeyen hata"))
                    self.logger.error(f"Browser-Use basarisiz: {error_msg}")
                    return {"success": False, "error": str(error_msg)}

            except Exception as e:
                self.logger.warning(f"Polling hatasi (devam ediliyor): {e}")
                continue

        return {"success": False, "error": f"Zaman asimi ({max_wait}s)"}

    def close(self):
        """Temizlik (cli.py tarafindan cagrilir)."""
        pass
