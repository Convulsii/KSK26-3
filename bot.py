import os
import datetime
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== НАСТРОЙКИ =====
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YA_DISK_TOKEN = os.getenv('YA_DISK_TOKEN')
FILE_PATH = os.getenv('FILE_PATH', '/schedule.json')

if not TELEGRAM_TOKEN or not YA_DISK_TOKEN:
    print("❌ Ошибка: не заданы TELEGRAM_TOKEN или YA_DISK_TOKEN")
    exit(1)

# ===== РАСПИСАНИЕ ВРЕМЕНИ =====
TIMES = {
    'monday': {
        'class_hour': ('8:00', '8:30'),
        '1': ('8:30', '10:00'),
        '2': ('10:10', '11:40'),
        '3': ('12:20', '13:50'),
        '4': ('14:35', '16:05'),
        '5': ('16:15', '17:45'),
        '6': ('17:50', '18:50')
    },
    'tue_fri': {
        '1': ('8:15', '9:45'),
        '2': ('9:55', '11:25'),
        '3': ('12:05', '13:35'),
        '4': ('13:45', '15:15'),
        '5': ('15:40', '17:10'),
        '6': ('17:20', '18:50')
    },
    'saturday': {
        '1': ('8:15', '9:15'),
        '2': ('9:25', '10:25'),
        '3': ('10:35', '11:35'),
        '4': ('12:05', '13:05'),
        '5': ('13:15', '14:15'),
        '6': ('14:25', '15:25')
    }
}

DAY_MAP = {
    'monday': 'пн',
    'tuesday': 'вт',
    'wednesday': 'ср',
    'thursday': 'чт',
    'friday': 'пт',
    'saturday': 'сб',
    'sunday': None
}

DAY_TYPE = {
    'пн': 'monday',
    'вт': 'tue_fri',
    'ср': 'tue_fri',
    'чт': 'tue_fri',
    'пт': 'tue_fri',
    'сб': 'saturday'
}

# ===== РАБОТА С ЯНДЕКС.ДИСКОМ =====
def get_schedule_from_yandex():
    """Скачивает файл расписания с Яндекс.Диска и возвращает dict."""
    try:
        disk = YandexDisk(YA_DISK_TOKEN)
        content = disk.download_file(FILE_PATH, stream=False)
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"Ошибка загрузки с Яндекс.Диска: {e}")
        return None

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С РАСПИСАНИЕМ =====
def get_day_schedule(schedule, day_key):
    return schedule.get(day_key, {})

def format_schedule(day_name, day_schedule, day_type_key):
    if not day_schedule:
        return f"📭 На {day_name} пар нет."

    times = TIMES[day_type_key]
    lines = [f"📚 **Расписание на {day_name}**", ""]

    if day_type_key == 'monday':
        lines.append("🕗 **Классный час**: 8:00–8:30")
        lines.append("")

    for pair_num in sorted(day_schedule.keys()):
        pair_key = str(pair_num)
        if pair_key not in times:
            continue
        start, end = times[pair_key]
        info = day_schedule[pair_num]
        lines.append(f"**{pair_num} пара** ({start}–{end})")
        lines.append(f"📖 {info.get('subject', '—')}")
        lines.append(f"👨‍🏫 {info.get('teacher', '—')}")
        lines.append(f"🏫 Ауд. {info.get('room', '—')}")
        lines.append("")

    return "\n".join(lines)

def get_day_key_by_name(day_name):
    return DAY_MAP.get(day_name.lower())

# ===== ОБРАБОТЧИКИ КОМАНД =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-расписание группы КСК-26-3\n\n"
        "Команды:\n"
        "/today — расписание на сегодня\n"
        "/tomorrow — расписание на завтра\n"
        "/week — расписание на неделю"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule = get_schedule_from_yandex()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание")
        return

    now = datetime.datetime.now()
    day_key = get_day_key_by_name(now.strftime("%A"))
    if not day_key:
        await update.message.reply_text("Сегодня выходной 🎉")
        return

    day_schedule = get_day_schedule(schedule, day_key)
    day_type = DAY_TYPE.get(day_key, 'tue_fri')
    msg = format_schedule(now.strftime("%A"), day_schedule, day_type)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule = get_schedule_from_yandex()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание")
        return

    now = datetime.datetime.now()
    tomorrow_date = now + datetime.timedelta(days=1)
    day_key = get_day_key_by_name(tomorrow_date.strftime("%A"))
    if not day_key:
        await update.message.reply_text("Завтра выходной 🎉")
        return

    day_schedule = get_day_schedule(schedule, day_key)
    day_type = DAY_TYPE.get(day_key, 'tue_fri')
    msg = format_schedule(tomorrow_date.strftime("%A"), day_schedule, day_type)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule = get_schedule_from_yandex()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание")
        return

    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    msg_lines = ["🗓️ **Расписание на неделю**", ""]

    for day in days_order:
        day_key = get_day_key_by_name(day)
        if not day_key:
            continue
        day_schedule = get_day_schedule(schedule, day_key)
        day_name_ru = {
            'monday': 'ПН',
            'tuesday': 'ВТ',
            'wednesday': 'СР',
            'thursday': 'ЧТ',
            'friday': 'ПТ',
            'saturday': 'СБ'
        }.get(day, day)

        if day_schedule:
            pairs = [f"{p}. {info.get('subject', '—')}" for p, info in sorted(day_schedule.items())]
            msg_lines.append(f"**{day_name_ru}**: " + ", ".join(pairs))
        else:
            msg_lines.append(f"**{day_name_ru}**: пар нет")

    await update.message.reply_text("\n".join(msg_lines), parse_mode='Markdown')

# ===== ЗАПУСК БОТА =====
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("week", week))

    print("✅ Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()
