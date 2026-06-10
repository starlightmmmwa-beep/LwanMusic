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

            # ========== Awesome.ttf ဖောင့်ကိုသုံးမယ် ==========
            awesome_font_path = "Elevenyts/helpers/Awesome.ttf"
            self.watermark_font = ImageFont.truetype(awesome_font_path, 65)
            
            # သေးငယ်တဲ့ ™ နဲ့ ® အတွက် သေးငယ်တဲ့ font
            self.symbol_font = ImageFont.truetype(awesome_font_path, 35)

            self.small_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 18)

        except OSError as e:
            print(f"Font loading error: {e}")
            self.title_font = self.regular_font = self.watermark_font = self.symbol_font = self.small_font = ImageFont.load_default()

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

    def _draw_word_with_color(self, draw, word, x, y, font, color_map, start_index=0):
        """
        စကားလုံးတစ်လုံးဆွဲပေးမယ် (စာလုံးကြား space မပါ)
        color_map: {relative_index: color}
        """
        cx = x
        for i, char in enumerate(word):
            color = color_map.get(start_index + i, (255, 255, 255))
            
            # Shadow effect
            for offset_x, offset_y, shadow_color in [(-1, -1, (0,0,0,200)), (1, 1, (0,0,0,200))]:
                draw.text((cx + offset_x, y + offset_y), char, font=font, fill=shadow_color)
            
            draw.text((cx, y), char, font=font, fill=color)
            cx += font.getlength(char)
        
        return cx

    def _generate_sync(self, temp: str, output: str, song: Track, size=(1280, 720)) -> str:
        try:
            with Image.open(temp) as temp_img:
                base = temp_img.resize(size).convert("RGBA")

            bg = Image.new("RGBA", size, (0, 0, 0, 255))
            bg.paste(base, (0, 0), base)
            bg = bg.filter(ImageFilter.GaussianBlur(2))
            draw = ImageDraw.Draw(bg)

            # ========== "Soe Moe" (Soe တစ်စု၊ နောက် space၊ Moe တစ်စု) ==========
            word1 = "Soe"
            word2 = "Moe"
            
            # Soe ထဲက S ကို နက်ပြာ (index 0)
            # Moe ထဲက M ကို နက်ပြာ (index 0 relative to word2)
            x1, y1 = 40, 30
            
            # "Soe" ဆွဲမယ်
            cx = self._draw_word_with_color(draw, word1, x1, y1, self.watermark_font, {0: (0, 0, 255)})
            
            # Space ထည့်မယ် (စကားလုံးကြား)
            space_width = self.watermark_font.getlength(" ")
            cx += space_width
            
            # "Moe" ဆွဲမယ် (M ကို နက်ပြာ)
            cx = self._draw_word_with_color(draw, word2, cx, y1, self.watermark_font, {0: (0, 0, 255)})
            
            # ™ သင်္ကေတ (Moe နောက်မှာ)
            tm_x = cx
            tm_y = y1 - 5
            for offset_x, offset_y, shadow_color in [(-1, -1, (0,0,0,200)), (1, 1, (0,0,0,200))]:
                draw.text((tm_x + offset_x, tm_y + offset_y), "™", font=self.symbol_font, fill=shadow_color)
            draw.text((tm_x, tm_y), "™", font=self.symbol_font, fill=(255, 215, 0))

            # ========== "Music Bot" (Music တစ်စု၊ နောက် space၊ Bot တစ်စု) ==========
            word3 = "Music"
            word4 = "Bot"
            
            # Music ထဲက M ကို အနီရောင် (index 0)
            # Bot ထဲက B ကို အဝါရောင် (index 0 relative to word4)
            
            w3 = self.watermark_font.getlength(word3)
            w4 = self.watermark_font.getlength(word4)
            space_w = self.watermark_font.getlength(" ")
            total_w = w3 + space_w + w4
            
            x2 = 1280 - total_w - 40
            y2 = 30
            
            # "Music" ဆွဲမယ် (M အနီ)
            cx = self._draw_word_with_color(draw, word3, x2, y2, self.watermark_font, {0: (255, 0, 0)})
            
            # Space
            cx += space_width
            
            # "Bot" ဆွဲမယ် (B အဝါ)
            cx = self._draw_word_with_color(draw, word4, cx, y2, self.watermark_font, {0: (255, 255, 0)})
            
            # ® သင်္ကေတ (Bot နောက်မှာ)
            reg_x = cx
            reg_y = y2 - 5
            for offset_x, offset_y, shadow_color in [(-1, -1, (0,0,0,200)), (1, 1, (0,0,0,200))]:
                draw.text((reg_x + offset_x, reg_y + offset_y), "®", font=self.symbol_font, fill=shadow_color)
            draw.text((reg_x, reg_y), "®", font=self.symbol_font, fill=(255, 215, 0))

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

        except Exception as e:
            print(f"Thumbnail generation error: {e}")
            return config.DEFAULT_THUMB
