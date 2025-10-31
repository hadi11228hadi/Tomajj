import os
import asyncio
import pytz
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid, UserAlreadyParticipant, UserNotParticipant
from pyrogram.raw import functions
import aiohttp

# خواندن از متغیرهای محیطی
api_id = int(os.environ.get("API_ID", "25898994"))
api_hash = os.environ.get("API_HASH", "a5e6b163839bb82b4ca59b8dc6a3b5d4")
admin_id = int(os.environ.get("ADMIN_ID", "8024516184"))
deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "8024516184:upyI9z0kOQ7J3r6@Api_ManagerRoBot")

iran_tz = pytz.timezone('Asia/Tehran')
admins = {admin_id}  # مجموعه برای جلوگیری از تکرار

app = Client("my_session", api_id=api_id, api_hash=api_hash)

update_enabled = False
update_bio_enabled = False
always_online_enabled = False
update_emoji_enabled = False
last_minute = None
original_name = None
emoji_list = ["®️", "💫", "✨", "🔥", "🌙"]

deepseek_enabled = False
auto_reply_enabled = False
sent_offline_notice = set()  # برای پیگیری کاربرانی که اعلان آفلاین دریافت کرده‌اند

def is_admin(user_id):
    return user_id in admins

async def update_profile():
    global last_minute
    while update_enabled or update_bio_enabled:
        try:
            now = datetime.now(iran_tz)
            minute = now.strftime("%H:%M")

            if minute != last_minute:  
                last_minute = minute  
                if update_enabled:  
                    new_name = f"{original_name} {minute}"  
                    await app.update_profile(first_name=new_name)  
                if update_bio_enabled:  
                    await app.update_profile(bio=f"ساعت {minute}")  

            await asyncio.sleep(30)  
        except Exception as e:  
            print(f"⚠️ خطا در بروزرسانی پروفایل: {e}")  
            await asyncio.sleep(30)

async def keep_online():
    while always_online_enabled:
        try:
            await app.invoke(functions.account.UpdateStatus(offline=False))
            await asyncio.sleep(10)
        except Exception as e:
            print(f"⚠️ خطا در حالت آنلاین: {e}")
            await asyncio.sleep(10)

async def update_emoji():
    emoji_index = 0
    while update_emoji_enabled:
        try:
            new_emoji = emoji_list[emoji_index % len(emoji_list)]
            await app.update_profile(last_name=new_emoji)
            emoji_index += 1
            await asyncio.sleep(60)
        except Exception as e:
            print(f"⚠️ خطا در بروزرسانی اموجی: {e}")
            await asyncio.sleep(60)

async def deepseek_response(user_text):
    url = f"https://api.fast-creat.ir/deepseek?apikey={deepseek_api_key}&text={user_text}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # استخراج متن از ساختار JSON
                    if isinstance(data, dict):
                        if "result" in data and isinstance(data["result"], dict):
                            if "text" in data["result"]:
                                return data["result"]["text"]
                        elif "text" in data:
                            return data["text"]
                        else:
                            return str(data)
                    else:
                        return str(data)
                else:
                    return "❌ خطا در ارتباط با سرویس هوش مصنوعی"
    except Exception as e:
        return f"❌ خطا: {e}"

@app.on_message(filters.private & ~filters.me)
async def auto_reply_private(client, message):
    global deepseek_enabled, auto_reply_enabled, sent_offline_notice

    me = await app.get_me()  
    user_id = message.from_user.id

    # اگر پیام با + شروع شود (فقط برای هوش مصنوعی)
    if message.text and message.text.startswith('+'):
        if deepseek_enabled:
            user_text = message.text[1:].strip()  # حذف + از ابتدای متن
            if user_text:
                response_text = await deepseek_response(user_text)
                await message.reply_text(f"🤖 {response_text}")
        return  # اگر پیام با + شروع شده، همینجا پایان می‌یابد

    # فقط زمانی که شما آفلاین هستید و همیشه آنلاین فعال نیست
    if not always_online_enabled and auto_reply_enabled:
        # اگر کاربر هنوز اعلان آفلاین را دریافت نکرده است
        if user_id not in sent_offline_notice:
            await message.reply_text("ℹ️ من فعلاً آنلاین نیستم. لطفاً بعداً پیام دهید یا از هوش مصنوعی کمک بگیرید. برای استفاده از هوش مصنوعی کافیست قبل از پیامی که میدهید علامت + بگذارید مثال : +امروز هوا چطوره؟")
            sent_offline_notice.add(user_id)

    # اگر ادمین آنلاین شد، لیست اعلان‌ها را پاک کن
    if always_online_enabled and user_id in sent_offline_notice:
        sent_offline_notice.remove(user_id)

@app.on_message(filters.private & filters.me & filters.regex(r'^\+(.+)'))
async def deepseek_for_admin(client, message):
    global deepseek_enabled
    if not deepseek_enabled:
        await message.reply_text("❌ هوش مصنوعی غیرفعال است! از /deepseek on استفاده کنید.")
        return

    user_text = message.text[1:].strip()  # حذف + از ابتدای متن
    if user_text:
        response_text = await deepseek_response(user_text)
        await message.reply_text(f"🤖 {response_text}")

# ------------------- پایه‌ای -------------------  
@app.on_message(filters.command("start"))  
async def start_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  
    await message.reply_text("✅ ربات سلف فعال است!\nاز /help برای دیدن تمام دستورات استفاده کنید.")  

@app.on_message(filters.command("ping"))  
async def ping_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  
    await message.reply_text("🏓 Krals Online!")  

@app.on_message(filters.command("myid"))  
async def myid_command(client, message):  
    await message.reply_text(f"🆔 آیدی شما: {message.from_user.id}")  

@app.on_message(filters.command("help"))  
async def help_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  
    help_text = (  
        "📋 **راهنمای کامل سلف:**\n\n"  
        "⏰ **مدیریت زمان:**\n"  
        "/time on - فعال کردن ساعت در نام\n"  
        "/time off - غیرفعال کردن ساعت در نام\n"  
        "/time bio on - فعال کردن ساعت در بیو\n"  
        "/time bio off - غیرفعال کردن ساعت در بیو\n\n"  
        "🎭 **اموجی:**\n"  
        "/emoji on - فعال کردن تغییر خودکار اموجی\n"  
        "/emoji off - فعال کردن تغییر خودکار اموجی\n\n"  
        "🌐 **وضعیت آنلاین:**\n"  
        "/online mode on - فعال کردن همیشه آنلاین\n"  
        "/online mode off - غیرفعال کردن همیشه آنلاین\n\n"  
        "🧩 **ابزارها:**\n"  
        "/ping - بررسی وضعیت\n"  
        "/resat - غیرفعال کردن تمام بروزرسانی‌ها\n"  
        "/set name [نام] - تغییر نام\n"  
        "/clone (با ریپلی)\n\n"  
        "🤖 **هوش مصنوعی و پاسخ خودکار:**\n"  
        "/deepseek on/off - فعال/غیرفعال کردن هوش مصنوعی\n"  
        "/autoreply on/off - فعال/غیرفعال کردن پاسخ خودکار\n\n"  
        "👥 **مدیریت:**\n"  
        "/addadmin [id] - افزودن ادمین\n"  
        "/removeadmin [id] - حذف ادمین\n"  
        "/join @channel - عضویت در کانال\n"  
        "/left @channel - ترک کانال\n"  
        "/message [متن] @username - ارسال پیام\n\n"  
        "💡 **استفاده از هوش مصنوعی:**\n"  
        "برای استفاده از هوش مصنوعی، پیام خود را با + شروع کنید\n"  
        "مثال: +سلام چطوری؟"  
    )  
    await message.reply_text(help_text)  

# ------------------- مدیریت زمان -------------------  
@app.on_message(filters.command("time"))  
async def time_command(client, message):  
    global update_enabled, update_bio_enabled, original_name, last_minute  

    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    text = message.text.lower()  

    if "on" in text and "bio" not in text:  
        update_enabled = True  
        user = await app.get_me()  
        original_name = user.first_name  
        last_minute = None  
        asyncio.create_task(update_profile())  
        await message.reply_text("✅ بروزرسانی خودکار ساعت در نام فعال شد.")  

    elif "off" in text and "bio" not in text:  
        update_enabled = False  
        await message.reply_text("❌ بروزرسانی ساعت در نام غیرفعال شد.")  

    elif "bio on" in text:  
        update_bio_enabled = True  
        last_minute = None  
        asyncio.create_task(update_profile())  
        await message.reply_text("✅ بروزرسانی خودکار ساعت در بیو فعال شد.")  

    elif "bio off" in text:  
        update_bio_enabled = False  
        await message.reply_text("❌ بروزرسانی ساعت در بیو غیرفعال شد.")  

# ------------------- ریست همه -------------------  
@app.on_message(filters.command("resat"))  
async def resat_command(client, message):  
    global update_enabled, update_bio_enabled, update_emoji_enabled, always_online_enabled, sent_offline_notice  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    update_enabled = False  
    update_bio_enabled = False  
    update_emoji_enabled = False  
    always_online_enabled = False  
    sent_offline_notice.clear()  # پاک کردن لیست اعلان‌ها  
    await message.reply_text("🔄 همه بروزرسانی‌ها غیرفعال شدند.")  

# ------------------- تغییر نام -------------------  
@app.on_message(filters.command("set"))  
async def set_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    if "name" in message.text:  
        try:  
            new_name = message.text.split("name", 1)[1].strip()  
            global original_name  
            original_name = new_name  
            await app.update_profile(first_name=new_name)  
            await message.reply_text(f"✅ نام تغییر یافت به: {new_name}")  
        except Exception as e:  
            await message.reply_text(f"❌ خطا: {e}")  

# ------------------- کپی پروفایل -------------------  
@app.on_message(filters.command("clone"))  
async def clone_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    if not message.reply_to_message or not message.reply_to_message.from_user:  
        return await message.reply_text("❌ لطفاً روی پیام شخص موردنظر ریپلای کنید.")  

    try:  
        replied_user = message.reply_to_message.from_user  
        user_details = await app.get_chat(replied_user.id)  
        await app.update_profile(  
            first_name=replied_user.first_name or "",  
            last_name=replied_user.last_name or "",  
            bio=user_details.bio or ""  
        )  
        global original_name  
        original_name = replied_user.first_name or ""  
        await message.reply_text(f"✅ پروفایل {replied_user.first_name} کپی شد.")  
    except Exception as e:  
        await message.reply_text(f"❌ خطا در کپی پروفایل: {e}")  

# ------------------- همیشه آنلاین -------------------  
@app.on_message(filters.command("online"))  
async def online_command(client, message):  
    global always_online_enabled, sent_offline_notice  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    text = message.text.lower()  
    if "mode on" in text:  
        always_online_enabled = True  
        sent_offline_notice.clear()  # پاک کردن لیست اعلان‌ها هنگام آنلاین شدن  
        asyncio.create_task(keep_online())  
        await message.reply_text("✅ همیشه آنلاین فعال شد.")  
    elif "mode off" in text:  
        always_online_enabled = False  
        await message.reply_text("❌ همیشه آنلاین غیرفعال شد.")  

# ------------------- اموجی -------------------  
@app.on_message(filters.command("emoji"))  
async def emoji_command(client, message):  
    global update_emoji_enabled  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    text = message.text.lower()  
    if "on" in text:  
        update_emoji_enabled = True  
        asyncio.create_task(update_emoji())  
        await message.reply_text("✅ تغییر خودکار اموجی فعال شد.")  
    elif "off" in text:  
        update_emoji_enabled = False  
        await message.reply_text("❌ تغییر خودکار اموجی غیرفعال شد.")  

# ------------------- ارسال پیام -------------------  
@app.on_message(filters.command("message"))  
async def message_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  
    try:  
        parts = message.text.split()  
        if len(parts) >= 3 and parts[-1].startswith('@'):  
            text = ' '.join(parts[1:-1])  
            username = parts[-1][1:]  
            user = await client.get_users(username)  
            await client.send_message(user.id, text)  
            await message.reply_text(f"✅ پیام به @{username} ارسال شد.")  
        else:  
            await message.reply_text("❌ فرمت صحیح: /message متن @username")  
    except PeerIdInvalid:  
        await message.reply_text("❌ کاربر یافت نشد.")  
    except Exception as e:  
        await message.reply_text(f"❌ خطا در ارسال پیام: {e}")  

# ------------------- ادمین -------------------  
@app.on_message(filters.command("addadmin"))  
async def addadmin_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    try:  
        parts = message.text.split()  
        if len(parts) == 2:  
            new_admin = int(parts[1])  
            admins.add(new_admin)  
            await message.reply_text(f"✅ {new_admin} به ادمین‌ها اضافه شد.")  
        else:  
            await message.reply_text("❌ فرمت صحیح: /addadmin [id]")  
    except ValueError:  
        await message.reply_text("❌ آیدی باید عدد باشد.")  

@app.on_message(filters.command("removeadmin"))  
async def removeadmin_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    try:  
        parts = message.text.split()  
        if len(parts) == 2:  
            rem_admin = int(parts[1])  
            if rem_admin in admins:  
                admins.remove(rem_admin)  
                await message.reply_text(f"✅ {rem_admin} از لیست ادمین‌ها حذف شد.")  
            else:  
                await message.reply_text("❌ این کاربر ادمین نیست.")  
        else:  
            await message.reply_text("❌ فرمت صحیح: /removeadmin [id]")  
    except ValueError:  
        await message.reply_text("❌ آیدی باید عدد باشد.")  

# ------------------- عضویت/ترک -------------------  
@app.on_message(filters.command("join"))  
async def join_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  
    try:  
        parts = message.text.split()  
        if len(parts) == 2 and parts[1].startswith('@'):  
            await client.join_chat(parts[1])  
            await message.reply_text(f"✅ با موفقیت وارد {parts[1]} شدم.")  
        else:  
            await message.reply_text("❌ فرمت صحیح: /join @username")  
    except UserAlreadyParticipant:  
        await message.reply_text("ℹ️ از قبل عضو هستم.")  
    except Exception as e:  
        await message.reply_text(f"❌ خطا در عضویت: {e}")  

@app.on_message(filters.command("left"))  
async def left_command(client, message):  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  
    try:  
        parts = message.text.split()  
        if len(parts) == 2 and parts[1].startswith('@'):  
            await client.leave_chat(parts[1])  
            await message.reply_text(f"✅ از {parts[1]} خارج شدم.")  
        else:  
            await message.reply_text("❌ فرمت صحیح: /left @username")  
    except UserNotParticipant:  
        await message.reply_text("ℹ️ عضو نیستم.")  
    except Exception as e:  
        await message.reply_text(f"❌ خطا در خروج: {e}")  

# ------------------- کنترل هوش مصنوعی -------------------  
@app.on_message(filters.command("deepseek"))  
async def deepseek_command(client, message):  
    global deepseek_enabled  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    text = message.text.lower()  
    if "on" in text:  
        deepseek_enabled = True  
        await message.reply_text("✅ هوش مصنوعی DeepSeek فعال شد.")  
    elif "off" in text:  
        deepseek_enabled = False  
        await message.reply_text("❌ هوش مصنوعی DeepSeek غیرفعال شد.")  

# ------------------- کنترل پاسخ خودکار -------------------  
@app.on_message(filters.command("autoreply"))  
async def autoreply_command(client, message):  
    global auto_reply_enabled  
    if not is_admin(message.from_user.id):  
        return await message.reply_text("❌ دسترسی ندارید!")  

    text = message.text.lower()  
    if "on" in text:  
        auto_reply_enabled = True  
        await message.reply_text("✅ پاسخگویی خودکار فعال شد.")  
    elif "off" in text:  
        auto_reply_enabled = False  
        await message.reply_text("❌ پاسخگویی خودکار غیرفعال شد.")

if __name__ == "__main__":
    print("=" * 50)
    print("✅ ربات سلف آماده اجرا است...")
    print("📡 در حال راه‌اندازی کلاینت Pyrogram...")
    print(f"🆔 API ID: {api_id}")
    print(f"👤 ادمین: {admin_id}")
    print("⏰ زمان تهران:", datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    app.run()