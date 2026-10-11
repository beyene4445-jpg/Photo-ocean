import os
import logging
from io import BytesIO
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont

# --- የ Render አካባቢ ተለዋዋጮች ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8080))

# --- የፎንት ፋይሎች ሙሉ መንገድ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AMHARIC_FONT_PATH = os.path.join(BASE_DIR, "amharic.ttf")
ENGLISH_FONT_PATH = os.path.join(BASE_DIR, "arialbd.ttf") 

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

def add_text_to_image(image_bytes: bytes) -> BytesIO:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    W, H = img.width, img.height
    draw = ImageDraw.Draw(img)

    # --- ጽሑፎች ---
    text_am1 = "ቅድስና"
    text_am2 = "ለእግዚአብሔር"
    text_en  = "HOLINESS TO THE LORD"

    # --- የፎንት መጠን ማስያዝ (እንደ ማጣቀሻ ፎቶው) ---
    # "ቅድስና" በጣም ትልቅ (ከፎቶው ስፋት ~22%)
    # "ለእግዚአብሔር" መካከለኛ (ከፎቶው ስፋት ~9%)
    # "HOLINESS..." ትንሽ (ከፎቶው ስፋት ~3.5%)
    try:
        am1_size = int(W * 0.22)
        am2_size = int(W * 0.09)
        en_size  = int(W * 0.035)

        font_am1 = ImageFont.truetype(AMHARIC_FONT_PATH, am1_size)
        font_am2 = ImageFont.truetype(AMHARIC_FONT_PATH, am2_size)
        font_en  = ImageFont.truetype(ENGLISH_FONT_PATH, en_size)
    except OSError as e:
        logging.error(f"❌ የፎንት ፋይል ማግኘት አልቻለም! ስህተት: {e}")
        # ፎንት ካልተገኘ የሚሠራ የኋላ አማራጭ
        am1_size = int(W * 0.15)
        am2_size = int(W * 0.08)
        en_size  = int(W * 0.04)
        font_am1 = ImageFont.load_default()
        font_am2 = ImageFont.load_default()
        font_en = ImageFont.load_default()

    # --- የጽሑፍ ስፋትና ቁመት ማስላት ---
    bbox_am1 = draw.textbbox((0, 0), text_am1, font=font_am1)
    bbox_am2 = draw.textbbox((0, 0), text_am2, font=font_am2)
    bbox_en  = draw.textbbox((0, 0), text_en, font=font_en)

    h_am1, h_am2, h_en = bbox_am1[3]-bbox_am1[1], bbox_am2[3]-bbox_am2[1], bbox_en[3]-bbox_en[1]
    w_am1, w_am2, w_en = bbox_am1[2]-bbox_am1[0], bbox_am2[2]-bbox_am2[0], bbox_en[2]-bbox_en[0]

    # --- የ Y መጋጠሚያ (ከታች ወደ ላይ ስንሄድ) ---
    # ፎቶው ግርጌ ላይ ትንሽ ክፍተት እንዲኖረው
    margin_bottom = int(H * 0.08)
    spacing = int(H * 0.015) # በጽሑፎች መካከል ያለው ክፍተት

    # 1. የእንግሊዝኛ ጽሑፍ (ከሁሉም በታች)
    en_y = H - margin_bottom - h_en
    
    # 2. "ለእግዚአብሔር" (ከእንግሊዝኛው በላይ)
    am2_y = en_y - spacing - h_am2
    
    # 3. "ቅድስና" (ከሁሉም በላይ)
    am1_y = am2_y - spacing - h_am1

    # --- የ X መጋጠሚያ (በመሃል ለማድረግ) ---
    am1_x = (W - w_am1) // 2
    am2_x = (W - w_am2) // 2
    en_x  = (W - w_en) // 2

    # --- የጥላ (Stroke) ውፍረት ለቦልድነት ---
    # ፎቶው ላይ ጽሑፉ ጎልቶ እንዲታይ የጥላውን ውፍረት ከፎቶው ስፋት አንጻር እናሰላለን
    stroke_w = max(2, int(W * 0.004))

    # --- ጽሑፎቹን መጻፍ ---
    # "ቅድስና" - በወርቅ ቀለም እና በጥቁር ጥላ
    draw.text((am1_x, am1_y), text_am1, font=font_am1, fill=(255, 215, 0), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    # "ለእግዚአብሔር" - በወርቅ ቀለም እና በጥቁር ጥላ
    draw.text((am2_x, am2_y), text_am2, font=font_am2, fill=(255, 215, 0), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    # "HOLINESS TO THE LORD" - በነጭ ቀለም እና በጥቁር ጥላ
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
