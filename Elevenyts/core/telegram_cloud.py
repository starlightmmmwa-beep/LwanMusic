# Elevenyts/core/telegram_cloud.py
import asyncio
from pyrogram import Client, types
from Elevenyts import userbot, logger, db


class TelegramCloud:
    def __init__(self):
        # Get the first available assistant client
        if userbot.clients:
            self.userbot = userbot.clients[0]  # Primary assistant
        else:
            self.userbot = None
            logger.warning("⚠️ No assistant clients available for cloud storage")

    async def upload_video_to_cloud(self, video_path: str, title: str) -> str:
        """Upload video to Userbot's Saved Messages and return file_id"""
        if not self.userbot:
            logger.error("❌ No userbot available for cloud upload")
            return None
            
        try:
            # Upload to Saved Messages
            sent_msg = await self.userbot.send_video(
                chat_id="me",  # Saved Messages
                video=video_path,
                caption=f"🎬 {title}"
            )
            file_id = sent_msg.video.file_id
            logger.info(f"✅ Video uploaded to Telegram Cloud: {file_id[:20]}...")
            return file_id
        except Exception as e:
            logger.error(f"❌ Failed to upload to Telegram Cloud: {e}")
            return None

    async def stream_from_cloud(self, chat_id: int, file_id: str) -> bool:
        """Stream video directly from Telegram Cloud using file_id"""
        try:
            # Get the assistant client for this chat
            client = await db.get_assistant(chat_id)
            
            if not client:
                logger.error(f"❌ No assistant client for chat {chat_id}")
                return False
            
            # Stream directly from file_id (no download needed!)
            await client.send_video(
                chat_id=chat_id,
                video=file_id,
                supports_streaming=True
            )
            logger.info(f"✅ Streaming from cloud to chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to stream from cloud: {e}")
            return False


cloud_manager = TelegramCloud()
