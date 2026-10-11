import os
import logging
from io import BytesIO
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- የ Render አካባቢ ተለዋዋጮች ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8080))

# --- የፎንት ፋይሎች ሙሉ መንገድ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# አሁን ፎንቱ በGitHub ላይ 'amharic.ttf' ተብሎ ስለሚቀየር በቀጥታ እንጠራዋለን
AMHARIC_FONT_PATH = os.path.join(BASE_DIR, "amharic.ttf")
ENGLISH_FONT_PATH = os.path.join(BASE_DIR, "arialbd.ttf") 

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- ጽሑፉ ከፎቶው እንዳይወጣ በራሱ መጠን የሚያስተካክል ተግባር ---
def get_fitted_font(font_path, text, max_width, max_height, start_size):
    size = start_size
    while size > 10:
        try:
            font = ImageFont.truetype(font_path, size)
            bbox = font.getbbox(text)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            # ጽሑፉ ከፎቶው ስፋትና ቁመት ካልወጣ ወዲያውኑ እንውጣ
            if w <= max_width and h <= max_height:
                return font
            size -= 2
        except Exception:
            break
    return ImageFont.load_default()

def add_text_to_image(image_bytes: bytes) -> BytesIO:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    W, H = img.width, img.height

    # --- ጨለማ ዳራ (Gradient Overlay) ለጽሑፍ ግልጽነት ---
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(H):
        alpha = int(200 * (y / H) ** 2)
        odraw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # --- ጽሑፎች ---
    text_am1 = "ቅድስና"
    text_am2 = "ለእግዚአብሔር"
    text_en  = "HOLINESS TO THE LORD"

    # --- የፎንት መጠን ማስያዝ (እንደ ተጠቃሚው ጥያቄ 50%, 40%, 35% ተብሎ ተጽፎ በራሱ ይቀንሳል) ---
    # ከፎቶው ስፋት 90% ብቻ እንዲይዝ ገደብ አስቀምጠናል
    max_text_width = int(W * 0.90)
    
    # ቁመታቸውን ገድበን ፎንቶቹን እናገኛለን
    font_am1 = get_fitted_font(AMHARIC_FONT_PATH, text_am1, max_text_width, int(H * 0.25), int(W * 0.50))
    font_am2 = get_fitted_font(AMHARIC_FONT_PATH, text_am2, max_text_width, int(H * 0.15), int(W * 0.40))
    font_en  = get_fitted_font(ENGLISH_FONT_PATH, text_en,  max_text_width, int(H * 0.10), int(W * 0.35))

    # --- የጽሑፍ ስፋትና ቁመት ማስላት ---
    bbox_am1 = draw.textbbox((0, 0), text_am1, font=font_am1)
    bbox_am2 = draw.textbbox((0, 0), text_am2, font=font_am2)
    bbox_en  = draw.textbbox((0, 0), text_en, font=font_en)

    h_am1, h_am2, h_en = bbox_am1[3]-bbox_am1[1], bbox_am2[3]-bbox_am2[1], bbox_en[3]-bbox_en[1]
    w_am1, w_am2, w_en = bbox_am1[2]-bbox_am1[0], bbox_am2[2]-bbox_am2[0], bbox_en[2]-bbox_en[0]

    # --- የ Y መጋጠሚያ (ከታች ወደ ላይ) ---
    margin_bottom = int(H * 0.08)
    spacing = int(H * 0.02)

    en_y = H - margin_bottom - h_en
    am2_y = en_y - spacing - h_am2
    am1_y = am2_y - spacing - h_am1

    # --- የ X መጋጠሚያ (በመሃል) ---
    am1_x = (W - w_am1) // 2
    am2_x = (W - w_am2) // 2
    en_x  = (W - w_en) // 2

    # --- "በጣም ቦልድ" ለማድረግ የጥላ (Stroke) ውፍረት ---
    stroke_w = max(2, int(W * 0.01)) 

    # --- ጽሑፎቹን መጻፍ (ከጥቁር ጥላ ጋር - ይህ በጣም ቦልድ ያደርገዋል) ---
    draw.text((am1_x, am1_y), text_am1, font=font_am1, fill=(255, 215, 0), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    draw.text((am2_x, am2_y), text_am2, font=font_am2, fill=(255, 215, 0), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    draw.text((en_x, en_y), text_en, font=font_en, fill=(255, 255, 255), stroke_width=stroke_w, stroke_fill=(0, 0, 0))

    # --- ውጤቱን ማስቀመጥ ---
    out = BytesIO()
    out.name = "blessed.jpg"
    img.save(out, "JPEG", quality=95)
    out.seek(0)
    return out

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ሰላም! 👋 እንኳን ደህና መጣህ።\n\n"
        "እባክህ ፎቶ ላክልኝ፣ በ'ቅድስና ለእግዚአብሔር' ጽሑፍ አሸብርቄ እመልስልሃለሁ። 📸✨"
    )

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

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot ተጀምሯል...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
