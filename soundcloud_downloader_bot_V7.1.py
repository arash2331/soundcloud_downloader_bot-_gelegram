"""
V7.1

"""
import os
import asyncio
from datetime import timedelta
from urllib.parse import urlparse
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatAction
from youtube_dl import YoutubeDL
from PIL import Image
import ffmpeg
import re

# Config
API_ID = "API_ID"
API_HASH = "API_HASH"
BOT_TOKEN = "BOT_TOKEN"
admin_chat_id = "admin_chat_id"

MUSIC_MAX_LENGTH = 10800
DELAY_DELETE_INFORM = 10
TG_THUMB_MAX_LENGTH = 320
REGEX_SITES = (
    r"^((?:https?:)?\/\/)?"  # پروتکل اختیاری
    r"((?:www|m|on)\.)?"    # www، m یا on به‌صورت اختیاری
    r"(soundcloud\.com|mixcloud\.com|youtube\.com|youtu\.be)"  # دامنه‌های معتبر
    r"(\/)([-a-zA-Z0-9()@:%_\+.~#?&//=]*)([\w\-]+)(\S+)?$"  # مسیر URL
)
REGEX_EXCLUDE_URL = (
    r"\/channel\/|\/playlist\?list=|&list=|\/sets\/"
)
os.environ["API_ID"] = API_ID
os.environ["API_HASH"] = API_HASH
os.environ["BOT_TOKEN"] = BOT_TOKEN

def is_user_in_file(user_id: int) -> bool:
        with open("allowed_users.txt", "r") as file:
            # خواندن تمام خطوط و تبدیل به لیست
            user_ids = [line.strip() for line in file if line.strip().isdigit()]
        if str(user_id) in user_ids:
            return True
        else:
            return False

def append_to_file(text: str):
    try:
        # باز کردن فایل در حالت خواندن برای بررسی وجود متن
        with open('allowed_users.txt', "r") as file:
            lines = file.readlines()

        # بررسی وجود متن
        if text + "\n" not in lines:  # چک می‌کنیم آیا متن قبلاً اضافه شده یا نه
            with open('allowed_users.txt', "a") as file:  # باز کردن فایل در حالت append
                file.write(f"{text}\n")  # اضافه کردن متن به خط جدید
    except FileNotFoundError:
        # اگر فایل وجود نداشت، فایل را ایجاد کرده و متن را به آن اضافه می‌کنیم
        with open('allowed_users.txt', "w") as file:
            file.write(f"{text}\n")

def remove_from_file(text: str):
    try:
        # خواندن محتوای فایل
        with open('allowed_users.txt', "r") as file:
            lines = file.readlines()

        # حذف متن مشخص از خطوط
        with open('allowed_users.txt', "w") as file:
            for line in lines:
                if line.strip() != text:  # اگر خط برابر متن نبود، دوباره به فایل بنویس
                    file.write(line)
    except FileNotFoundError:
        pass
#--------------------

# MUSIC_CHATS = get_music_chats()
API_ID = os.environ["API_ID"]
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# - handlers and functions
main_filter = (
    filters.text
    # filters.chat(MUSIC_CHATS)
    & filters.incoming
    #& ~filters.edited
)

@app.on_message(main_filter & filters.regex("^/help"))
async def start(_, message: Message):
    ADMINS = str(admin_chat_id)
    if ADMINS == str(message.from_user.id):

        await message.reply_text('''/start استارت
/ping 
/add [user_id] - افزودن کاربر به لیست مجاز
/del [user_id] - حذف کاربر از لیست مجاز
/list - مشاهده لیست کاربران مجاز
''')

@app.on_message(filters.command("add") & filters.text)
def handle_add_command(client, message):
    ADMINS = str(admin_chat_id)
    if ADMINS == str(message.from_user.id):
        try:
            # بررسی فرمت پیام: باید /add به همراه یک شماره باشد
            if len(message.text.split()) != 2:
                message.reply("فرمت صحیح: /add [شماره]\nلطفاً شماره‌ای وارد کنید.")
                return
            
            # جداسازی شماره
            command, number = message.text.split()  # بخش اول دستور است و بخش دوم شماره

            # بررسی اینکه شماره فقط شامل ارقام باشد
            if not number.isdigit():
                message.reply("لطفاً یک شماره معتبر وارد کنید.")
                return

            # پاسخ به کاربر
            message.reply(f"شماره {number} با موفقیت ثبت شد!")

            # ذخیره شماره (در صورت نیاز)
            append_to_file(number)  # تابع ذخیره شماره در فایل

        except Exception as e:
            message.reply(f"یک خطا رخ داد: {str(e)}")


@app.on_message(filters.command("del") & filters.text)
def handle_remove_command(client, message):
    ADMINS = str(admin_chat_id)
    if ADMINS == str(message.from_user.id):
        try:
            # بررسی فرمت پیام: باید /del به همراه یک شماره باشد
            if len(message.text.split()) != 2:
                message.reply("فرمت صحیح: /del [شماره]\nلطفاً شماره‌ای وارد کنید.")
                return

            # جداسازی شماره
            command, number = message.text.split()  # بخش اول دستور است و بخش دوم شماره

            # بررسی اینکه شماره فقط شامل ارقام باشد
            if not number.isdigit():
                message.reply("لطفاً یک شماره معتبر وارد کنید.")
                return

            # حذف شماره از فایل
            result = remove_from_file(number)  # تابع حذف شماره از فایل

            if result:
                message.reply(f"شماره {number} با موفقیت حذف شد!")
            else:
                message.reply(f"شماره {number} در فایل پیدا نشد.")

        except Exception as e:
            message.reply(f"یک خطا رخ داد: {str(e)}")

@app.on_message(filters.command("list") & filters.text)
def handle_list_command(client, message):
    ADMINS = str(admin_chat_id)
    if ADMINS == str(message.from_user.id):
        try:
            # خواندن محتوای فایل
            with open("allowed_users.txt", "r") as file:
                lines = file.readlines()

            # بررسی اینکه آیا فایل خالی است
            if not lines:
                message.reply("📂 لیست کاربران خالی است.")
                return

            # ساخت پیام برای نمایش لیست کاربران
            users_list = "\n".join(f"{i + 1}. {line.strip()}" for i, line in enumerate(lines))
            message.reply(f"📋 لیست کاربران ذخیره‌شده:\n\n{users_list}")

        except FileNotFoundError:
            message.reply("❌ فایل کاربران پیدا نشد. لیست خالی است.")
        except Exception as e:
            message.reply(f"یک خطا رخ داد: {str(e)}")


@app.on_message(main_filter & filters.regex("^/ping$"))
async def ping_pong(_, message):
    user_id = message.from_user.id  # آی‌دی عددی کاربر
    username = message.from_user.username or "بدون یوزرنیم"  # یوزرنیم کاربر (در صورت وجود)
    full_name = message.from_user.first_name  # نام کاربر
    text = message.text  # متن پیام

    # قالب متن برای ارسال به ادمین
    log_text = (
        f"📥 پیام جدید دریافت شد:\n"
        f"👤 کاربر: {full_name}\n"
        f"🔗 یوزرنیم: @{username}\n"
        f"🆔 آی‌دی عددی: {user_id}\n"
        f"💬 پیام:\n{text}"
    )
    await app.send_message(chat_id=admin_chat_id, text=log_text)
    if is_user_in_file(message.from_user.id) == True:
        await _reply_and_delete_later(message, "pong",
                                    DELAY_DELETE_INFORM)

@app.on_message(main_filter & filters.regex("^/start"))
async def start(_, message: Message):
    user_id = message.from_user.id  # آی‌دی عددی کاربر
    username = message.from_user.username or "بدون یوزرنیم"  # یوزرنیم کاربر (در صورت وجود)
    full_name = message.from_user.first_name  # نام کاربر
    text = message.text  # متن پیام

    # قالب متن برای ارسال به ادمین
    log_text = (
        f"📥 پیام جدید دریافت شد:\n"
        f"👤 کاربر: {full_name}\n"
        f"🔗 یوزرنیم: @{username}\n"
        f"🆔 آی‌دی عددی: {user_id}\n"
        f"💬 پیام:\n{text}"
    )
    await app.send_message(chat_id=admin_chat_id, text=log_text)
    if is_user_in_file(message.from_user.id) == True:

        await message.reply_text('''🎵 SoundCloud Downloader 🎵
سلام! 👋 من ربات دانلودر SoundCloud هستم و به شما کمک می‌کنم تا موسیقی‌ها و ترک‌های مورد علاقه‌تان را به راحتی دانلود کنید.

📌 امکانات من:

🎧 دانلود موسیقی با کیفیت بالا

🔍 پیدا کردن ترک‌ها با لینک مستقیم

📥 دریافت سریع و آسان فایل‌های صوتی
1. لینک ترک مورد نظر را از SoundCloud کپی کنید.

2. لینک را برای من ارسال کنید.

3. فایل آماده دانلود خواهد شد!

📞 پشتیبانی: @insta_data_Support''') 

# Regex برای شناسایی لینک‌های SoundCloud
SOUNDCLOUD_LINK_REGEX = r'(https:\/\/(?:m\.)?soundcloud\.com\/[^\s]+|https:\/\/on\.soundcloud\.com\/[a-zA-Z0-9]+)'

@app.on_message(main_filter & filters.regex(SOUNDCLOUD_LINK_REGEX))
async def music_downloader(_, message: Message):
    user_id = message.from_user.id  # آی‌دی عددی کاربر
    username = message.from_user.username or "بدون یوزرنیم"  # یوزرنیم کاربر (در صورت وجود)
    full_name = message.from_user.first_name  # نام کاربر
    text = message.text  # متن پیام

    # قالب متن برای ارسال به ادمین
    log_text = (
        f"📥 پیام جدید دریافت شد:\n"
        f"👤 کاربر: {full_name}\n"
        f"🔗 یوزرنیم: @{username}\n"
        f"🆔 آی‌دی عددی: {user_id}\n"
        f"💬 پیام:\n{text}"
    )
    await app.send_message(chat_id=admin_chat_id, text=log_text)

    print(message.text)
    if is_user_in_file(message.from_user.id):  # بررسی کاربر
        link = re.search(SOUNDCLOUD_LINK_REGEX, message.text).group(0)
        await _fetch_and_send_music(message, link)
    else:
        await message.reply("⛔ شما اجازه استفاده از این قابلیت را ندارید.")


async def _fetch_and_send_music(message: Message, link: str):
    await message.reply_chat_action(ChatAction.TYPING)
    try:
        # تنظیمات yt-dlp برای دانلود
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': '%(title)s - %(extractor)s-%(id)s.%(ext)s',
            'writethumbnail': True
        }
        ydl = YoutubeDL(ydl_opts)
        info_dict = ydl.extract_info(link, download=False)

        # بررسی دسته‌بندی غیرمجاز (اختیاری)
        if not message.reply_to_message and _youtube_video_not_music(info_dict):
            inform = ("این لینک در دسته‌بندی موسیقی قرار ندارد. "
                      "می‌توانید لینک را به عنوان پاسخ ارسال کنید تا اجباراً دانلود شود.")
            await _reply_and_delete_later(message, inform, DELAY_DELETE_INFORM)
            return

        # بررسی محدودیت طول موسیقی
        if info_dict['duration'] > MUSIC_MAX_LENGTH:
            readable_max_length = str(timedelta(seconds=MUSIC_MAX_LENGTH))
            inform = ("این فایل دانلود نمی‌شود زیرا طول آن بیشتر از حد مجاز است: "
                      "`{}`".format(readable_max_length))
            await _reply_and_delete_later(message, inform, DELAY_DELETE_INFORM)
            return

        # شروع دانلود
        d_status = await message.reply_text("🎵 Downloading...", quote=True, disable_notification=True)
        ydl.process_info(info_dict)
        audio_file = ydl.prepare_filename(info_dict)

        # آپلود موسیقی
        task = asyncio.create_task(_upload_audio(message, info_dict, audio_file))
        await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
        await d_status.delete()

        # نمایش وضعیت آپلود
        while not task.done():
            await asyncio.sleep(4)
            await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)

        await message.reply_chat_action(ChatAction.CANCEL)
        if message.chat.type == "private":
            await message.delete()
    except Exception as e:
        await message.reply_text(f"⛔ خطایی رخ داده است: {repr(e)}")

async def _upload_audio(message: Message, info_dict: dict, audio_file: str):
    try:
        # اطلاعات فایل
        title = info_dict.get("title", "بدون عنوان")
        artist = info_dict.get("uploader", "ناشناس")
        duration = info_dict.get("duration", 0)

        # آپلود موسیقی
        await message.reply_audio(
            audio=audio_file,
            title=title,
            performer=artist,
            duration=duration
        )
    except Exception as e:
        await message.reply_text(f"⛔ خطا در ارسال موسیقی: {e}")


def _youtube_video_not_music(info_dict):
    if info_dict['extractor'] == 'youtube' \
            and 'Music' not in info_dict['categories']:
        return True
    return False


async def _reply_and_delete_later(message: Message, text: str, delay: int):
    reply = await message.reply_text(text, quote=True)
    await asyncio.sleep(delay)
    await reply.delete()


async def _upload_audio(message: Message, info_dict, audio_file):
    basename = audio_file.rsplit(".", 1)[-2]
    if info_dict['ext'] == 'webm':
        audio_file_opus = basename + ".opus"
        ffmpeg.input(audio_file).output(audio_file_opus, codec="copy").run()
        os.remove(audio_file)
        audio_file = audio_file_opus
    thumbnail_url = info_dict['thumbnail']
    if os.path.isfile(basename + ".jpg"):
        thumbnail_file = basename + ".jpg"
    else:
        thumbnail_file = basename + "." + \
            _get_file_extension_from_url(thumbnail_url)
    squarethumb_file = basename + "_squarethumb.jpg"
    make_squarethumb(thumbnail_file, squarethumb_file)
    webpage_url = info_dict['webpage_url']
    title = info_dict['title']
    caption = f"<b><a href=\"{webpage_url}\">{title}</a></b>"
    duration = int(float(info_dict['duration']))
    performer = info_dict['uploader']
    await message.reply_audio(audio_file,
                              caption=caption,
                              duration=duration,
                              performer=performer,
                              title=title,
                              parse_mode=ParseMode.HTML,
                              thumb=squarethumb_file)
    for f in (audio_file, thumbnail_file, squarethumb_file):
        os.remove(f)

@app.on_message(filters.text)
async def log_message(_, message: Message):
    ADMINS = [admin_chat_id]
    # اطلاعات پیام و کاربر ارسال‌کننده
    user_id = message.from_user.id  # آی‌دی عددی کاربر
    username = message.from_user.username or "بدون یوزرنیم"  # یوزرنیم کاربر (در صورت وجود)
    full_name = message.from_user.first_name  # نام کاربر
    text = message.text  # متن پیام

    # قالب متن برای ارسال به ادمین
    log_text = (
        f"📥 پیام جدید دریافت شد:\n"
        f"👤 کاربر: {full_name}\n"
        f"🔗 یوزرنیم: @{username}\n"
        f"🆔 آی‌دی عددی: {user_id}\n"
        f"💬 پیام:\n{text}"
    )

    # ارسال لاگ به همه ادمین‌ها
    for admin_id in ADMINS:
        try:
            await app.send_message(chat_id=admin_id, text=log_text)
        except Exception as e:
            print(f"خطا در ارسال پیام به ادمین {admin_id}: {e}")

def _get_file_extension_from_url(url):
    url_path = urlparse(url).path
    basename = os.path.basename(url_path)
    return basename.split(".")[-1]


def make_squarethumb(thumbnail, output):
    """Convert thumbnail to square thumbnail"""
    # https://stackoverflow.com/a/52177551
    original_thumb = Image.open(thumbnail)
    squarethumb = _crop_to_square(original_thumb)
    squarethumb.thumbnail((TG_THUMB_MAX_LENGTH, TG_THUMB_MAX_LENGTH),
                          Image.Resampling.LANCZOS)
    squarethumb.save(output)


def _crop_to_square(img):
    width, height = img.size
    length = min(width, height)
    left = (width - length) / 2
    top = (height - length) / 2
    right = (width + length) / 2
    bottom = (height + length) / 2
    return img.crop((left, top, right, bottom))


# - start


app.start()
print('>>> BOT STARTED')
idle()
app.stop()
print('\n>>> BOT STOPPED')
