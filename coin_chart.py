import logging
import requests
import matplotlib.pyplot as plt
from telegram.ext import ContextTypes
from telegram import Update
from io import BytesIO
import numpy as np
from datetime import datetime, timedelta

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

async def get_coin_chart(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> None:
    """
    دریافت و نمایش نمودار قیمت 7 روزه ارز با نماد یا شناسه داده‌شده (case-insensitive).
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
    logger.debug(f"درخواست نمودار برای ارز: {symbol} توسط کاربر {update.effective_user.id}")

    # تبدیل نماد اختصاری به شناسه کامل (اگه لازم باشه)
    coin_id = SYMBOL_TO_ID.get(symbol, symbol)
    logger.debug(f"شناسه ارز برای API: {coin_id}")

    try:
        # درخواست به API کوین‌گکو برای نمودار قیمت 7 روزه
        response = requests.get(
            f"{COINGECKO_API}/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
        )
        response.raise_for_status()
        data = response.json()
        logger.debug(f"پاسخ API برای {coin_id}: {data}")

        if not data.get("prices"):
            logger.debug(f"داده‌ای برای نمودار یافت نشد: {coin_id}")
            await update.message.reply_text(
                "داده‌ای برای نمودار یافت نشد! نماد را بررسی کنید."
            )
            return

        # استخراج قیمت‌ها و زمان‌ها
        prices = [price[1] for price in data["prices"]]
        timestamps = [price[0] for price in data["prices"]]  # زمان‌ها به‌صورت timestamp

        # تبدیل زمان‌ها به تاریخ خوانا
        dates = [datetime.fromtimestamp(ts / 1000) for ts in timestamps]
        date_labels = [date.strftime("%Y-%m-%d") for date in dates]

        # محاسبه قیمت بالا و پایین
        high_price = max(prices)
        low_price = min(prices)

        # محاسبه میانگین متحرک 3 روزه
        window_size = 3
        moving_average = np.convolve(prices, np.ones(window_size)/window_size, mode='valid')
        # تنظیم طول برای تطبیق با داده‌ها
        ma_x = range(window_size-1, len(prices))

        # تنظیم تم تیره
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='black')
        ax.set_facecolor('black')

        # رسم نمودار قیمت
        ax.plot(prices, label=f"{symbol.upper()} Price (USD)", color='cyan', linewidth=2)
        # رسم میانگین متحرک
        ax.plot(ma_x, moving_average, label="3-Day Moving Average", color='orange', linestyle='--', linewidth=1.5)

        # تنظیم محورها
        ax.set_title(
            f"نمودار قیمت {symbol.upper()} (7 روز گذشته)\n"
            f"بالاترین: ${high_price:,.2f} | پایین‌ترین: ${low_price:,.2f}",
            color='white', fontsize=12, pad=15
        )
        ax.set_xlabel("تاریخ", color='white', fontsize=10)
        ax.set_ylabel("قیمت (دلار)", color='white', fontsize=10)

        # تنظیم تیک‌های محور X با تاریخ‌ها
        step = len(dates) // 5  # 5 تیک روی محور X
        if step == 0:
            step = 1
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels([date_labels[i] for i in range(0, len(dates), step)], rotation=45, color='white')

        # تنظیم تیک‌های محور Y
        ax.tick_params(axis='y', colors='white')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))

        # اضافه کردن گرید و لجند
        ax.grid(True, linestyle='--', alpha=0.5, color='gray')
        ax.legend(facecolor='black', edgecolor='white', labelcolor='white')

        # تنظیمات نهایی
        plt.tight_layout()

        # ذخیره نمودار در حافظه
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches='tight', facecolor='black')
        buffer.seek(0)
        plt.close()

        await update.message.reply_photo(
            photo=buffer
        )

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"خطای HTTP در دریافت نمودار ارز {coin_id}: {http_err}")
        await update.message.reply_text("خطای سرور API. دوباره امتحان کنید یا نماد دیگری وارد کنید.")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"خطای شبکه در دریافت نمودار ارز {coin_id}: {req_err}")
        await update.message.reply_text("خطای شبکه. اینترنت خود را بررسی کنید.")
    except Exception as e:
        logger.error(f"خطای عمومی در دریافت نمودار ارز {coin_id}: {e}")
        await update.message.reply_text("خطایی رخ داد. دوباره امتحان کنید یا نماد دیگری وارد کنید.")