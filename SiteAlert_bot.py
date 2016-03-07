__author__ = 'iLTeoooD'

import sys
import sqlite3
import os
import re
from io import StringIO
from os.path import expanduser

import telebot
from telebot import types

import SiteAlert

TOKEN = 'YOUR TOKEN HERE'
db = expanduser("~") + os.sep + "SiteAlert.db"
leng = ""
f = sqlite3.connect(db, check_same_thread=False)
Array = {}
gen_markup = types.ReplyKeyboardHide(selective=False)
wlcm_msg = "!\nWelcome to @SiteAlert_bot.\nCommands available:\n/ping - Pong\n/show - Print the list of saved sites\n/check - Check new website\n/addme - Notify me on an already registered site\n/removeme - Reverse action\n/register - Register your email\n/registered - Check if you are alredy registered, and show your subscribed sites\n/unregister - Delete your registration\n/link - Print the link associated to a website\n/mailoff - Disable mail notification\n/mailon - Reverse action\n/telegramoff - Disable telegram notification\n/telegramon - Reverse action\n/help - Print help message"


def overrideStdout(funcName, msg, credentials, nameSite="", link=""):
    global f
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    if funcName == "show":
        dirs = f.execute("SELECT name FROM SiteAlert ORDER BY name COLLATE NOCASE").fetchall()
        leng = len(dirs)
        SiteAlert.displaySites(dirs, leng)
    elif funcName == "check":
        SiteAlert.addSite(f, nameSite, link, credentials[0], msg.chat.id)
    sys.stdout = old_stdout
    return result.getvalue()


tb = telebot.TeleBot(TOKEN)


@tb.message_handler(commands=['ping'])
def ping(m):
    tb.send_message(m.chat.id, "Pong")


@tb.message_handler(commands=['show'])
def show(m):
    tb.send_message(m.chat.id, overrideStdout("show", m, ""))


@tb.message_handler(commands=['check'])
def check(m):
    global f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,)).fetchone()
    if credentials is not None:
        msg = tb.send_message(m.chat.id, "Ok, how we should call it?")
        tb.register_next_step_handler(msg, ck1)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


def ck1(m):
    if not m.text.startswith("/"):
        Array[m.chat.id] = m.text
        msg = tb.send_message(m.chat.id, "Ok, got it.\nNow send the link of the website:")
        tb.register_next_step_handler(msg, ck2)
    else:
        tb.send_message(m.chat.id, "Invalid name.")


def ck2(m):
    if not m.text.startswith("/"):
        credentials = f.execute("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,)).fetchone()
        tb.send_message(m.chat.id, overrideStdout("check", m, credentials, Array[m.chat.id], m.text))
        del Array[m.chat.id]
    else:
        tb.send_message(m.chat.id, "Invalid name.")


@tb.message_handler(commands=['addme'])
def addme(m):
    global f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,)).fetchone()
    if credentials is not None:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        dirs = f.execute(
            "SELECT name FROM SiteAlert EXCEPT SELECT name FROM Registered, Users WHERE Registered.mail = Users.mail AND telegram = ? ORDER BY name COLLATE NOCASE",
            (m.chat.id,)).fetchall()
        for dir in dirs:
            markup.add(dir[0])
        msg = tb.send_message(m.chat.id, "Ok, to...?", reply_markup=markup)
        tb.register_next_step_handler(msg, am)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


def am(m):
    global f, gen_markup
    dirs = f.execute("SELECT * FROM SiteAlert WHERE name=?", (m.text,)).fetchall()
    if len(dirs) > 0:
        credentials = f.execute("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,)).fetchone()
        try:
            f.execute("INSERT INTO Registered VALUES(?, ?)", (m.text, credentials[0]))
            tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=gen_markup)
        except sqlite3.IntegrityError:
            tb.send_message(m.chat.id, "You are already registered to this site!", reply_markup=gen_markup)
        f.commit()
    elif not m.text.startswith("/"):
        tb.send_message(m.chat.id, "Invalid input.")


@tb.message_handler(commands=['removeme'])
def removeme(m):
    global f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,)).fetchone()
    if credentials is not None:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        dirs = f.execute(
            "SELECT name FROM Registered, Users WHERE Registered.mail = Users.mail AND telegram = ? ORDER BY name COLLATE NOCASE",
            (m.chat.id,)).fetchall()
        for dir in dirs:
            markup.add(dir[0])
        msg = tb.send_message(m.chat.id, "Ok, from...?", reply_markup=markup)
        tb.register_next_step_handler(msg, rm)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


def rm(m):
    global f, gen_markup
    dirs = f.execute("SELECT * FROM SiteAlert WHERE name=?", (m.text,)).fetchall()
    if len(dirs) > 0:
        credentials = f.execute("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,)).fetchone()
        f.execute("DELETE FROM Registered WHERE mail=? AND name=?", (credentials[0], m.text)).fetchall()
        tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=gen_markup)
        f.commit()
    elif not m.text.startswith("/"):
        tb.send_message(m.chat.id, "Invalid input.")


@tb.message_handler(commands=['register'])
def register(m):
    global f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,)).fetchone()
    if credentials is None:
        msg = tb.send_message(m.chat.id, "Tell me your e-mail: ")
        tb.register_next_step_handler(msg, reg)
    else:
        tb.send_message(m.chat.id, "User already registered.\nUse /registered")


def reg(m):
    global f
    if re.match("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", m.text) is not None:
        f.execute("INSERT INTO Users VALUES(?,?,'True','True')", (m.text, m.chat.id)).fetchall()
        tb.send_message(m.chat.id, "Action completed successfully!")
        f.commit()
    else:
        tb.send_message(m.chat.id, "Invalid e-mail.")


@tb.message_handler(commands=['registered'])
def registered(m):
    global f
    i = 1
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,)).fetchone()
    if credentials is not None:
        mymsg = "You have registered this e-mail: " + credentials[0] + "\nYour notification status is:\nE-mail: "
        status = f.execute("SELECT mailnotification FROM Users WHERE mail = ?", (credentials[0],)).fetchone()
        mymsg += status[0] + "\nTelegram: "
        status = f.execute("SELECT telegramnotification FROM Users WHERE mail = ?", (credentials[0],)).fetchone()
        mymsg += status[0] + "\nYou are registered to:"
        for site in f.execute("SELECT name FROM Registered WHERE mail = ?", (credentials[0],)).fetchall():
            mymsg = mymsg + "\n" + str(i) + ") " + site[0]
            i += 1
        tb.send_message(m.chat.id, mymsg)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['link'])
def link(m):
    global f
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    dirs = f.execute("SELECT name FROM SiteAlert ORDER BY name COLLATE NOCASE").fetchall()
    for dir in dirs:
        markup.add(dir[0])
    msg = tb.send_message(m.chat.id, "Of which site?", reply_markup=markup)
    tb.register_next_step_handler(msg, lk)


def lk(m):
    global gen_markup
    try:
        link = f.execute("SELECT link FROM SiteAlert WHERE name = ?", (m.text,)).fetchone()
        tb.send_message(m.chat.id, "To " + m.text + " corresponds: " + link[0], reply_markup=gen_markup)
    except Exception:
        tb.send_message(m.chat.id, "Invalid link.", reply_markup=gen_markup)


@tb.message_handler(commands=['unregister'])
def unregister(m):
    global gen_markup, f
    mail = f.execute("SELECT mail FROM Users WHERE telegram = ?", (m.chat.id,)).fetchone()
    if mail is not None:
        f.execute("DELETE FROM Users WHERE mail = ?", (mail[0],))
        f.execute("DELETE FROM Registered WHERE mail = ?", (mail[0],))
        f.commit()
        tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=gen_markup)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['mailoff'])
def mailoff(m):
    global f
    try:
        f.execute("UPDATE Users SET mailnotification = 'False' WHERE telegram = ?", (m.chat.id,))
        f.commit()
        tb.send_message(m.chat.id, "Action completed successfully!")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['mailon'])
def mailon(m):
    global f
    try:
        f.execute("UPDATE Users SET mailnotification = 'True' WHERE telegram = ?", (m.chat.id,))
        f.commit()
        tb.send_message(m.chat.id, "Action completed successfully!")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['telegramoff'])
def telegramoff(m):
    global f
    try:
        f.execute("UPDATE Users SET telegramnotification = 'False' WHERE telegram = ?", (m.chat.id,))
        f.commit()
        tb.send_message(m.chat.id, "Action completed successfully!")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['telegramon'])
def telegramon(m):
    global f
    try:
        f.execute("UPDATE Users SET telegramnotification = 'True' WHERE telegram = ?", (m.chat.id,))
        f.commit()
        tb.send_message(m.chat.id, "Action completed successfully!")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['cancel'])
def cancel(m):
    global gen_markup
    tb.send_message(m.chat.id, "Ok, I forgot everything!", reply_markup=gen_markup)


@tb.message_handler(commands=['help', 'start'])
def help(m):
    if m.chat.first_name is not None:
        if m.chat.last_name is not None:
            tb.send_message(m.chat.id, "Hello, " + m.chat.first_name + " " + m.chat.last_name + wlcm_msg)
        else:
            tb.send_message(m.chat.id, "Hello, " + m.chat.first_name + wlcm_msg)
    else:
        tb.send_message(m.chat.id, "Hello, " + m.chat.title + wlcm_msg)


tb.polling(none_stop=True)
