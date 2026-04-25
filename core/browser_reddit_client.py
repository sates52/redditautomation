# -*- coding: utf-8 -*-
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
        """Checks if logged in, opens browser for manual login if not."""
        context = self._start_browser()
        page = context.new_page()
        page.goto("https://www.reddit.com/")
        
        # Check if login button exists or if profile icon exists
        try:
            # If we see "Log In" button, we are likely not logged in
            login_button = page.wait_for_selector("text=Log In", timeout=5000)
            if login_button:
                self.logger.info("Not logged in. Please log in manually in the opened browser.")
                print("\n[!] Reddit oturumu açık değil. Lütfen açılan tarayıcıda giriş yapın.")
                print("[!] Giriş yaptıktan sonra bu pencereyi kapatmayın, sistem devam edecektir.\n")
                
                # Wait for user to login - we'll check for profile icon periodically
                while True:
                    try:
                        # reddit.com/user/me should redirect to profile if logged in
                        # or check for a selector that only appears when logged in
                        if page.query_selector("[aria-label='User settings']") or page.query_selector("#user-drawer-button"):
                            self.logger.info("Login detected!")
                            print("[✓] Giriş başarılı!")
                            break
                    except:
                        pass
                    time.sleep(2)
                return True
        except TimeoutError:
            # If no login button found, maybe we are already logged in
            self.logger.info("Likely already logged in.")
            return True
        finally:
            page.close()

    def post_to_subreddit(self, subreddit: str, title: str, body: str) -> dict:
        context = self._start_browser()
        page = context.new_page()
        
        try:
            submit_url = f"https://www.reddit.com/r/{subreddit}/submit"
            self.logger.info(f"Navigating to {submit_url}")
            # Use 'domcontentloaded' instead of 'load' to avoid waiting for heavy ads/trackers
            # and increase timeout to 60 seconds
            page.goto(submit_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for any of the main inputs to appear (indicating page loaded)
            page.wait_for_load_state("networkidle")
            
            # Try to switch to Markdown mode if it's not already there
            # In some versions, it's hidden under 'More options' (three dots)
            try:
                # Try to find 'More options' first if markdown switch isn't visible
                more_options = page.locator("button[aria-label*='More' i], button[aria-label*='options' i]").first
                if more_options.is_visible():
                    more_options.click()
                    time.sleep(0.5)
            except:
                pass

            markdown_selectors = [
                "button:has-text('Switch to markdown')",
                "button:has-text('Markdown Mode')",
                "button:has-text('Markdown')"
            ]
            
            for selector in markdown_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible():
                        self.logger.info(f"Switching to Markdown mode using: {selector}")
                        btn.click()
                        time.sleep(1)
                        break
                except:
                    continue

            # Fill Title
            # More robust selectors for Title
            title_found = False
            title_selectors = [
                "textarea[name='title']",
                "textarea[placeholder='Title']",
                "h1[contenteditable='true']",
                "textarea[placeholder*='Title']"
            ]
            
            for selector in title_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, title)
                    title_found = True
                    self.logger.info(f"Title filled using selector: {selector}")
                    break
                except:
                    continue
            
            if not title_found:
                raise Exception("Could not find Title input field")

            # Fill Body
            # In Markdown mode, it's usually a textarea
            body_found = False
            body_selectors = [
                "textarea[name='text']",
                "textarea[placeholder*='Text']",
                "textarea[placeholder*='optional']",
                "div[contenteditable='true']"
            ]
            
            for selector in body_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, body)
                    body_found = True
                    self.logger.info(f"Body filled using selector: {selector}")
                    break
                except:
                    continue
            
            if not body_found:
                raise Exception("Could not find Body input field")

            # Click Post / Submit
            submit_found = False
            submit_button_selectors = [
                "button:has-text('Post')",
                "button[type='submit']",
                "button:has-text('Submit')"
            ]
            
            for selector in submit_button_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_enabled():
                        btn.click()
                        submit_found = True
                        self.logger.info(f"Submit button clicked using selector: {selector}")
                        break
                except:
                    continue

            if not submit_found:
                # One last try - maybe the button isn't enabled because of a small delay
                time.sleep(2)
                btn = page.locator("button:has-text('Post')").first
                if btn.is_enabled():
                    btn.click()
                    submit_found = True

            if not submit_found:
                raise Exception("Could not find or click enabled Submit button")

            # Wait for redirection to the new post
            page.wait_for_url(lambda url: "/comments/" in url, timeout=20000)
            post_url = page.url
            post_id = post_url.split("/comments/")[1].split("/")[0]
            
            return {
                "success": True,
                "post_id": post_id,
                "post_url": post_url
            }
                
        except Exception as e:
            self.logger.error(f"Browser post error: {e}")
            # Take screenshot for debugging
            screenshot_path = Path("data/error_screenshot.png")
            page.screenshot(path=str(screenshot_path))
            return {
                "success": False,
                "error": str(e),
                "screenshot": str(screenshot_path)
            }
        finally:
            page.close()
