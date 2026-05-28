import os
import re
import asyncio
import aiohttp
import base64
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from Elevenyts import config
from Elevenyts.helpers import Track


def decode_text(encoded: str) -> str:
    return base64.b64decode(encoded).decode("utf-8")


def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis


class Thumbnail:
    def __init__(self):
        try:
            self.title_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 40)

            self.regular_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 22)

            self.watermark_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 55)

            self.small_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 18)

        except OSError:
            self.title_font = self.regular_font = self.watermark_font = self.small_font = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_modern.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            return await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync, temp, output, song, size
            )

        except Exception:
            return config.DEFAULT_THUMB

    def _generate_sync(self, temp: str, output: str, song: Track, size=(1280, 720)) -> str:
        try:
            with Image.open(temp) as temp_img:
                base = temp_img.resize(size).convert("RGBA")

            bg = Image.new("RGBA", size, (0, 0, 0, 255))
            bg.paste(base, (0, 0), base)
            bg = bg.filter(ImageFilter.GaussianBlur(2))
            draw = ImageDraw.Draw(bg)

            _a = decode_text("U29lTW9l")      # "SoeMoe"
            _b = decode_text("TXVzaWNCb3Q=")  # "MusicBot"

            colors = [(255, 0, 150), (0, 200, 255), (255, 200, 0)]

            # ========== SoeMoe Logo (ဘယ်ဘက်အပေါ် - ဘောင်မပါ) ==========
            w1 = self.watermark_font.getlength(_a)
            h1 = self.watermark_font.size
            
            # နေရာ
            x1, y1 = 40, 30
                                   
            # ✅ စာသားကို တိုက်ရိုက်ဆွဲမယ် (အရိပ်အနည်းငယ်ထည့်မယ်)
            # အရိပ်အတွက် (Shadow effect)
            for offset_x, offset_y, shadow_color in [(-1, -1, (0,0,0,200)), (1, 1, (0,0,0,200))]:
                cx = x1 + offset_x
                cy = y1 + offset_y
                for i, char in enumerate(_a):
                    draw.text((cx, cy), char, font=self.watermark_font, fill=shadow_color)
                    cx += self.watermark_font.getlength(char)
            
            # အဓိက စာသား
            cx = x1
            for i, char in enumerate(_a):
                draw.text((cx, y1), char, font=self.watermark_font, fill=colors[i % 3])
                cx += self.watermark_font.getlength(char)

            # ========== MusicBot Logo (ညာဘက်အောက် - ဘောင်မပါ) ==========
            w2 = self.watermark_font.getlength(_b)
            h2 = self.watermark_font.size
            
            # နေရာ (ညာဘက်အောက်ထောင့်)
            x2 = 1280 - w2 - 40
            y2 = 720 - h2 - 30
            
            # ❌ ဘောင်မဆွဲတော့ဘူး (ဖျက်ပြီး)
            
            # အရိပ်အတွက် (Shadow effect)
            for offset_x, offset_y, shadow_color in [(-1, -1, (0,0,0,200)), (1, 1, (0,0,0,200))]:
                cx = x2 + offset_x
                cy = y2 + offset_y
                for i, char in enumerate(_b):
                    draw.text((cx, cy), char, font=self.watermark_font, fill=shadow_color)
                    cx += self.watermark_font.getlength(char)
            
            # အဓိက စာသား
            cx = x2
            for i, char in enumerate(_b):
                draw.text((cx, y2), char, font=self.watermark_font, fill=colors[i % 3])
                cx += self.watermark_font.getlength(char)

            # ========== Gradient Overlay ==========
            gradient = Image.new("L", (1, 300))
            for i in range(300):
                gradient.putpixel((0, i), int(255 * (i / 300)))

            alpha = gradient.resize((1280, 300))
            black_overlay = Image.new("RGBA", (1280, 300), (0, 0, 0, 200))
            black_overlay.putalpha(alpha)

            bg.paste(black_overlay, (0, 420), black_overlay)

            # ========== Thumbnail ပုံသေး ==========
            thumb = base.resize((180, 180))
            mask = Image.new("L", thumb.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, 180, 180), 25, fill=255)
            bg.paste(thumb, (60, 450), mask)

            # ========== Song Title ==========
            title = re.sub(r"\W+", " ", song.title).title()

            draw.text(
                (260, 470),
                trim_to_width(title, self.title_font, 800),
                fill="white",
                font=self.title_font
            )

            draw.text(
                (260, 530),
                f"YouTube • {song.view_count or 'Unknown'}",
                fill="lightgray",
                font=self.regular_font
            )

            # ========== Progress Bar ==========
            draw.line([(260, 600), (760, 600)], fill="gray", width=5)
            draw.line([(260, 600), (480, 600)], fill="red", width=6)

            draw.ellipse([(472, 592), (488, 608)], fill="red")

            # ========== Time Text ==========
            draw.text((260, 615), "00:00", fill="white", font=self.small_font)
            draw.text(
                (700, 615),
                getattr(song, 'duration', '00:00'),
                fill="white",
                font=self.small_font
            )

            bg.save(output)

            try:
                os.remove(temp)
            except:
                pass

            return output

        except Exception:
            return config.DEFAULT_THUMB
