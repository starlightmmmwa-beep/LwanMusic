# ==============================================================================
# stop.py - Stop Playback Command
# ==============================================================================

import asyncio
import logging
from pyrogram import filters, types
from pyrogram.errors import ChatSendPlainForbidden, ChatWriteForbidden

from Elevenyts import tune, app, db, lang
from Elevenyts.helpers import can_manage_vc

logger = logging.getLogger(__name__)


async def auto_delete_message(msg, delay: int = 5):
    """Auto delete a message after delay seconds"""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


@app.on_message(filters.command(["end", "stop", "cend", "cstop"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _stop(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass
    
    if len(m.command) > 1:
        return
    
    # Check for channel play mode
    is_channel = m.command[0].lower() in ["cend", "cstop"]
    chat_id = m.chat.id
    
    if is_channel:
        channel_id = await db.get_cmode(m.chat.id)
        if channel_id is None:
            msg = await m.reply_text("Channel play is not enabled. Use /channelplay to enable.")
            asyncio.create_task(auto_delete_message(msg, 5))
            return
        chat_id = channel_id
    
    if not await db.get_call(chat_id):
        try:
            msg = await m.reply_text("Nothing is playing.")
            # ✅ Auto-delete after 5 seconds
            asyncio.create_task(auto_delete_message(msg, 5))
            return
        except (ChatSendPlainForbidden, ChatWriteForbidden):
            logger.warning("Cannot send text in this chat, skipping reply.")
            return
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return

    await tune.stop(chat_id)
    try:
        sent_msg = await m.reply_text(f"Stopped by {m.from_user.mention}")
        # Auto-delete stop confirmation after 5 seconds
        asyncio.create_task(auto_delete_message(sent_msg, 5))
    except (ChatSendPlainForbidden, ChatWriteForbidden):
        logger.warning("Cannot send text in this chat, stream stopped silently.")
        return
    except Exception as e:
        logger.error(f"Failed to send stop confirmation: {e}")
        return
