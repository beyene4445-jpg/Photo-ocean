import os
import logging
from io import BytesIO
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BOT_TOKEN = os.environ.get("BOT_TOKEN")   # ከ Render Environment Variable
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") # ከ Render Environment Variable
PORT = int(os.environ.get("PORT", 8080))

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

def add_text_to_image(image_bytes: bytes) -> BytesIO:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(img.height):
        alpha = int(180 * (y / img.height) ** 2)
        odraw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    am_size = int(img.width * 0.075)
    en_size = int(img.width * 0.045)

    try:
        am_font = ImageFont.truetype("NotoSansEthiopic-Bold.ttf", am_size)
        en_font = ImageFont.truetype("arialbd.ttf", en_size)
    except OSError:
        am_font = ImageFont.load_default()
        en_font = ImageFont.load_default()

    am_text = "ቅድስና ለእግዚአብሔር"
    en_text = "HOLINESS TO THE LORD"

    am_bbox = draw.textbbox((0, 0), am_text, font=am_font)
    en_bbox = draw.textbbox((0, 0), en_text, font=en_font)

    am_w = am_bbox[2] - am_bbox[0]
    en_w = en_bbox[2] - en_bbox[0]

    margin_bottom = int(img.height * 0.08)
    en_y = img.height - margin_bottom - (en_bbox[3] - en_bbox[1])
    am_y = en_y - (am_bbox[3] - am_bbox[1]) - int(img.height * 0.03)

    am_x = (img.width - am_w) // 2
    en_x = (img.width - en_w) // 2

    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.text((am_x, am_y), am_text, font=am_font, fill=(255, 215, 0, 180))
    gdraw.text((en_x, en_y), en_text, font=en_font, fill=(255, 215, 0, 180))
    glow = glow.filter(ImageFilter.GaussianBlur(12))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    draw.text((am_x, am_y), am_text, font=am_font, fill=(255, 215, 0))
    draw.text((en_x, en_y), en_text, font=en_font, fill=(255, 255, 255))

    line_y = am_y + (am_bbox[3] - am_bbox[1]) // 2
    pad = int(img.width * 0.03)
    draw.line([(am_x - pad - 60, line_y), (am_x - pad, line_y)],
              fill=(255, 215, 0), width=3)
    draw.line([(am_x + am_w + pad, line_y), (am_x + am_w + pad + 60, line_y)],
              fill=(255, 215, 0), width=3)

    out = BytesIO()
    out.name = "blessed.jpg"
    img.save(out, "JPEG", quality=95)
    out.seek(0)
    return out


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    photo = msg.photo[-1]
    file = await photo.get_file()
    data = await file.download_as_bytearray()

    await msg.reply_text("⏳ በማስከፈት ላይ...")

    try:
        result = add_text_to_image(bytes(data))
        await msg.reply_photo(photo=result, caption="🙏 ቅድስና ለእግዚአብሔር")
    except Exception as e:
        logging.exception(e)
        await msg.reply_text("❌ ስህተት ተፈጠረ። እባክህ እንደገና ሞክር።")


async def healthcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Render ላይ ለ health check"""
    return "OK"


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Webhook ማስጀመር
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
