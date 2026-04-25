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
            page.goto(submit_url)
            
            # Wait for title input
            page.wait_for_selector("textarea[placeholder='Title']", timeout=10000)
            
            # Fill title
            page.fill("textarea[placeholder='Title']", title)
            
            # Fill body
            # Reddit uses a rich text editor or markdown. Usually markdown is easier to target.
            # Look for the markdown mode button if possible, or just fill the textarea
            
            # Try to switch to Markdown mode if it's in Fancy Pant editor
            try:
                markdown_button = page.wait_for_selector("text=Markdown Mode", timeout=2000)
                if markdown_button:
                    markdown_button.click()
            except:
                pass # Already in markdown or selector different
                
            # Fill the post body
            # The selector for the body can be tricky.
            # It's often a textarea or a contenteditable div
            body_selector = "textarea[placeholder='Text (optional)']"
            page.wait_for_selector(body_selector, timeout=5000)
            page.fill(body_selector, body)
            
            # Wait a bit for UI to catch up
            time.sleep(1)
            
            # Click Post button
            # Button text is usually "Post"
            post_button = page.locator("button:has-text('Post')").first
            if post_button.is_enabled():
                post_button.click()
                
                # Wait for redirection to the new post
                # The URL should change from /submit to the post URL
                page.wait_for_url(lambda url: "/comments/" in url, timeout=15000)
                post_url = page.url
                post_id = post_url.split("/comments/")[1].split("/")[0]
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": post_url
                }
            else:
                return {
                    "success": False,
                    "error": "Post button is disabled (maybe missing title or body?)"
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
