from pyrogram import filters
from pyrogram import types
from pyrogram.errors import FloodWait, MessageIdInvalid, MessageDeleteForbidden, ChatSendPlainForbidden, ChatWriteForbidden

from Elevenyts import tune, app, config, db, lang, queue, tg, yt
from Elevenyts.helpers import buttons, utils
from Elevenyts.helpers._play import checkUB
import asyncio
import os
import logging

logger = logging.getLogger(__name__)


async def safe_edit(message, text, **kwargs):
    """
    Safely edit a message with proper error handling for common Telegram API errors.
    
    Args:
        message: The message object to edit
        text: New text content
        **kwargs: Additional arguments for edit_text
        
    Returns:
        True if successful, False otherwise
    """
    try:
        await message.edit_text(text, **kwargs)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await message.edit_text(text, **kwargs)
            return True
        except (MessageIdInvalid, MessageDeleteForbidden, Exception):
            return False
    except (MessageIdInvalid, MessageDeleteForbidden):
        # Message was deleted or became invalid - this is expected
        return False
    except Exception:
        # Other errors - log but don't crash
        return False


async def safe_reply(message, text, **kwargs):
    """
    Safely send a reply message with proper error handling for media-only chats.
    
    Args:
        message: The message object to reply to
        text: Text content to send
        **kwargs: Additional arguments for reply_text
        
    Returns:
        The sent message object if successful, None otherwise
    """
    try:
        return await message.reply_text(text, **kwargs)
    except (ChatSendPlainForbidden, ChatWriteForbidden):
        logger.warning(f"Cannot send text in chat {message.chat.id} (chat write forbidden)")
        return None
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")
        return None


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    """
    Add multiple tracks to queue and format them as a message.
    
    Args:
        chat_id: The chat ID where queue is managed
        tracks: List of Track objects to add
        
    Returns:
        Formatted string listing all added tracks
    """
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text

# Global flag to enable/disable cloud storage
ENABLE_CLOUD_STORAGE = getattr(config, 'ENABLE_CLOUD_STORAGE', True)


async def auto_delete_message(msg, delay: int = 20):
    """Auto delete a message after delay seconds"""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
        logger.debug(f"Auto-deleted queue message: {msg.id}")
    except Exception:
        pass


@app.on_message(
    filters.command(
        [
            "play",
            "playforce",
            "cplay",
            "cplayforce",
            "vplay",
            "vplayforce",
            "cvplay",
            "cvplayforce",
        ]
    )
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    url: str = None,
    cplay: bool = False,
    video: bool = False,
) -> None:
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    # Handle channel play mode
    chat_id = m.chat.id
    message_chat_id = m.chat.id
    if cplay:
        channel_id = await db.get_cmode(m.chat.id)
        if channel_id is None:
            return await safe_reply(m,
                "<blockquote>❌ Channel play is not enabled.\n\n"
                "To enable for linked channel:\n"
                "`/channelplay linked`\n\n"
                "To enable for any channel:\n"
                "`/channelplay [channel_id]`</blockquote>"
            )
        try:
            chat = await app.get_chat(channel_id)
            chat_id = channel_id
        except:
            await db.set_cmode(m.chat.id, None)
            return await safe_reply(m,
                "<blockquote>❌ Cannot find channel!\n\n"
                "Please make sure I'm admin in the channel and channel exists.</blockquote>"
            )
        
        client = await db.get_client(channel_id)
        try:
            await app.get_chat_member(channel_id, client.id)
        except Exception:
            try:
                if chat.username:
                    invite_link = chat.username
                else:
                    try:
                        invite_link = chat.invite_link
                        if not invite_link:
                            invite_link = await app.export_chat_invite_link(channel_id)
                    except Exception:
                        return await safe_reply(m,
                            f"<blockquote>❌ Assistant cannot join channel!\n\n"
                            f"Please add @{client.username if client.username else client.mention} "
                            f"to the channel as an admin with permission to join.</blockquote>"
                        )
                
                join_msg = await safe_reply(m,
                    f"<blockquote>🔌 Joining assistant to channel...</blockquote>"
                )
                await client.join_chat(invite_link)
                await asyncio.sleep(1)
                try:
                    await join_msg.delete()
                except:
                    pass
                    
            except Exception as e:
                error_str = str(e)
                return await safe_reply(m,
                    f"<blockquote>❌ Failed to join assistant to channel!\n\n"
                    f"Please manually add @{client.username if client.username else client.mention} "
                    f"to the channel as an admin with permission to join.\n\n"
                    f"Error: {error_str}</blockquote>"
                )

    play_emoji = m.lang["play_emoji"]
    
    try:
        sent = await safe_reply(m, m.lang["play_searching"].format(play_emoji))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            sent = await safe_reply(m, m.lang["play_searching"].format(play_emoji))
        except FloodWait as e2:
            await asyncio.sleep(e2.value)
            return
        except Exception:
            return
    except Exception:
        return
    
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []
    file = None

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif url:
        if "playlist" in url:
            await safe_edit(sent, m.lang["playlist_fetch"])
            try:
                tracks = await yt.playlist(
                    config.PLAYLIST_LIMIT, mention, url
                )
            except Exception as e:
                await safe_edit(
                    sent,
                    f"<blockquote>❌ Failed to fetch playlist.\n\n"
                    f"YouTube playlists are currently experiencing issues. "
                    f"Please try a single track instead.</blockquote>"
                )
                return

            if not tracks:
                await safe_edit(sent, m.lang["playlist_error"])
                return

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id)

        if not file:
            await safe_edit(
                sent,
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )
            return

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id)
        if not file:
            await safe_edit(
                sent,
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )
            return

    if not file:
        return

    file.video = getattr(file, "video", False) or video
    if file.video:
        for track in tracks:
            track.video = True

    if not file.is_live and file.duration_sec > config.DURATION_LIMIT:
        await safe_edit(
            sent,
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )
        return

    if await db.is_logger():
        await utils.play_log(m, file.title, file.duration)

    file.user = mention
    if force:
        queue.force_add(chat_id, file)
    else:
        position = queue.add(chat_id, file)

        if await db.get_call(chat_id):
            await safe_edit(
                sent,
                m.lang["play_queued"].format(
                    position,
                    file.url,
                    file.title,
                    file.duration,
                    m.from_user.mention,
                ),
                reply_markup=buttons.play_queued(
                    chat_id, file.id, m.lang["play_now"]
                ),
            )
            
            # ✅ Auto-delete queue message after 20 seconds
            asyncio.create_task(auto_delete_message(sent, 20))
            
            if tracks:
                added = playlist_to_queue(chat_id, tracks)
                try:
                    await app.send_message(
                        chat_id=m.chat.id,
                        text=m.lang["playlist_queued"].format(len(tracks)) + added,
                    )
                except Exception:
                    pass
            
            try:
                from Elevenyts import preload
                asyncio.create_task(preload.start_preload(chat_id, count=2))
            except Exception:
                pass
            
            return

    if not file.file_path:
        file.file_path = await yt.download(
            file.id,
            is_live=file.is_live,
            video=getattr(file, "video", False),
        )
        if not file.file_path:
            await safe_edit(
                sent,
                "<blockquote>❌ Failed to download media.\n\n"
                "Possible reasons:\n"
                "• YouTube detected bot activity (update cookies)\n"
                "• Video is region-blocked or private\n"
                "• Age-restricted content (requires cookies)</blockquote>"
            )
            return

    # ========== PROXY DOWNLOAD METHOD (TELEGRAM CLOUD STORAGE) ==========
    if ENABLE_CLOUD_STORAGE and video and file.file_path and os.path.exists(file.file_path):
        try:
            from Elevenyts.core.telegram_cloud import cloud_manager
            
            file_size_mb = os.path.getsize(file.file_path) / (1024 * 1024)
            logger.info(f"☁️ Processing {file_size_mb:.1f}MB video (360p conversion + cloud upload)...")
            
            await safe_edit(sent, "🔄 Processing video (convert to 360p & upload to cloud)...")
            
            # ✅ NEW: Use process_video() which does convert + upload + stream
            success = await cloud_manager.process_video(file.file_path, file.title, chat_id)
            
            if success:
                try:
                    await sent.delete()
                except Exception:
                    pass
                
                # Send now playing message with controls
                text = m.lang["play_media"].format(
                    file.url,
                    file.title,
                    file.duration,
                    m.from_user.mention,
                )
                keyboard = buttons.controls(chat_id)
                
                _thumb = config.DEFAULT_THUMB
                if config.THUMB_GEN and isinstance(file, Track) and hasattr(file, 'thumbnail') and file.thumbnail:
                    try:
                        from Elevenyts.helpers import thumb
                        _thumb = await thumb.generate(file)
                    except Exception:
                        pass
                
                await app.send_photo(
                    chat_id=chat_id,
                    photo=_thumb,
                    caption=text,
                    reply_markup=keyboard,
                )
                return
            else:
                logger.warning("Cloud processing failed, falling back to local playback")
                await safe_edit(sent, "⚠️ Cloud processing failed, trying local playback...")
                
        except ImportError:
            logger.debug("telegram_cloud.py not found, using local playback only")
        except Exception as e:
            logger.error(f"Cloud storage error: {e}, falling back to local playback")
            await safe_edit(sent, "⚠️ Cloud error, using local playback...")
    # ========== END PROXY DOWNLOAD METHOD ==========

    try:
        await tune.play_media(
            chat_id=chat_id, 
            message=sent, 
            media=file, 
            message_chat_id=message_chat_id if chat_id != message_chat_id else None
        )
        try:
            emoji = m.lang["play_emoji"]
            await m.react(emoji)
        except Exception:
            pass
    except Exception as e:
        error_msg = str(e)
        if "bot" in error_msg.lower() or "sign in" in error_msg.lower():
            await safe_edit(
                sent,
                "<blockquote>❌ YouTube bot detection triggered.\n\n"
                "Solution:\n"
                "• Update YouTube cookies in `Elevenyts/cookies/` folder\n"
                "• Wait a few minutes before trying again\n"
                "• Try /radio for uninterrupted music\n\n"
                f"Support: {config.SUPPORT_CHAT}</blockquote>"
            )
        else:
            await safe_edit(
                sent,
                f"<blockquote>❌ Playback error:\n{error_msg}\n\n"
                f"Support: {config.SUPPORT_CHAT}</blockquote>"
            )
        return
    if not tracks:
        return
    added = playlist_to_queue(chat_id, tracks)
    try:
        await app.send_message(
            chat_id=m.chat.id,
            text=m.lang["playlist_queued"].format(len(tracks)) + added,
        )
    except Exception:
        pass
