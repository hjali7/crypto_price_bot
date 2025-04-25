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

async def get_coin_price(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> None:
    """
    دریافت و نمایش قیمت ارز با نماد یا شناسه داده‌شده (case-insensitive).
    ورودی: نماد ارز (مثل btc یا BTC) یا شناسه (مثل bitcoin)
    """
    logger.debug(f"ورودی نماد: {symbol}")
    if not symbol:
        logger.debug("هیچ نمادی وارد نشده")
        await update.message.reply_text(
            "لطفاً نماد ارز را وارد کنید. مثال: btc، eth، bitcoin"
        )
        return

    # تبدیل نماد به حروف کوچک برای سازگاری
    symbol = symbol.lower()
    logger.debug(f"درخواست قیمت برای ارز: {symbol} توسط کاربر {update.effective_user.id}")

    # تبدیل نماد اختصاری به شناسه کامل (اگه لازم باشه)
    coin_id = SYMBOL_TO_ID.get(symbol, symbol)
    logger.debug(f"شناسه ارز برای API: {coin_id}")

    try:
        # درخواست به API کوین‌گکو برای قیمت ارز
        response = requests.get(
            f"{COINGECKO_API}/simple/price?ids={coin_id}&vs_currencies=usd"
        )
        response.raise_for_status()
        data = response.json()
        logger.debug(f"پاسخ API برای {coin_id}: {data}")

        if coin_id not in data:
            logger.debug(f"ارز یافت نشد: {coin_id}")
            await update.message.reply_text(
                "ارز یافت نشد! نماد را بررسی کنید. مثال: btc، eth، bitcoin"
            )
            return

        price = data[coin_id]["usd"]
        await update.message.reply_text(
            f"قیمت {symbol.upper()}: ${price:,.2f}"
        )

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"خطای HTTP در دریافت قیمت ارز {coin_id}: {http_err}")
        await update.message.reply_text("خطای سرور API. دوباره امتحان کنید یا نماد دیگری وارد کنید.")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"خطای شبکه در دریافت قیمت ارز {coin_id}: {req_err}")
        await update.message.reply_text("خطای شبکه. اینترنت خود را بررسی کنید.")
    except Exception as e:
        logger.error(f"خطای عمومی در دریافت قیمت ارز {coin_id}: {e}")
        await update.message.reply_text("خطایی رخ داد. دوباره امتحان کنید یا نماد دیگری وارد کنید.")