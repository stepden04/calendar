from telebot import TeleBot
from telebot.types import InlineKeyboardButton,InlineKeyboardMarkup
from table import Course, read_table
from datetime import datetime, timedelta
from schedule import every, run_pending, clear, get_jobs, repeat
import schedule
from time import sleep
from threading import Thread
from cfg import API_TOKEN, LOG_PATH, USERS_PATH,TIMEDELTA
import logging


bot = TeleBot(API_TOKEN, parse_mode=None)
subscriptions = []


try:
    logging.basicConfig(filename=LOG_PATH,
                        filemode='w',
                        encoding='utf-16',
                        level=logging.INFO)
    log = logging.getLogger('systemd-log')
    log.addHandler(JournalHandler())
    log.setLevel(logging.DEBUG)
except:
    log = logging.getLogger()
    log.warning('cant access systemd logs')


def notify(task: Course):
    for id in set(subscriptions):
        try:
            btn = InlineKeyboardMarkup()
            btn.add(InlineKeyboardButton("Посилання на пару", task.get_link()))
            bot.send_message(chat_id=id,
                             text=task,
                             reply_markup=btn)
        except:
            bot.send_message(chat_id=id, text=f'{task}\n{task.get_link()}')
    log.info(f'sent {task} to {subscriptions}')


@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    global subscriptions
    bot.reply_to(message, "Added to a notification list")
    if not subscriptions.count(message.chat.id):
        with open(USERS_PATH, 'a') as file:
            file.write(
                f'{message.chat.id}:{message.chat.first_name} {message.chat.last_name} / {message.chat.username}\n')
        subscriptions.append(message.chat.id)
    subscriptions = list(set(subscriptions))
    log.info(f'Added {message.chat.username} : {message.chat.id}')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Відправте /subscribe щоб отримувати сповіщення")


@bot.message_handler(commands=['timetable'])
def send_timetable(message):
    bot.reply_to(message, print_jobs('this_day'))


@repeat(every().day.at("00:00"))
def update():
    global subscriptions
    #
    clear(tag='this_day')
    jobs = []
    #
    log.info(f'UPDATE : {datetime.now().strftime(r"%d-%m - %H:%M:%S")}')

    with open(USERS_PATH) as file:
        for row in file:
            subscriptions.append(int(row.split(" ")[0].split(":")[0]))
            
    subscriptions = list(set(subscriptions))
    
    log.info(f'SUBS : {subscriptions}')

    try:
        jobs = read_table()
    except:
        print('Cant source timetable file')

    is_odd_week = (int(datetime.today().strftime("%V")) + 0) % 2

    for job in jobs:
        if job.day == datetime.today().strftime(r"%a") and (job.leap == is_odd_week or job.leap == 2):
            print(job)
            exec_time = (job.time - timedelta(minutes=TIMEDELTA)).strftime("%H:%M")
            every().day.at(exec_time, 'Europe/Tallinn').do(notify, task=job).tag('this_day')
            
    print_jobs('this_day', '[TASK] :')
    print(subscriptions)


def print_jobs(task_tag: str, log_tag: str = ''):
    msg = ""
    for job in get_jobs(task_tag):
        log.warning(
            f"{log_tag} {str(job.job_func.keywords['task'])}")
        msg += f"{log_tag}{str(job.job_func.keywords['task'])}\n"
    return msg


if __name__ == '__main__':
    run_pending()
    update()
    bot_polling = Thread(target=bot.infinity_polling)
    bot_polling.start()
    while True:
        run_pending()
        sleep(1)
