import logging
import requests
from telegram.ext import ContextTypes
from telegram import Update

# تنظیم لاگینگ
logger = logging.getLogger(__name__)

# URL API کوین‌گکو
COINGECKO_API = "https://api.coingecko.com/api/v3"

# دیکشنری نگاشت نمادهای اختصاری به شناسه‌های کامل
SYMBOL_TO_ID = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "usdt": "tether",
    "bnb": "binancecoin",
    "sol": "solana",
    "xrp": "ripple",
    "usdc": "usd-coin",
    "ada": "cardano",
    "avax": "avalanche-2",
    "doge": "dogecoin",
}

async def get_coin_info(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> None:
    """
    دریافت و نمایش اطلاعات ارز با نماد یا شناسه داده‌شده (case-insensitive).
    ورودی: نماد ارز (مثل btc یا BTC) یا شناسه (مثل bitcoin)
    """
    logger.debug(f"ورودی نماد: {symbol}")
    if not symbol:
        logger.debug("هیچ نمادی وارد نشده")
        await update.message.reply_text(
            "لطفاً نماد ارز را وارد کنید. مثال: /info btc، /info eth"
        )
        return

    # تبدیل نماد به حروف کوچک برای سازگاری
    symbol = symbol.lower()
    logger.debug(f"درخواست اطلاعات برای ارز: {symbol} توسط کاربر {update.effective_user.id}")

    # تبدیل نماد اختصاری به شناسه کامل (اگه لازم باشه)
    coin_id = SYMBOL_TO_ID.get(symbol, symbol)
    logger.debug(f"شناسه ارز برای API: {coin_id}")

    try:
        # درخواست به API کوین‌گکو برای اطلاعات ارز
        response = requests.get(
            f"{COINGECKO_API}/coins/markets?vs_currency=usd&ids={coin_id}&per_page=1&page=1"
        )
        response.raise_for_status()
        data = response.json()
        logger.debug(f"پاسخ API برای {coin_id}: {data}")

        if not data:
            logger.debug(f"ارز یافت نشد: {coin_id}")
            await update.message.reply_text(
                "ارز یافت نشد! نماد را بررسی کنید. مثال: btc، eth، bitcoin"
            )
            return

        # استخراج اطلاعات
        coin = data[0]
        name = coin["name"]
        symbol = coin["symbol"].upper()
        price = coin["current_price"]
        change_24h = coin["price_change_percentage_24h"]
        volume_24h = coin["total_volume"]
        market_cap = coin["market_cap"]

        # ساخت پیام
        message = (
            f"📊 اطلاعات {name} ({symbol}):\n"
            f"💵 قیمت: ${price:,.2f}\n"
            f"📈 تغییر 24 ساعته: {change_24h:.2f}%\n"
            f"📉 حجم معاملات 24 ساعته: ${volume_24h:,.0f}\n"
            f"🏦 ارزش بازار: ${market_cap:,.0f}"
        )
        await update.message.reply_text(message)

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"خطای HTTP در دریافت اطلاعات ارز {coin_id}: {http_err}")
        await update.message.reply_text("خطای سرور API. دوباره امتحان کنید.")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"خطای شبکه در دریافت اطلاعات ارز {coin_id}: {req_err}")
        await update.message.reply_text("خطای شبکه. اینترنت خود را بررسی کنید.")
    except Exception as e:
        logger.error(f"خطای عمومی در دریافت اطلاعات ارز {coin_id}: {e}")
        await update.message.reply_text("خطایی رخ داد. دوباره امتحان کنید.")