import os
import datetime
import json
import logging
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
# ===== НАСТРОЙКИ =====
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ Ошибка: не задан TELEGRAM_TOKEN")
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

DAY_NAME_RU = {
    'monday': 'ПН',
    'tuesday': 'ВТ',
    'wednesday': 'СР',
    'thursday': 'ЧТ',
    'friday': 'ПТ',
    'saturday': 'СБ'
}

DAY_NAME_FULL = {
    'monday': 'Понедельник',
    'tuesday': 'Вторник',
    'wednesday': 'Среда',
    'thursday': 'Четверг',
    'friday': 'Пятница',
    'saturday': 'Суббота'
}

# ===== РАБОТА С РАСПИСАНИЕМ (локальный JSON) =====
def get_schedule():
    """Читает расписание из локального файла schedule.json."""
    try:
        with open('schedule.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл schedule.json не найден")
        return None
    except json.JSONDecodeError:
        print("❌ Ошибка в формате schedule.json")
        return None

def get_day_schedule(schedule, day_key):
    """Возвращает расписание для конкретного дня."""
    if not schedule:
        return {}
    return schedule.get(day_key, {})

def format_schedule(day_name, day_schedule, day_type_key):
    """Форматирует расписание для отправки в Telegram."""
    if not day_schedule:
        return f"📭 На {DAY_NAME_FULL.get(day_name, day_name)} пар нет."

    times = TIMES[day_type_key]
    lines = [f"📚 **Расписание на {DAY_NAME_FULL.get(day_name, day_name)}**", ""]

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
    """Преобразует английское название дня в ключ (пн, вт, ...)."""
    return DAY_MAP.get(day_name.lower())

# ===== ОБРАБОТЧИКИ КОМАНД =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение."""
    await update.message.reply_text(
        " Привет. Я пидорас вашей группы\n\n"
        "📌 Команды:\n"
        "/today — расписание на сегодня\n"
        "/tomorrow — расписание на завтра\n"
        "/week — расписание на неделю\n"
        "/day ПН — расписание на указанный день (пн, вт, ср, чт, пт, сб)"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расписание на сегодня."""
    schedule = get_schedule()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание. Проверь файл schedule.json")
        return

    now = datetime.datetime.now()
    day_name = now.strftime("%A").lower()
    day_key = get_day_key_by_name(day_name)

    if not day_key:
        await update.message.reply_text("Сегодня выходной 🎉")
        return

    day_schedule = get_day_schedule(schedule, day_key)
    day_type = DAY_TYPE.get(day_key, 'tue_fri')
    msg = format_schedule(day_name, day_schedule, day_type)

    await update.message.reply_text(msg, parse_mode='Markdown')

async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расписание на завтра."""
    schedule = get_schedule()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание. Проверь файл schedule.json")
        return

    now = datetime.datetime.now()
    tomorrow_date = now + datetime.timedelta(days=1)
    day_name = tomorrow_date.strftime("%A").lower()
    day_key = get_day_key_by_name(day_name)

    if not day_key:
        await update.message.reply_text("Завтра выходной 🎉")
        return

    day_schedule = get_day_schedule(schedule, day_key)
    day_type = DAY_TYPE.get(day_key, 'tue_fri')
    msg = format_schedule(day_name, day_schedule, day_type)

    await update.message.reply_text(msg, parse_mode='Markdown')

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает краткое расписание на всю неделю."""
    schedule = get_schedule()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание. Проверь файл schedule.json")
        return

    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    msg_lines = ["🗓️ **Расписание на неделю**", ""]

    for day in days_order:
        day_key = get_day_key_by_name(day)
        if not day_key:
            continue

        day_schedule = get_day_schedule(schedule, day_key)
        day_short = DAY_NAME_RU.get(day, day)

        if day_schedule:
            pairs = []
            for p, info in sorted(day_schedule.items()):
                pairs.append(f"{p}. {info.get('subject', '—')}")
            msg_lines.append(f"**{day_short}**: " + ", ".join(pairs))
        else:
            msg_lines.append(f"**{day_short}**: пар нет")

    await update.message.reply_text("\n".join(msg_lines), parse_mode='Markdown')

async def day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расписание на указанный день (аргумент: пн, вт, ср, ...)."""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажи день недели.\n"
            "Пример: `/day пн` или `/day понедельник`",
            parse_mode='Markdown'
        )
        return

    user_input = context.args[0].lower().strip()

    # Сопоставляем ввод пользователя с ключами
    day_mapping = {
        'пн': 'пн', 'понедельник': 'пн',
        'вт': 'вт', 'вторник': 'вт',
        'ср': 'ср', 'среда': 'ср',
        'чт': 'чт', 'четверг': 'чт',
        'пт': 'пт', 'пятница': 'пт',
        'сб': 'сб', 'суббота': 'сб'
    }

    day_key = day_mapping.get(user_input)
    if not day_key:
        await update.message.reply_text(
            "❌ Неверный день. Доступные варианты: пн, вт, ср, чт, пт, сб"
        )
        return

    schedule = get_schedule()
    if not schedule:
        await update.message.reply_text("❌ Не удалось загрузить расписание. Проверь файл schedule.json")
        return

    day_schedule = get_day_schedule(schedule, day_key)
    day_type = DAY_TYPE.get(day_key, 'tue_fri')

    # Находим английское название дня для форматирования
    day_name_eng = None
    for eng, ru in DAY_MAP.items():
        if ru == day_key:
            day_name_eng = eng
            break

    msg = format_schedule(day_name_eng or day_key, day_schedule, day_type)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def set_commands(app):
    commands = [
        BotCommand("start", "Показать приветствие и список команд"),
        BotCommand("today", "Расписание на сегодня"),
        BotCommand("tomorrow", "Расписание на завтра"),
        BotCommand("week", "Расписание на неделю"),
        BotCommand("day", "Расписание на конкретный день (пн, вт, ср...)")
    ]
    await app.bot.set_my_commands(commands)
# ===== ЗАПУСК БОТА =====
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("day", day))

    print("✅ Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()
