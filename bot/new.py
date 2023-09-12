
import os

from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from datetime import datetime, timedelta
from dotenv import load_dotenv
from course import Course, read_msg, load_cache, save_cache
from threading import Thread, Timer
from time import sleep
from schedule import every, run_pending, clear, get_jobs, repeat, CancelJob
from typing import List

load_dotenv()

ADMINS = os.getenv("ADMINS")
API_TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POST_DELTA = int(os.getenv("POST_DELTA"))
DELETE_DELTA = int(os.getenv("DELETE_DELTA"))

bot = TeleBot(API_TOKEN, parse_mode=None)
test = 1

class Single:
    courses = []
    leap_mod = True
    msg = 0
    
    def __init__(self,courses =[],leap_mod=True,msg =()):
        self.courses = courses
        self.leap_mod = leap_mod
        self.msg = msg

try:
    main = Single()
    for course in load_cache()['courses']:
        main.courses.append(Course(**course))    
except Exception as e:
    print(e)
    print('cant read cache')
    main = Single()

def notify(task: Course):
    global test
    try:
        btn = InlineKeyboardMarkup()
        btn.add(InlineKeyboardButton("Посилання на пару", task.get_link()))
        main.msg = bot.send_message(chat_id=CHANNEL_ID,
                         text=task,
                         reply_markup=btn).message_id
    except Exception as e:
        print(e)
        main.msg = bot.send_message(chat_id=CHANNEL_ID, text=f'{task}\n{task.get_link()}').message_id
    try:
        t = Timer(DELETE_DELTA*60, delete_last)  
        t.start()
    except: pass
    

def delete_last():
    try:
        bot.delete_message(CHANNEL_ID,main.msg)
    except Exception as e:
        print("---DELETE---")
        print(e)

def init_schedule(course_list: List[Course]):
    is_odd_week = int((int(datetime.today().strftime("%V")) + 0) % 2 and main.leap_mod)
    print('UPD')
    clear('daily')
    for course in course_list:
        if datetime.today().weekday() == course.day and (course.leap == is_odd_week or course.leap == 2):
            every().day.at((datetime.strptime(course.time,"%H:%M") - timedelta(minutes=POST_DELTA)).strftime("%H:%M"),
                           tz='Europe/Kyiv').do(notify, task=course).tag('daily')
    save_cache(main.__dict__)
    main.courses = course_list


def user_filter(message: Message):
    return str(message.from_user.id) in ADMINS


@bot.message_handler(commands=['timetable'], func=user_filter)
def get_table(message):
    msg = ''
    for course in main.courses:
        msg += (course.full() + '\n')
    bot.reply_to(message, msg)


@bot.message_handler(commands=['table'], func=user_filter)
def get_table(message):
    msg = ''
    for course in main.courses:
        if datetime.today().weekday() == course.day:
            msg += (str(course) + '\n')
    bot.reply_to(message, msg)


@bot.message_handler(commands=['flip'], func=user_filter)
def flip_leap(message):
    main.leap = not main.leap_mod
    init_schedule(main.courses)
    bot.reply_to(message, 'Інвертовано верхній/нижній тижні')


@bot.message_handler(func=user_filter)
def update_table(message):
    if len(message.text) > 100:
        try:
            main.courses = read_msg(message.text)
            bot.reply_to(message, 'Оновлено')
            init_schedule(main.courses)
        except Exception as e:
            bot.reply_to(message, f'Помилка читання розкладу\n{e}')


@bot.edited_message_handler(func=user_filter)
def update_edits(message):
    print('edit:', end=' ')
    update_table(message)


@repeat(every().day.at('03:00', tz='Europe/Kyiv'))
def reset():
    clear('daily')
    init_schedule(main.courses)


if __name__ == "__main__":
    bot_polling = Thread(target=bot.infinity_polling)
    bot_polling.start()
    while True:
        run_pending()
        sleep(1)
