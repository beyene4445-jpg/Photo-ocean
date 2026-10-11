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

# --- የፎንት ፋይሎች ሙሉ መንገድ (Absolute Path) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AMHARIC_FONT_PATH = os.path.join(BASE_DIR, "NotoSansEthiopic-Bold.ttf")
ENGLISH_FONT_PATH = os.path.join(BASE_DIR, "arialbd.ttf") 

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

def add_text_to_image(image_bytes: bytes) -> BytesIO:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")

    # --- ጨለማ ዳራ (Gradient Overlay) ለጽሑፍ ግልጽነት ---
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(img.height):
        alpha = int(200 * (y / img.height) ** 2) # ጨለማውን ትንሽ ጨመርኩት
        odraw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # --- የፎንት መጠን ማስያዝ (እንደ ተጠቃሚው ጥያቄ) ---
    # 50% ማለት ከፎቶው ስፋት 50% ማለት ነው።
    am1_size = int(img.width * 0.50) 
    am2_size = int(img.width * 0.40) 
    en_size  = int(img.width * 0.35) 

    # --- ፎንቶችን መጫን ---
    try:
        font_am1 = ImageFont.truetype(AMHARIC_FONT_PATH, am1_size)
        font_am2 = ImageFont.truetype(AMHARIC_FONT_PATH, am2_size)
        font_en  = ImageFont.truetype(ENGLISH_FONT_PATH, en_size)
    except OSError as e:
        logging.error(f"❌ የፎንት ፋይል ማግኘት አልቻለም! ስህተት: {e}")
        font_am1 = ImageFont.load_default()
        font_am2 = ImageFont.load_default()
        font_en = ImageFont.load_default()

    # --- ጽሑፎች ---
    text_am1 = "ቅድስና"
    text_am2 = "ለእግዚአብሔር"
    text_en  = "HOLINESS TO THE LORD"

    # --- የጽሑፍ ስፋትና ቁመት ማስላት ---
    bbox_am1 = draw.textbbox((0, 0), text_am1, font=font_am1)
    bbox_am2 = draw.textbbox((0, 0), text_am2, font=font_am2)
    bbox_en  = draw.textbbox((0, 0), text_en, font=font_en)

    h_am1 = bbox_am1[3] - bbox_am1[1]
    h_am2 = bbox_am2[3] - bbox_am2[1]
    h_en  = bbox_en[3] - bbox_en[1]

    w_am1 = bbox_am1[2] - bbox_am1[0]
    w_am2 = bbox_am2[2] - bbox_am2[0]
    w_en  = bbox_en[2] - bbox_en[0]

    # --- የ Y መጋጠሚያ (ከታች ወደ ላይ ስንሄድ) ---
    margin_bottom = int(img.height * 0.05) 
    spacing = int(img.height * 0.02) # በጽሑፎች መካከል ያለው ክፍተት

    # 1. የእንግሊዝኛ ጽሑፍ (ከሁሉም በታች)
    en_y = img.height - margin_bottom - h_en
    
    # 2. "ለእግዚአብሔር" (ከእንግሊዝኛው በላይ)
    am2_y = en_y - spacing - h_am2
    
    # 3. "ቅድስና" (ከሁሉም በላይ)
    am1_y = am2_y - spacing - h_am1

    # --- የ X መጋጠሚያ (በመሃል ለማድረግ) ---
    am1_x = (img.width - w_am1) // 2
    am2_x = (img.width - w_am2) // 2
    en_x  = (img.width - w_en) // 2

    # --- የወርቅ ብርሃን ውጤት (Glow Effect) ---
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.text((am1_x, am1_y), text_am1, font=font_am1, fill=(255, 215, 0, 200))
    gdraw.text((am2_x, am2_y), text_am2, font=font_am2, fill=(255, 215, 0, 180))
    gdraw.text((en_x, en_y), text_en, font=font_en, fill=(255, 215, 0, 150))
    
    glow = glow.filter(ImageFilter.GaussianBlur(int(img.width * 0.02)))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # --- "በጣም ቦልድ" ለማድረግ የጥላ (Stroke) መጠን ---
    stroke_w = max(2, int(img.width * 0.005)) # የጥላው ውፍረት

    # --- ጽሑፎቹን መጻፍ (ከጥላ ጋር) ---
    # ወርቅ ቀለም ያላቸው ጽሑፎች ጥቁር ጥላ እንዲኖራቸው
    draw.text((am1_x, am1_y), text_am1, font=font_am1, fill=(255, 215, 0), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    draw.text((am2_x, am2_y), text_am2, font=font_am2, fill=(255, 215, 0), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    # ነጭ ቀለም ያለው ጽሑፍ ደግሞ ጥቁር ጥላ እንዲኖረው
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
