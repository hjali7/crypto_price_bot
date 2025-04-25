import logging
import requests
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, 
    filters, ConversationHandler
)
from io import BytesIO
from dotenv import load_dotenv
import os
from top_coins import get_top_coins_panel
from coin_info import get_coin_info
from coin_price import get_coin_price

# تنظیم لاگینگ با جزئیات بیشتر
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# دریافت توکن از متغیر محیطی
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# URLهای API کوین‌گکو
COINGECKO_API = "https://api.coingecko.com/api/v3"

# حالت‌های ConversationHandler
COIN_SYMBOL_INFO = 0
COIN_SYMBOL_PRICE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال پیام خوش‌آمدگویی با پنل شیشه‌ای"""
    logger.debug(f"دریافت پیام /start از کاربر {update.effective_user.id}")
    user = update.effective_user
    # تعریف دکمه‌های پنل شیشه‌ای با ایموجی
    keyboard = [
        [
            InlineKeyboardButton("💰 نمایش قیمت", callback_data="price"),
            InlineKeyboardButton("ℹ️ اطلاعات ارز", callback_data="info"),
        ],
        [
            InlineKeyboardButton("📈 نمودار قیمت", callback_data="chart"),
            InlineKeyboardButton("🏆 10 ارز برتر", callback_data="top"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_html(
        rf"سلام {user.mention_html()}! 👋 به ربات قیمت ارز دیجیتال خوش آمدید! 📈"
        "\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id if update.message else None
    )

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ری‌استارت ربات (همان عملکرد /start)"""
    logger.debug(f"دریافت پیام /restart از کاربر {update.effective_user.id}")
    await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت پیام‌های غیرفرمان با دکمه شروع مجدد"""
    logger.debug(f"دریافت پیام متنی: {update.message.text} از کاربر {update.effective_user.id}")
    keyboard = [[InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "لطفاً از دستورات ربات استفاده کنید یا برای بازگشت به منوی اصلی، دکمه زیر را بزنید:",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id
    )

async def start_coin_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع مکالمه برای دریافت نماد ارز (اطلاعات)"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "لطفاً نماد ارز را وارد کنید (مثال: btc، eth، bitcoin):",
        reply_to_message_id=query.message.message_id
    )
    return COIN_SYMBOL_INFO

async def start_coin_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع مکالمه برای دریافت نماد ارز (قیمت)"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "لطفاً نماد ارز را وارد کنید (مثال: btc، eth، bitcoin):",
        reply_to_message_id=query.message.message_id
    )
    return COIN_SYMBOL_PRICE

async def receive_coin_symbol_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نماد ارز و نمایش اطلاعات"""
    symbol = update.message.text.strip()
    logger.debug(f"نماد دریافت‌شده برای اطلاعات: {symbol} از کاربر {update.effective_user.id}")
    await get_coin_info(update, context, symbol)
    # پایان مکالمه
    return ConversationHandler.END

async def receive_coin_symbol_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نماد ارز و نمایش قیمت"""
    symbol = update.message.text.strip()
    logger.debug(f"نماد دریافت‌شده برای قیمت: {symbol} از کاربر {update.effective_user.id}")
    await get_coin_price(update, context, symbol)
    # پایان مکالمه
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو مکالمه"""
    logger.debug(f"لغو مکالمه توسط کاربر {update.effective_user.id}")
    await update.message.reply_text(
        "عملیات لغو شد. برای شروع دوباره، /start را بزنید."
    )
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت کلیک روی دکمه‌های پنل"""
    query = update.callback_query
    await query.answer()
    logger.debug(f"کلیک روی دکمه: {query.data} توسط کاربر {query.from_user.id}")

    if query.data == "price":
        return await start_coin_price(update, context)
    elif query.data == "info":
        return await start_coin_info(update, context)
    elif query.data == "chart":
        await query.message.reply_text(
            "لطفاً نماد ارز را وارد کنید. مثال: /chart btc",
            reply_to_message_id=query.message.message_id
        )
    elif query.data == "top":
        message, reply_markup = get_top_coins_panel()
        await query.message.reply_text(
            message,
            reply_markup=reply_markup,
            reply_to_message_id=query.message.message_id
        )
    elif query.data == "restart":
        await start(query, context)
    elif query.data.startswith("coin_"):
        # مدیریت کلیک روی دکمه‌های 10 ارز برتر
        coin_id = query.data.split("_")[1]
        await get_coin_info(query, context, coin_id)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش قیمت لحظه‌ای یک ارز (برای دستور مستقیم /price)"""
    logger.debug(f"اجرای دستور /price توسط کاربر {update.effective_user.id}")
    if not context.args:
        await update.message.reply_text(
            "لطفاً نماد ارز را وارد کنید. مثال: /price btc"
        )
        return

    symbol = context.args[0].lower()
    await get_coin_price(update, context, symbol)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش اطلاعات ارز با استفاده از ماژول (برای دستور مستقیم /info)"""
    logger.debug(f"اجرای دستور /info توسط کاربر {update.effective_user.id}")
    symbol = context.args[0] if context.args else ""
    await get_coin_info(update, context, symbol)

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش نمودار قیمت 7 روزه"""
    logger.debug(f"اجرای دستور /chart توسط کاربر {update.effective_user.id}")
    if not context.args:
        await update.message.reply_text(
            "لطفاً نماد ارز را وارد کنید. مثال: /chart btc"
        )
        return

    symbol = context.args[0].lower()
    try:
        response = requests.get(
            f"{COINGECKO_API}/coins/{symbol}/market_chart?vs_currency=usd&days=7"
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("prices"):
            await update.message.reply_text(
                "داده‌ای برای نمودار یافت نشد!"
            )
            return

        prices = [price[1] for price in data["prices"]]
        times = [i for i in range(len(prices))]

        plt.figure(figsize=(10, 5))
        plt.plot(times, prices, label=f"{symbol.upper()} Price (USD)")
        plt.title(f"نمودار قیمت {symbol.upper()} در 7 روز گذشته")
        plt.xlabel("زمان")
        plt.ylabel("قیمت (دلار)")
        plt.legend()
        plt.grid(True)

        # ذخیره نمودار در حافظه
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close()

        await update.message.reply_photo(
            photo=buffer
        )
    except Exception as e:
        logger.error(f"خطا در تولید نمودار: {e}")
        await update.message.reply_text(
            "خطایی رخ داد. دوباره امتحان کنید."
        )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش 10 ارز برتر با استفاده از ماژول"""
    logger.debug(f"اجرای دستور /top توسط کاربر {update.effective_user.id}")
    message, reply_markup = get_top_coins_panel()
    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت خطاها"""
    logger.error(f"خطا رخ داد: {context.error}")
    if update:
        await update.message.reply_text(
            "خطایی رخ داد. لطفاً دوباره امتحان کنید."
        )

def main() -> None:
    """اجرای ربات"""
    if not BOT_TOKEN:
        logger.error("توکن ربات پیدا نشد! لطفاً فایل .env را بررسی کنید.")
        return

    logger.info("ربات شروع به کار کرد!")
    application = Application.builder().token(BOT_TOKEN).build()

    # تعریف ConversationHandler برای اطلاعات ارز
    info_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_coin_info, pattern="^info$")],
        states={
            COIN_SYMBOL_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_coin_symbol_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # تعریف ConversationHandler برای قیمت ارز
    price_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_coin_price, pattern="^price$")],
        states={
            COIN_SYMBOL_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_coin_symbol_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # افزودن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("chart", chart))
    application.add_handler(CommandHandler("top", top))
    application.add_handler(info_handler)
    application.add_handler(price_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # هندلر خطا
    application.add_error_handler(error_handler)

    # شروع ربات
    logger.info("شروع polling ربات...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()