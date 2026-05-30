# Elevenyts/core/telegram_cloud.py
import os
import subprocess
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

    async def convert_to_360p(self, input_path: str) -> str:
        """Convert video to 360p MP4 format"""
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_360p.mp4"
        
        # FFmpeg command for 360p conversion
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", "scale=640:360",
            "-b:v", "500k",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "64k",
            "-preset", "fast",
            "-y", output_path
        ]
        
        try:
            logger.info(f"🔄 Converting video to 360p: {input_path}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.PIPE,
                stderr=asyncio.PIPE
            )
            await process.communicate()
            
            if os.path.exists(output_path):
                logger.info(f"✅ Converted to 360p: {output_path}")
                return output_path
            else:
                logger.error("❌ Conversion failed - output file not found")
                return input_path
                
        except Exception as e:
            logger.error(f"❌ Conversion error: {e}")
            return input_path

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
                caption=f"🎬 {title} (360p)"
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

    async def process_video(self, video_path: str, title: str, chat_id: int) -> bool:
        """
        Complete video processing pipeline:
        1. Convert to 360p
        2. Upload to Saved Messages
        3. Delete local files
        4. Stream from cloud
        
        Returns True if successful
        """
        try:
            # Step 1: Convert to 360p
            logger.info(f"🎬 Processing video: {title}")
            converted_path = await self.convert_to_360p(video_path)
            
            # Step 2: Upload to Saved Messages
            file_id = await self.upload_video_to_cloud(converted_path, title)
            
            if not file_id:
                logger.error("Failed to upload to cloud")
                return False
            
            # Step 3: Delete local files to free disk space
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                    logger.info(f"🗑️ Deleted original: {video_path}")
                if converted_path != video_path and os.path.exists(converted_path):
                    os.remove(converted_path)
                    logger.info(f"🗑️ Deleted converted: {converted_path}")
            except Exception as e:
                logger.warning(f"Could not delete local files: {e}")
            
            # Step 4: Stream from cloud
            success = await self.stream_from_cloud(chat_id, file_id)
            
            if success:
                logger.info(f"✅ Successfully streamed {title} from cloud")
                return True
            else:
                logger.error("Failed to stream from cloud")
                return False
                
        except Exception as e:
            logger.error(f"❌ Video processing failed: {e}")
            return False


cloud_manager = TelegramCloud()
