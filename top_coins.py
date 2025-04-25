import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# تنظیم لاگینگ
logger = logging.getLogger(__name__)

# URL API کوین‌گکو
COINGECKO_API = "https://api.coingecko.com/api/v3"

# دیکشنری ایموجی‌های مینیمال برای 10 ارز برتر (بر اساس نماد)
COIN_EMOJIS = {
    "bitcoin": "🪙",  # بیت‌کوین
    "ethereum": "⧫",  # اتریوم
    "tether": "₮",    # تتر
    "binancecoin": "🔶",  # بایننس‌کوین
    "solana": "🌞",   # سولانا
    "ripple": "💧",   # ریپل (XRP)
    "usd-coin": "💵", # USDC
    "cardano": "🌱",  # کاردانو
    "avalanche-2": "❄️",  # آوالانچ
    "dogecoin": "🐶", # دوج‌کوین
}

def get_top_coins_panel() -> tuple[str, InlineKeyboardMarkup]:
    try:
        response = requests.get(
            f"{COINGECKO_API}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
        )
        response.raise_for_status()
        data = response.json()

        # پیام کوتاه
        message = "📊 10 ارز برتر:"
        
        # ساخت دکمه‌های پنل عمودی
        keyboard = []
        for coin in data:
            symbol = coin["symbol"].upper()
            price = coin["current_price"]
            coin_id = coin["id"].lower()  # برای تطبیق با دیکشنری ایموجی
            
            # انتخاب ایموجی مینیمال (اگه نبود، ایموجی پیش‌فرض)
            emoji = COIN_EMOJIS.get(coin_id, "💸")
            
            # ساخت متن دکمه با لوگو، نماد و قیمت
            button_text = f"{emoji} {symbol}: ${price:,.2f}"
            button = InlineKeyboardButton(
                text=button_text,
                callback_data=f"coin_{coin_id}"  # برای تعاملات بعدی
            )
            keyboard.append([button])  # هر دکمه تو یه سطر جدا

        reply_markup = InlineKeyboardMarkup(keyboard)
        return message, reply_markup

    except Exception as e:
        logger.error(f"خطا در دریافت 10 ارز برتر: {e}")
        return "خطایی رخ داد. دوباره امتحان کنید.", None