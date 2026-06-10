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

            # ========== Another Danger - Demo.otf ==========
            custom_font_path = "Elevenyts/helpers/Another Danger - Demo.otf"
            self.watermark_font = ImageFont.truetype(custom_font_path, 65)
            
            # အကြီးစာလုံးအတွက် နည်းနည်းပိုကြီးတဲ့ font
            self.watermark_font_large = ImageFont.truetype(custom_font_path, 78)  # 65 -> 78 (20% bigger)

            self.small_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 18)

        except OSError as e:
            print(f"Font loading error: {e}")
            self.title_font = self.regular_font = self.watermark_font = self.watermark_font_large = self.small_font = ImageFont.load_default()

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

    def _draw_colored_text_with_variable_size(self, draw, text, x, y, base_font, large_font, color_map, shadow=True):
        """
        စာလုံးတစ်လုံးချင်းဆွဲပါ - အချို့စာလုံးကို ပိုကြီးအောင်ဆွဲပေးမယ်
        color_map: {index: (color, use_large_font)} 
        """
        cx = x
        for i, char in enumerate(text):
            # ဒီစာလုံးအတွက် font နဲ့ color ရွေးမယ်
            if i in color_map:
                color, use_large = color_map[i]
                font = large_font if use_large else base_font
            else:
                color = (255, 255, 255)  # default white
                font = base_font
            
            # Shadow effect
            if shadow:
                for offset_x, offset_y, shadow_color in [(-1, -1, (0,0,0,200)), (1, 1, (0,0,0,200))]:
                    draw.text((cx + offset_x, y + offset_y), char, font=font, fill=shadow_color)
            
            # အဓိကစာသား
            draw.text((cx, y), char, font=font, fill=color)
            
            # နောက်စာလုံးနေရာရွှေ့ဖို့ - သုံးထားတဲ့ font ရဲ့ width အတိုင်း
            cx += font.getlength(char)
        
        return cx  # နောက်ဆုံး x coordinate ပြန်ပေးမယ်

    def _generate_sync(self, temp: str, output: str, song: Track, size=(1280, 720)) -> str:
        try:
            with Image.open(temp) as temp_img:
                base = temp_img.resize(size).convert("RGBA")

            bg = Image.new("RGBA", size, (0, 0, 0, 255))
            bg.paste(base, (0, 0), base)
            bg = bg.filter(ImageFilter.GaussianBlur(2))
            draw = ImageDraw.Draw(bg)

            _a = decode_text("U29lTW9l")      # "SoeMoe" -> အခု "SOE MOE" လိုချင်တယ်
            _b = decode_text("TXVzaWNCb3Q=")  # "MusicBot" -> အခု "MUSIC BOT" လိုချင်တယ်
            
            # ========== "SOE MOE" (space ပါအောင်) ==========
            # မူရင်း "SoeMoe" အစား "SOE MOE" ကို တိုက်ရိုက်သုံးမယ်
            text_a = "SOE MOE"
            # S (index0) နဲ့ M (index4) ကို အနီရောင် + ကြီးအောင်
            # index: 0=S,1=O,2=E,3=(space),4=M,5=O,6=E
            color_map_a = {
                0: ((255, 0, 0), True),    # S - အနီရောင် + ကြီး
                4: ((255, 0, 0), True),    # M - အနီရောင် + ကြီး
                # space ကို ဘာမှမဆွဲဘူး (ဒါပေမယ့် နေရာယူမယ်)
            }
            
            w1 = self.watermark_font.getlength(text_a)  # rough estimate
            x1, y1 = 40, 30
            
            # စာဆွဲမယ် (space ပါတဲ့အတွက် ပုံမှန် draw.text မသုံးဘူး)
            self._draw_colored_text_with_variable_size(
                draw, text_a, x1, y1, 
                self.watermark_font, self.watermark_font_large, 
                color_map_a, shadow=True
            )

            # ========== "MUSIC BOT" (space ပါအောင်) ==========
            text_b = "MUSIC BOT"
            # M (index0) အနီရောင်+ကြီး၊ B (index6) အဝါရောင်+ကြီး
            # index: 0=M,1=U,2=S,3=I,4=C,5=(space),6=B,7=O,8=T
            color_map_b = {
                0: ((255, 0, 0), True),      # M - အနီရောင် + ကြီး
                6: ((255, 255, 0), True),    # B - အဝါရောင် + ကြီး
            }
            
            w2 = self.watermark_font.getlength(text_b)
            x2 = 1280 - w2 - 40
            y2 = 30  # SoeMoe နဲ့အတူတူ
            
            self._draw_colored_text_with_variable_size(
                draw, text_b, x2, y2,
                self.watermark_font, self.watermark_font_large,
                color_map_b, shadow=True
            )

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
