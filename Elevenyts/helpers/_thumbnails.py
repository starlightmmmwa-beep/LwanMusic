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

            # ========== Awesome.ttf ==========
            awesome_font_path = "Elevenyts/helpers/Awesome.ttf"
            self.main_font = ImageFont.truetype(awesome_font_path, 50)
            self.symbol_font = ImageFont.truetype(awesome_font_path, 50)

            self.small_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 18)

        except OSError as e:
            print(f"Font loading error: {e}")
            self.title_font = self.regular_font = self.main_font = self.symbol_font = self.small_font = ImageFont.load_default()

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

            # ========== "Soe Moe" +  (U+F04F) ==========
            # သင်္ကေတကို လဲလှယ်လိုက်ပြီ (အရင်က  ကနေ  ကိုပြောင်း)
            symbol1 = "\uf04f"  #  (ဒီသင်္ကေတကို Soe Moe နောက်မှာ)
            
            # အကုန်လုံးကို အပေါ်နည်းနည်းတိုးမယ် (y ကို 30 ကနေ 20 ကိုပြောင်း)
            x1, y1 = 40, 20  # 50 ကနေ 20 ကို ပြောင်း (အပေါ်ကို 30 တိုး)
            
            cx = x1
            text = "Soe Moe"
            for i, char in enumerate(text):
                if char in ['S', 'M']:
                    color = (255, 0, 0)
                else:
                    color = (255, 255, 255)
                
                for ox, oy, sc in [(-1,-1,(0,0,0,200)), (1,1,(0,0,0,200))]:
                    draw.text((cx+ox, y1+oy), char, font=self.main_font, fill=sc)
                draw.text((cx, y1), char, font=self.main_font, fill=color)
                cx += self.main_font.getlength(char)
            
            # သင်္ကေတ
            sym_x = cx
            sym_y = y1
            for ox, oy, sc in [(-1,-1,(0,0,0,200)), (1,1,(0,0,0,200))]:
                draw.text((sym_x+ox, sym_y+oy), symbol1, font=self.symbol_font, fill=sc)
            draw.text((sym_x, sym_y), symbol1, font=self.symbol_font, fill=(0, 0, 0)) 

            # ========== "Music Bot" +  (U+F051) ==========
            # သင်္ကေတကို လဲလှယ်လိုက်ပြီ (အရင်က  ကနေ  ကိုပြောင်း)
            symbol2 = "\uf051"  #  (ဒီသင်္ကေတကို Music Bot နောက်မှာ)
            
            text2 = "Music Bot"
            w2 = self.main_font.getlength(text2)
            x2 = 1280 - w2 - 40
            y2 = 20  # 50 ကနေ 20 ကို ပြောင်း (အပေါ်ကို 30 တိုး)
            
            cx = x2
            for i, char in enumerate(text2):
                if char == 'M':
                    color = (255, 0, 0)
                elif char == 'B':
                    color = (255, 255, 0)
                else:
                    color = (255, 255, 255)
                
                for ox, oy, sc in [(-1,-1,(0,0,0,200)), (1,1,(0,0,0,200))]:
                    draw.text((cx+ox, y2+oy), char, font=self.main_font, fill=sc)
                draw.text((cx, y2), char, font=self.main_font, fill=color)
                cx += self.main_font.getlength(char)
            
            # သင်္ကေတ 
            sym2_x = cx
            sym2_y = y2
            for ox, oy, sc in [(-1,-1,(0,0,0,200)), (1,1,(0,0,0,200))]:
                draw.text((sym2_x+ox, sym2_y+oy), symbol2, font=self.symbol_font, fill=sc)
            draw.text((sym2_x, sym2_y), symbol2, font=self.symbol_font, fill=(0, 0, 0))  

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
