import praw
from typing import Optional, Dict
from datetime import datetime
import time


class RedditClient:
    def __init__(self, client_id: str, client_secret: str, user_agent: str, 
                 username: str, password: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.username = username
        self.password = password
        
        self.reddit = None
        self.user = None
        self._initialize()
    
    def _initialize(self):
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                username=self.username,
                password=self.password
            )
            self.user = self.reddit.user.me()
            print(f"Connected to Reddit as {self.user.name}")
        except Exception as e:
            print(f"Failed to connect to Reddit: {e}")
            self.user = None
    
    def is_authenticated(self) -> bool:
        return self.user is not None
    
    def post_to_subreddit(self, subreddit_name: str, title: str, text: str, 
                          flair: str = None) -> Dict:
        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Not authenticated to Reddit"
            }
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            post = subreddit.submit(
                title=title,
                selftext=text
            )
            
            if flair:
                post.flair(flair)
            
            return {
                "success": True,
                "post_id": post.id,
                "post_url": post.url,
                "permalink": post.permalink,
                "title": title,
                "subreddit": str(subreddit),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "post_id": None,
                "post_url": None,
                "permalink": None,
                "title": title,
                "subreddit": subreddit_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_subreddit(self, subreddit_name: str):
        try:
            return self.reddit.subreddit(subreddit_name)
        except Exception as e:
            print(f"Error getting subreddit: {e}")
            return None
    
    def check_rate_limit(self) -> Dict:
        if not self.is_authenticated():
            return {"can_post": False, "reason": "Not authenticated"}
        
        try:
            limits = self.reddit.karma()
            return {
                "can_post": True,
                "karma": limits,
                "reason": "OK"
            }
        except Exception as e:
            return {
                "can_post": False,
                "reason": str(e)
            }
