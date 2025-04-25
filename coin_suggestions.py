from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# لیست نمادهای محبوب
POPULAR_COINS = [
    "btc",  # بیت‌کوین
    "eth",  # اتریوم
    "usdt", # تتر
    "bnb",  # بایننس‌کوین
    "sol",  # سولانا
]

def get_suggestions_panel(mode: str) -> InlineKeyboardMarkup:
    """
    ساخت پنل شیشه‌ای با نمادهای محبوب.
    ورودی:
        mode: "price" برای نمایش قیمت، "info" برای نمایش اطلاعات
    خروجی:
        InlineKeyboardMarkup با دکمه‌های نمادهای محبوب
    """
    keyboard = []
    # هر ردیف 3 دکمه داشته باشه
    row = []
    for coin in POPULAR_COINS:
        button = InlineKeyboardButton(
            text=coin.upper(),
            callback_data=f"{mode}_{coin}"  # مثلاً price_btc یا info_eth
        )
        row.append(button)
        if len(row) == 3:  # هر ردیف 3 دکمه
            keyboard.append(row)
            row = []
    if row:  # اضافه کردن ردیف آخر اگه پر نشده
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)