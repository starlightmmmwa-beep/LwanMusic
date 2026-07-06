from os import getenv
from typing import List, Optional
from dotenv import load_dotenv
import random

# Load environment variables from .env file (create one from sample.env)
load_dotenv()


class Config:
    """
    Configuration class for managing bot settings.

    All settings are loaded from environment variables with sensible defaults where applicable.
    Required variables are validated on initialization through the check() method.
    """

    def __init__(self):
        """Initialize configuration by loading all environment variables."""

        # ============ TELEGRAM API CREDENTIALS ============
        # Get these from https://my.telegram.org
        # Telegram API ID (numeric)
        self.API_ID: int = int(getenv("API_ID", "0"))
        # Telegram API Hash (hexadecimal)
        self.API_HASH: str = getenv("API_HASH", "")

        # ============ BOT CONFIGURATION ============
        # Bot token from @BotFather
        self.BOT_TOKEN: str = getenv("BOT_TOKEN", "")
        # Group/channel ID for logs (must be negative)
        self.LOGGER_ID: int = int(getenv("LOGGER_ID", "0"))
        # Your user ID (get from @elevenytsbot)
        self.OWNER_ID: int = int(getenv("OWNER_ID", "0"))

        # ============ DATABASE CONFIGURATION ============
        # MongoDB connection URL (mongodb+srv://...)
        self.MONGO_URL: str = getenv("MONGO_DB_URI", "")

        # ============ MUSIC BOT LIMITS ============
        # Convert minutes to seconds for duration limit
        # Max song duration (default: 300 min)
        self.DURATION_LIMIT: int = int(getenv("DURATION_LIMIT", "300")) * 60
        # Max songs in queue (default: 30)
        self.QUEUE_LIMIT: int = int(getenv("QUEUE_LIMIT", "30"))
        # Max songs from playlist (default: 20)
        self.PLAYLIST_LIMIT: int = int(getenv("PLAYLIST_LIMIT", "20"))

        # ============ ASSISTANT/USERBOT SESSIONS ============
        # Pyrogram session strings - get from @genStringBot
        # You can have up to 3 assistants for handling multiple groups
        # Primary assistant (required)
        self.SESSION1: str = getenv("STRING_SESSION", "")
        # Secondary assistant (optional)
        self.SESSION2: str = getenv("STRING_SESSION2", "")
        # Tertiary assistant (optional)
        self.SESSION3: str = getenv("STRING_SESSION3", "")

        # ============ SUPPORT LINKS ============
        self.SUPPORT_CHANNEL: str = getenv(
            "SUPPORT_CHANNEL", "https://t.me/bookbykosoemoe")
        self.SUPPORT_CHAT: str = getenv("SUPPORT_CHAT", "https://t.me/+B7WGcxuyNQNkMjg1")

        # ============ EXCLUDED CHATS ============
        # Parse comma-separated chat IDs that assistants should never leave
        self.EXCLUDED_CHATS: List[int] = self._parse_excluded_chats()

        # ============ FEATURE FLAGS ============
        # Auto-end stream when queue is empty
        self.AUTO_END: bool = self._str_to_bool(getenv("AUTO_END", "False"))
        # Auto-leave inactive chats
        self.AUTO_LEAVE: bool = self._str_to_bool(getenv("AUTO_LEAVE", "False"))
        # Enable/disable thumbnail generation (set False to use default thumb)
        self.THUMB_GEN: bool = self._str_to_bool(getenv("THUMB_GEN", "True"))
        # Enable/disable video playback commands (/vplay)
        self.VIDEO_PLAY: bool = self._str_to_bool(getenv("VIDEO_PLAY", "True"))
        # Maximum video height (in pixels) when downloading /vplay media
        self.VIDEO_MAX_HEIGHT: int = self._parse_video_height()

        # ArtistBots API
        self.ARTISTBOTS_API_URL: str = getenv("ARTISTBOTS_API_URL", "http://Artistbotsapi.onrender.com")
        self.ARTISTBOTS_KEY: str = getenv("ARTISTBOTS_KEY", "")
        self.ENABLE_API: bool = self._str_to_bool(getenv("ENABLE_API", "True"))
        self.ENABLE_COOKIES_FALLBACK: bool = self._str_to_bool(getenv("ENABLE_COOKIES_FALLBACK", "True"))
        self.API_TIMEOUT: int = int(getenv("API_TIMEOUT", "60"))
        self.API_STREAM_TIMEOUT: int = int(getenv("API_STREAM_TIMEOUT", "300"))

        # ============ YOUTUBE COOKIES ============
        # Parse space-separated cookie URLs for age-restricted content
        self.COOKIES_URL: List[str] = self._parse_cookies()

        # ============ IMAGE URLS (ပုံ ၅ ပုံ အလှည့်ကျသုံးရန်) ============
        self.IMAGE_LIST: List[str] = [
            "https://github.com/starlightmwamm-droid/Photo/blob/main/Lwan/LwanMusic%20(1).png?raw=true",
            "https://github.com/starlightmwamm-droid/Photo/blob/main/Lwan/LwanMusic%20(2).png?raw=true",
            "https://github.com/starlightmwamm-droid/Photo/blob/main/Lwan/LwanMusic%20(3).png?raw=true",
            "https://github.com/starlightmwamm-droid/Photo/blob/main/Lwan/LwanMusic%20(4).png?raw=true",
            "https://github.com/starlightmwamm-droid/Photo/blob/main/Lwan/LwanMusic%20(5).png?raw=true",
        ]
        
        # Image rotation counter (ပုံအလှည့်ကျပြဖို့)
        self._image_index = 0

        # ============ MODERATION ============
        # List of usernames to exclude from admin mentions
        self.EXCLUDED_USERNAMES: List[str] = getenv("EXCLUDED_USERNAMES", "").split()

        # ============ PROXY DOWNLOAD METHOD (TELEGRAM CLOUD) ============
        # Enable/disable Telegram Cloud storage for video files
        # When enabled, videos are uploaded to Telegram Cloud and streamed from there
        # This saves Render disk space (free tier only has 500MB)
        # Set to "False" in .env if you want to disable cloud storage
        self.ENABLE_CLOUD_STORAGE: bool = self._str_to_bool(getenv("ENABLE_CLOUD_STORAGE", "True"))

    def _parse_video_height(self) -> int:
        """Parse and validate video height configuration."""
        default_height = 720
        raw_value = getenv("VIDEO_MAX_HEIGHT", str(default_height))
        try:
            height = int(raw_value)
        except (TypeError, ValueError):
            return default_height

        if height <= 0:
            return 0

        return max(480, min(height, 2160))

    def _parse_excluded_chats(self) -> List[int]:
        """
        Parse excluded chat IDs from comma-separated string.

        Returns:
            List[int]: List of chat IDs to exclude from auto-leave.
        """
        excluded = getenv("EXCLUDED_CHATS", "")
        if not excluded:
            return []

        chat_ids = []
        for chat_id in excluded.split(","):
            chat_id = chat_id.strip()
            if chat_id.lstrip('-').isdigit():
                chat_ids.append(int(chat_id))
        return chat_ids

    def _parse_cookies(self) -> List[str]:
        cookie_str = getenv("COOKIE_URL", "")
        if not cookie_str:
            return []
        valid_sources = ["batbin.me", "pastebin.com", "paste.ee", "rentry.co"]
        return [url.strip() for url in cookie_str.split() if url.strip() and any(source in url for source in valid_sources)]

    @staticmethod
    def _str_to_bool(value: str) -> bool:
        return value.lower() in ("true", "1", "yes", "y", "on")

    def check(self) -> None:
        required_vars = {
            "API_ID": self.API_ID,
            "API_HASH": self.API_HASH,
            "BOT_TOKEN": self.BOT_TOKEN,
            "MONGO_DB_URI": self.MONGO_URL,
            "LOGGER_ID": self.LOGGER_ID,
            "OWNER_ID": self.OWNER_ID,
            "STRING_SESSION": self.SESSION1,
        }
        missing = [name for name, value in required_vars.items() if not value or (isinstance(value, int) and value == 0)]
        if missing:
            raise SystemExit(f"Missing required env vars: {', '.join(missing)}")
        
        if self.ENABLE_API and not self.ARTISTBOTS_KEY:
            print("Warning: ENABLE_API is True but ARTISTBOTS_KEY is not set")

    # ============ IMAGE ROTATION METHODS ============
    
    def get_next_image(self) -> str:
        """ပုံတစ်ပုံချင်းစီ အလှည့်ကျပြန်ပေးမယ် (တစ်လှည့်စီ)"""
        image = self.IMAGE_LIST[self._image_index % len(self.IMAGE_LIST)]
        self._image_index += 1
        return image
    
    def get_next_ping_image(self) -> str:
        """Ping command အတွက် အလှည့်ကျပုံ"""
        return self.get_next_image()
    
    def get_next_start_image(self) -> str:
        """Start command အတွက် အလှည့်ကျပုံ"""
        return self.get_next_image()
    
    def get_next_radio_image(self) -> str:
        """Radio command အတွက် အလှည့်ကျပုံ"""
        return self.get_next_image()
    
    def reset_image_rotation(self) -> None:
        """ပုံအလှည့်ကို ပြန်စမယ် (bot restart ချိန်မှာ သုံးလို့ရ)"""
        self._image_index = 0

    @property
    def DEFAULT_THUMB(self) -> str:
        """Default thumbnail - အလှည့်ကျပုံ"""
        return self.get_next_image()

    @property
    def PING_IMG(self) -> str:
        """Ping command အတွက် အလှည့်ကျပုံ"""
        return self.get_next_ping_image()

    @property
    def START_IMG(self) -> str:
        """Start command အတွက် အလှည့်ကျပုံ"""
        return self.get_next_start_image()

    @property
    def RADIO_IMG(self) -> str:
        """Radio command အတွက် အလှည့်ကျပုံ"""
        return self.get_next_radio_image()


# Global config instance
config = Config()
