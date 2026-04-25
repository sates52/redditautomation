# -*- coding: utf-8 -*-
"""Old Reddit (old.reddit.com) uzerinden post atan Playwright istemci.

Yeni Reddit arayuzu Shadow DOM ve React kullandigi icin Playwright
ile uyumsuz. Eski Reddit ise dumduz HTML formlari kullanir ve
otomasyon icin mukemmeldir.
"""
import os
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError


class BrowserRedditClient:
    def __init__(self, user_data_dir: str, headless: bool = False):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.logger = logging.getLogger(__name__)
        self.browser_context = None
        self.playwright = None

    def _start_browser(self):
        if not self.playwright:
            self.playwright = sync_playwright().start()
        if not self.browser_context:
            self.browser_context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
        return self.browser_context

    def close(self):
        if self.browser_context:
            self.browser_context.close()
            self.browser_context = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def check_login(self) -> bool:
        """old.reddit.com uzerinden login kontrolu yapar."""
        context = self._start_browser()
        page = context.new_page()
        try:
            page.goto("https://old.reddit.com/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            
            # old.reddit.com'da login olunca sag ustte kullanici adi gorulur
            # Login degilse "login or register" linki gorulur
            user_el = page.query_selector("span.user a.login-required")
            if user_el:
                # Demek ki login degil
                self.logger.info("Login degil. Yeni Reddit uzerinden login deneniyor...")
                page.goto("https://www.reddit.com/login", wait_until="domcontentloaded", timeout=30000)
                print("\n[!] Reddit oturumu acik degil. Lutfen acilan tarayicida giris yapin.")
                print("[!] Giris yaptiktan sonra bu pencereyi kapatmayin.\n")
                
                # Kullanicinin login olmasini bekle
                for _ in range(120):  # 4 dakika bekle
                    time.sleep(2)
                    try:
                        page.goto("https://old.reddit.com/", wait_until="domcontentloaded", timeout=15000)
                        time.sleep(1)
                        user_check = page.query_selector("span.user a.login-required")
                        if not user_check:
                            # Login basarili
                            self.logger.info("Login basarili!")
                            print("[OK] Giris basarili!")
                            return True
                    except:
                        continue
                return False
            else:
                self.logger.info("Zaten login durumunda.")
                return True
        except Exception as e:
            self.logger.error(f"Login kontrol hatasi: {e}")
            return False
        finally:
            page.close()

    def post_to_subreddit(self, subreddit: str, title: str, body: str) -> dict:
        """old.reddit.com/r/{sub}/submit uzerinden post atar.
        
        Old Reddit'in formu cok basit:
        - input[name='title'] -> Baslik
        - textarea[name='text'] -> Icerik (selftext tab)
        - button[name='submit'] -> Gonder
        """
        context = self._start_browser()
        page = context.new_page()

        try:
            submit_url = f"https://old.reddit.com/r/{subreddit}/submit?selftext=true"
            self.logger.info(f"Navigating to {submit_url}")
            page.goto(submit_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)

            # Selftext (text post) tabinin secili oldugundan emin ol
            text_tab = page.query_selector("a.text-button, li.selected a[href*='selftext']")
            if text_tab:
                text_tab.click()
                time.sleep(0.5)

            # Baslik doldur
            title_input = page.wait_for_selector("textarea[name='title'], input[name='title']", timeout=10000)
            title_input.fill(title)
            self.logger.info("Baslik dolduruldu.")

            # Icerik doldur (selftext textarea)
            body_textarea = page.wait_for_selector("textarea[name='text']", timeout=10000)
            body_textarea.fill(body)
            self.logger.info("Icerik dolduruldu.")

            # Gonder butonuna bas
            # old.reddit.com'da buton class="save" ve type="submit"
            submit_btn = page.locator("button.save[type='submit']").first
            submit_btn.scroll_into_view_if_needed()
            time.sleep(0.5)
            submit_btn.click()
            self.logger.info("Gonder butonuna basildi.")

            # Yonlendirmeyi bekle (post sayfasina gider)
            # old.reddit.com'da /comments/ iceren URL'ye yonlendirir
            page.wait_for_url(lambda url: "/comments/" in url, timeout=20000)
            post_url = page.url
            post_id = post_url.split("/comments/")[1].split("/")[0] if "/comments/" in post_url else "unknown"

            self.logger.info(f"Post basarili! URL: {post_url}")
            return {
                "success": True,
                "post_id": post_id,
                "post_url": post_url
            }

        except Exception as e:
            self.logger.error(f"Browser post hatasi: {e}")
            screenshot_path = Path("data/error_screenshot.png")
            try:
                page.screenshot(path=str(screenshot_path))
            except:
                pass
            return {
                "success": False,
                "error": str(e),
                "screenshot": str(screenshot_path)
            }
        finally:
            page.close()
