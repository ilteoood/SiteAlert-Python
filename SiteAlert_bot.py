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
wlcm_msg = "!\nWelcome to @SiteAlert_bot.\nCommands available:\n/ping - Pong\n/show - Print the list of saved sites\n/check - Check new website\n/addme - Notify me on an already registered site\n/removeme - Reverse action\n/register - Register your email\n/registered - Check if you are alredy registered, and show your subscribed sites\n/link - Print the link associated to a website\n/help - Print help message"


def overrideStdout(funcName, msg, credentials, nameSite="", link=""):
    global f
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    if funcName == "show":
        dirs = f.execute("SELECT name FROM SiteAlert").fetchall()
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
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
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


def ck2(m):
    if not m.text.startswith("/"):
        credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
        tb.send_message(m.chat.id, overrideStdout("check", m, credentials, Array[m.chat.id], m.text))
        del Array[m.chat.id]


@tb.message_handler(commands=['addme'])
def addme(m):
    global f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
    if credentials is not None:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        dirs = f.execute(
            "SELECT name FROM SiteAlert EXCEPT SELECT name FROM Registered, Users WHERE Registered.mail = Users.mail AND telegram = \"%d\" ORDER BY name" % (
                m.chat.id)).fetchall()
        for dir in dirs:
            markup.add(dir[0])
        msg = tb.send_message(m.chat.id, "Ok, to...?", reply_markup=markup)
        tb.register_next_step_handler(msg, am)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


def am(m):
    if not m.text.startswith("/"):
        global f, gen_markup
        credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
        try:
            f.execute("INSERT INTO Registered VALUES(\"%s\", \"%s\")" % (m.text, credentials[0]))
            tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=gen_markup)
        except sqlite3.IntegrityError:
            tb.send_message(m.chat.id, "You are already registered to this site!", reply_markup=gen_markup)
        f.commit()
    else:
        tb.send_message(m.chat.id, "Invalid input.")


@tb.message_handler(commands=['removeme'])
def removeme(m):
    global f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
    if credentials is not None:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        dirs = f.execute(
            "SELECT name FROM Registered, Users WHERE Registered.mail = Users.mail AND telegram = \"%d\" ORDER BY name" % (
                m.chat.id)).fetchall()
        for dir in dirs:
            markup.add(dir[0])
        msg = tb.send_message(m.chat.id, "Ok, to...?", reply_markup=markup)
        tb.register_next_step_handler(msg, rm)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


def rm(m):
    if not m.text.startswith("/"):
        global f, gen_markup
        credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
        f.execute("DELETE FROM Registered WHERE mail=\"%s\" AND name=\"%s\"" % (credentials[0], m.text)).fetchall()
        tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=gen_markup)
        f.commit()
    else:
        tb.send_message(m.chat.id, "Invalid input.")


@tb.message_handler(commands=['register'])
def register(m):
    msg = tb.send_message(m.chat.id, "Tell me your e-mail: ")
    tb.register_next_step_handler(msg, reg)


def reg(m):
    try:
        if re.match("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", m.text) is not None:
            f.execute("INSERT INTO Users VALUES(\"%s\",\"%s\")" % (m.text, m.chat.id)).fetchall()
            tb.send_message(m.chat.id, "Action completed successfully!")
            f.commit()
        else:
            tb.send_message(m.chat.id, "Invalid e-mail.")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "User or e-mail already registered.\n")


@tb.message_handler(commands=['registered'])
def registered(m):
    global f
    i = 1
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
    if credentials is not None:
        mymsg = "You have registered this e-mail: " + credentials[0] + "\nYou are registered to:"
        for site in f.execute("SELECT name FROM Registered WHERE mail = \"%s\"" % (credentials[0])).fetchall():
            mymsg = mymsg + "\n" + str(i) + ") " + site[0]
            i += 1
        tb.send_message(m.chat.id, mymsg)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['link'])
def link(m):
    global f
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    dirs = f.execute("SELECT name FROM SiteAlert ORDER BY name").fetchall()
    for dir in dirs:
        markup.add(dir[0])
    msg = tb.send_message(m.chat.id, "Of which site?", reply_markup=markup)
    tb.register_next_step_handler(msg, lk)


def lk(m):
    global gen_markup
    try:
        link = f.execute("SELECT link FROM SiteAlert WHERE name = \"%s\"" % (m.text)).fetchone()
        tb.send_message(m.chat.id, "To " + m.text + " corresponds: " + link[0], reply_markup=gen_markup)
    except Exception:
        tb.send_message(m.chat.id, "Invalid link.", reply_markup=gen_markup)


@tb.message_handler(commands=['cancel'])
def cancel(m):
    global gen_markup
    tb.send_message(m.chat.id, "Ok, I forgot everything!", reply_markup=gen_markup)


@tb.message_handler(commands=['help', 'start'])
def help(m):
    try:
        tb.send_message(m.chat.id, "Hello, " + m.chat.first_name + " " + m.chat.last_name + wlcm_msg)
    except AttributeError:
        tb.send_message(m.chat.id, "Hello, " + m.chat.title + wlcm_msg)
    except TypeError:
        tb.send_message(m.chat.id, "Hello, " + m.chat.first_name + wlcm_msg)


tb.polling(none_stop=True)
