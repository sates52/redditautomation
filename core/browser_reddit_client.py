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
            
            # Wait for basic UI structure to appear instead of waiting for networkidle
            # (Reddit never reaches networkidle due to continuous tracking/ad requests)
            page.wait_for_selector("body", timeout=30000)
            time.sleep(3) # Give React a moment to render the complex UI
            
            # Fill Title
            title_found = False
            title_selectors = [
                "textarea[name='title']",
                "textarea[placeholder='Title']",
                "h1[contenteditable='true']",
                "textarea[placeholder*='Title']",
                "shreddit-composer" # Fallback wrapper
            ]
            
            for selector in title_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, title)
                    title_found = True
                    self.logger.info(f"Title filled using selector: {selector}")
                    # Switch focus specifically to the body editor using JS to bypass shadow DOM completely
                    page.evaluate("""
                        setTimeout(() => {
                            // Find all possible body containers
                            const textAreas = document.querySelectorAll('textarea');
                            const editables = document.querySelectorAll('div[contenteditable="true"]');
                            
                            // Usually the body is the last/largest editable div or second textarea
                            if (editables.length > 0) {
                                editables[editables.length - 1].focus();
                            } else if (textAreas.length > 1) {
                                textAreas[textAreas.length - 1].focus();
                            }
                        }, 500);
                    """)
                    time.sleep(1.5)
                    break
                except:
                    continue
            
            if not title_found:
                raise Exception("Could not find Title input field")

            # Fill Body using Keyboard typing 
            self.logger.info("Typing body using keyboard simulation (bypassing strict selectors)...")
            page.keyboard.type(body, delay=0)
            time.sleep(1)

            # Click Post / Submit
            submit_found = False
            
            # Since Reddit is using Shadow DOM components now, standard button selectors often fail.
            # We can use get_by_role which pierces shadow bounds, or look for the Post button within shreddit-composer
            try:
                post_btn = page.locator("button, shreddit-button").filter(has_text="Post").first
                if post_btn.is_visible():
                    post_btn.click()
                    submit_found = True
                    self.logger.info("Submit button clicked via generic locator.")
            except:
                pass
                
            if not submit_found:
                try:
                    # Alternative: get_by_role
                    role_btn = page.get_by_role("button", name="Post").first
                    if role_btn.is_visible():
                        role_btn.click()
                        submit_found = True
                        self.logger.info("Submit button clicked via get_by_role.")
                except:
                    pass

            # Final ultimate fallback for clicking Post
            if not submit_found:
                try:
                    page.evaluate("""
                        const btn = Array.from(document.querySelectorAll('button, shreddit-button, div')).find(el => el.textContent.trim() === 'Post');
                        if (btn) btn.click();
                    """)
                    submit_found = True
                    self.logger.info("Submit button clicked via Javascript evaluate.")
                except:
                    pass

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
