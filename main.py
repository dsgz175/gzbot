TOKEN = "7041636443:AAFgh6qfG6aIbJP2NgQIBe6x_7WG5pFdvFQ"
TIMEZONE = "Europe/Moscow"

import logging

from telegram import Chat, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from datetime import datetime, timedelta
import zoneinfo

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def get_conference_link():
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    email = "test-account-bot@yandex.ru"
    password = "GDJSKG12578gq(#@%&^dg(o*d&@#%olodig6YTiea*topyT"
    driver.get('https://telemost.yandex.ru/')
    driver.find_element(By.XPATH,"/html/body/div/div/div[2]/div[2]/div/div[2]/div/button").click()
    driver.find_element(By.XPATH,"//*[@id='passp-field-login']").send_keys(email)
    driver.find_element(By.XPATH,"//*[@id='passp:sign-in']").click()
    driver.find_element(By.XPATH,"//*[@id='passp-field-passwd']").send_keys(password)
    driver.find_element(By.XPATH,"//*[@id='passp:sign-in']").click()
    time.sleep(3)
    url = driver.current_url
    driver.find_element(By.XPATH,"/html/body/div/div/div[2]/div[2]/div/div[3]/div/button").click()
    driver.quit()
    return(url)

def get_users(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.bot_data.setdefault("users", {})

def get_timezone(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.chat_data.setdefault("timezone", "Europe/Moscow")

def get_meetings(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.chat_data.setdefault("meetings", {})

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 0:
        await update.effective_message.reply_text("Ошибка ввода. Команда /start не трубует аргументов.")
        return
    if update.effective_chat.type == Chat.PRIVATE:
        users = get_users(context)
        if update.effective_chat.username in users:
            await update.effective_message.reply_text("Чат-бот уже знает вас.\n")
            return
        users[update.effective_chat.username] = update.effective_chat.id
        await update.effective_message.reply_text("Теперь чат-бот может уведомлять вас о встречах.")
    else:
        await update.effective_message.reply_text("Используйте /help, чтобы получить список команд.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == Chat.PRIVATE:
        return
    if len(context.args) != 0:
        await update.effective_message.reply_text("Ошибка ввода. Команда /help не трубует аргументов.")
        return
    await update.effective_message.reply_text(
        "/start - Начать работу.\n"
        "/help - Получить список команд.\n"
        "/get_timezone - Получить часовой пояс.\n"
        "/set_timezone <часовой пояс> - Установить часовой пояс (см. доступные пояса: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).\n"
        "/get_meetings - Получить список встреч.\n"
        "/create_meeting <ID> <название> <дд.мм.гг или today/сегодня> <чч:мм> <опц. участники...> - Создать втречу.\n"
        "/remove_meetings <список ID...> - Отменить встречу."
        # "/get_members <ID> - Получить список участников встречи.\n"
        # "/add_members <ID> <участники...> - Добавить участников на встречу.\n"
        # "/remove_members <ID> <участники...> - Убрать участников со встречи."
    )

async def get_timezone_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == Chat.PRIVATE:
        return
    if len(context.args) != 0:
        await update.effective_message.reply_text("Ошибка ввода. Команда /get_timezone не трубует аргументов.")
        return
    timezone = get_timezone(context)
    await update.effective_message.reply_text(timezone)

async def set_timezone_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == Chat.PRIVATE:
        return
    if len(context.args) != 1:
        await update.effective_message.reply_text("Ошибка ввода. Используйте /set_timezone <часовой пояс>.")
        return
    timezone = context.args[0]
    if timezone not in zoneinfo.available_timezones():
        await update.effective_message.reply_text("Неизвестный часовой пояс.")
        return
    old_timezone = get_timezone(context)
    if timezone == timezone:
        await update.effective_message.reply_text("Старый часовой пояс совпадает с новым.")
        return
    context.chat_data["timezone"] = timezone
    await update.effective_message.reply_text(f"Часовой пояс изменён с {old_timezone} на {timezone}.")

async def get_meetings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == Chat.PRIVATE:
        return
    if len(context.args) != 0:
        await update.effective_message.reply_text("Ошибка ввода. Команда /get_meetings не трубует аргументов.")
        return
    meetings = get_meetings(context)
    if len(meetings) == 0:
        await update.effective_message.reply_text("Список пуст.")
        return
    reply = f"Список встреч ({len(meetings)}):\n"
    for i, (meeting_id, meeting) in enumerate(meetings.items()):
        date_time = meeting["date_time"].strftime("%d.%m.%y %H:%M")
        reply += f"{i + 1}. {meeting_id} - {meeting['name']} - {date_time}\n"
    reply = reply[:-1]
    await update.effective_message.reply_text(reply)

async def you_are_added_notif(context: ContextTypes.DEFAULT_TYPE) -> None:
    (id_, name) = context.job.data
    await context.bot.send_message(context.job.chat_id, text=f"Вы были добавлены на встречу {name} ({id_}).")

async def less_than_30_left_notif(context: ContextTypes.DEFAULT_TYPE) -> None:
    (private, data) = context.job.data
    if not private:
        (id_, link) = data
        meeting = get_meetings(context)[id_]
        name = meeting["name"]
        members = meeting["members"]
        users = get_users(context)
        for member in members:
            chat_id = users[member]
            context.job_queue.run_once(less_than_30_left_notif, datetime.now(zoneinfo.ZoneInfo(get_timezone(context))), chat_id=chat_id, name=f"{chat_id}/{id_}/{member}/2", data=(True, (id_, name, link)))
        await context.bot.send_message(context.job.chat_id, text=f"До начала встречи {name} ({id_}) осталось меньше 30 минут.")
    else:
        (id_, name, link) = data
        await context.bot.send_message(context.job.chat_id, text=f"До начала встречи {name} ({id_}) осталось меньше 30 минут.\nСсылка для входа: {link}")

async def less_than_5_left_notif(context: ContextTypes.DEFAULT_TYPE) -> None:
    (private, data) = context.job.data
    if not private:
        (id_, link) = data
        meeting = get_meetings(context)[id_]
        name = meeting["name"]
        members = meeting["members"]
        users = get_users(context)
        for member in members:
            chat_id = users[member]
            context.job_queue.run_once(less_than_5_left_notif, datetime.now(zoneinfo.ZoneInfo(get_timezone(context))), chat_id=chat_id, name=f"{chat_id}/{id_}/{member}/1", data=(True, (id_, name, link)))
        await context.bot.send_message(context.job.chat_id, text=f"До начала встречи {name} ({id_}) осталось меньше 5 минут.")
    else:
        (id_, name, link) = data
        await context.bot.send_message(context.job.chat_id, text=f"До начала встречи {name} ({id_}) осталось меньше 5 минут.\nСсылка для входа: {link}")

async def meeting_started_notif(context: ContextTypes.DEFAULT_TYPE) -> None:
    (private, data) = context.job.data
    if not private:
        (id_, link) = data
        meetings = get_meetings(context) 
        meeting = meetings[id_]
        name = meeting["name"]
        members = meeting["members"]
        users = get_users(context)
        for member in members:
            chat_id = users[member]
            context.job_queue.run_once(meeting_started_notif, datetime.now(zoneinfo.ZoneInfo(get_timezone(context))), chat_id=chat_id, name=f"{chat_id}/{id_}/{member}/0", data=(True, (id_, name, link)))
        meetings.pop(id_)
        await context.bot.send_message(context.job.chat_id, text=f"Встреча {name} ({id_}) уже началась.")
    else:
        (id_, name, link) = data
        await context.bot.send_message(context.job.chat_id, text=f"Встреча {name} ({id_}) уже началась.\nСсылка для входа: {link}")

async def about_30_left_notif(context: ContextTypes.DEFAULT_TYPE) -> None:
    id_ = context.job.data
    meeting = get_meetings(context)[id_]
    name = meeting["name"]
    members = meeting["members"]
    users = get_users(context)
    link = get_conference_link()
    context.job_queue.run_once(less_than_30_left_notif, datetime.now(zoneinfo.ZoneInfo(get_timezone(context))), chat_id=chat_id, name=f"{chat_id}/{id_}/2", data=(False, (id_, link)))
    context.job_queue.run_once(less_than_5_left_notif, date_time - timedelta(minutes=5) , chat_id=chat_id, name=f"{chat_id}/{id_}/1", data=(False, (id_, link)))
    context.job_queue.run_once(meeting_started_notif, date_time, chat_id=chat_id, name=f"{chat_id}/{id_}/0", data=(False, (id_, link)))

async def create_meeting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == Chat.PRIVATE:
        return
    if len(context.args) < 4:
        await update.effective_message.reply_text("Ошибка ввода. Используйте /create_meeting <ID> <название> <дд.мм.гг или today/сегодня> <чч:мм> <опц. участники...>.")
        return
    id_ = context.args[0]
    meetings = get_meetings(context)
    if id_ in meetings:
        await update.effective_message.reply_text("Встреча с таким ID уже существует.")
        return
    name = context.args[1].replace('_', ' ')
    date = context.args[2]
    time = context.args[3]
    now = datetime.now(zoneinfo.ZoneInfo(get_timezone(context)))
    try:
        if date not in ["today", "сегодня"]:
            date_time = datetime.strptime(f"{date} {time}", "%d.%m.%y %H:%M")
        else:
            date_time = datetime.strptime(time, "%H:%M")
            date_time = date_time.replace(day=now.day, month=now.month, year=now.year)
    except ValueError:
        await update.effective_message.reply_text("Направильный формат даты и времени. Используйте <дд.мм.гг или today/сегодня> <чч:мм>.")
        return
    date_time = date_time.replace(tzinfo=now.tzinfo)
    if date_time <= now:
        await update.effective_message.reply_text("Указанные дата и время меньше или совпадают с текущем временем.")
        return
    members_to_add = set()
    if len(context.args) > 4:
        members_to_add = set(context.args[4:])
    for member in members_to_add:
        if member[0] == '@' and len(member) > 1:
            members_to_add.discard(member)
            members_to_add.add(member[1:])
    users = get_users(context)
    unknown_users = set()
    for member in members_to_add:
        if member not in users:
            unknown_users.add(member)
    for member in unknown_users:
        members_to_add.remove(member)
    meetings = get_meetings(context)
    meetings[id_] = {"name": name, "date_time": date_time, "members": members_to_add}
    for member in members_to_add:
        chat_id = users[member]
        context.job_queue.run_once(you_are_added_notif, datetime.now(zoneinfo.ZoneInfo(get_timezone(context))), chat_id=chat_id, name=f"{chat_id}/{id_}/{member}", data=(id_, name))
    left = (date_time - now).total_seconds()
    chat_id = update.effective_chat.id
    if left <= 300: # 5 минут
        link = get_conference_link()
        context.job_queue.run_once(less_than_5_left_notif, datetime.now(zoneinfo.ZoneInfo(get_timezone(context))), chat_id=chat_id, name=f"{chat_id}/{id_}/1", data=(False, (id_, link)))
        context.job_queue.run_once(meeting_started_notif, date_time, chat_id=chat_id, name=f"{chat_id}/{id_}/0", data=(False, (id_, link)))
    elif left <= 1800: # 30 минут
        link = get_conference_link()
        context.job_queue.run_once(less_than_30_left_notif, datetime.now(zoneinfo.ZoneInfo(get_timezone(context))), chat_id=chat_id, name=f"{chat_id}/{id_}/2", data=(False, (id_, link)))
        context.job_queue.run_once(less_than_5_left_notif, date_time - timedelta(minutes=5) , chat_id=chat_id, name=f"{chat_id}/{id_}/1", data=(False, (id_, link)))
        context.job_queue.run_once(meeting_started_notif, date_time, chat_id=chat_id, name=f"{chat_id}/{id_}/0", data=(False, (id_, link)))
    else:
        context.job_queue.run_once(about_30_left_notif, date_time - timedelta(minutes=30), chat_id=chat_id, name=f"{chat_id}/{id_}", data=id_)
    reply = ""
    if len(unknown_users) != 0:
        reply = "Некоторые пользователи не были добавлены, т.к. они неизвестны чат-боту. Им необходимо написать /start чат-боту в личных сообщениях, чтобы тот мог отправлять уведомления о предстоящей встрече:\n"
        for i, user in enumerate(unknown_users):
            reply += f"{i + 1}. @{user}\n"
    minutes, seconds = divmod(left, 60)
    hours, minutes = divmod(minutes, 60)
    reply += f"До втречи осталось {int(hours)} часов {int(minutes)} минут {int(seconds)} секунд."
    await update.effective_message.reply_text(reply)

async def you_are_removed_notif(context: ContextTypes.DEFAULT_TYPE) -> None:
    (id_, name) = context.job.data
    await context.bot.send_message(context.job.chat_id, text=f"Вы були удалены из встречи {name} ({id_}).")

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    jobs = context.job_queue.get_jobs_by_name(name)
    if not jobs:
        return
    for job in jobs:
        job.schedule_removal()

async def remove_meetings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == Chat.PRIVATE:
        return
    if len(context.args) < 1:
        await update.effective_message.reply_text("Ошибка ввода. Используйте /remove_meetings <список ID...>.")
        return 
    meetings = get_meetings(context)
    unknown_ids = set()
    for id_ in context.args:
        if id_ not in meetings:
            unknown_ids.add(id_)
            continue
        meeting = meetings[id_]
        name = meeting["name"]
        members = meeting["members"]
        users = get_users(context)
        for member in members:
            chat_id = users[member]
            context.job_queue.run_once(you_are_removed_notif, datetime.now(zoneinfo.ZoneInfo(get_timezone(context))), chat_id=chat_id, name=f"{chat_id}/{id_}/{member}", data=(id_, name))
        remove_job_if_exists(f"{update.effective_chat.id}/{id_}", context)
        remove_job_if_exists(f"{update.effective_chat.id}/{id_}/0", context)
        remove_job_if_exists(f"{update.effective_chat.id}/{id_}/1", context)
        remove_job_if_exists(f"{update.effective_chat.id}/{id_}/2", context)
        meetings.pop(id_)
    if len(unknown_ids) != 0:
        reply = f"Некоторые встречи не найдены ({len(unknown_ids)}):\n"
        for i, id_ in enumerate(unknown_ids):
            reply += f"{i + 1}. {id_}\n"
        await update.effective_message.reply_text(reply)
        return
    await update.effective_message.reply_text(f"Встречи успешно удалены ({len(context.args) - len(unknown_ids)}).")

def main() -> None:
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)

    application = Application.builder().token(TOKEN).build()

    commands = {
        "start": start_cmd,
        "help": help_cmd,
        "get_timezone": get_timezone_cmd,
        "set_timezone": set_timezone_cmd,
        "get_meetings": get_meetings_cmd,
        "create_meeting": create_meeting_cmd,
        "remove_meetings": remove_meetings_cmd,
    }
    for command, function in commands.items():
        application.add_handler(CommandHandler(command, function))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()