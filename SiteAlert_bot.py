__author__ = 'ilteoood'

import sys
import sqlite3
import os
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


def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            global Array, Matrix, f
            credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
            markup = types.ReplyKeyboardHide(selective=False)
            if not m.text.startswith("/") and m.chat.id in Array:
                if credentials is not None:
                    if Array[m.chat.id] == "check":
                        if not (m.chat.id, 0) in Array or Array[m.chat.id, 0] == "":
                            Array[m.chat.id, 0] = m.text
                            tb.send_message(m.chat.id, "Ok, got it.\nNow send the link of the website:")
                        else:
                            tb.send_message(m.chat.id,
                                            overrideStdout("check", m, credentials, Array[m.chat.id, 0], m.text))
                            Array[m.chat.id] = ""
                            Array[m.chat.id, 0] = ""
                    elif Array[m.chat.id] == "addme":
                        try:
                            f.execute(
                                "INSERT INTO Registered VALUES(\"%s\", \"%s\",\"%s\")" % (
                                    m.text, credentials[0], m.chat.id))
                            tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=markup)
                        except sqlite3.IntegrityError:
                            tb.send_message(m.chat.id, "You are already registered to this site!", reply_markup=markup)
                        Array[m.chat.id] = ""
                    elif Array[m.chat.id] == "removeme":
                        f.execute("DELETE FROM Registered WHERE mail=\"%s\" AND name=\"%s\"" % (
                            credentials[0], m.text)).fetchall()
                        tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=markup)
                        Array[m.chat.id] = ""
                    elif Array[m.chat.id] == "register":
                        f.execute("UPDATE Users SET mail = \"%s\" WHERE telegram =\"%s\"" % (m.text, m.chat.id))
                        tb.send_message(m.chat.id, "Action completed successfully!")
                        Array[m.chat.id] = ""
                    f.commit()
                else:
                    if m.chat.id in Array:
                        if Array[m.chat.id] == "register":
                            if not m.text.startswith("/"):
                                try:
                                    f.execute(
                                        "INSERT INTO Users VALUES(\"%s\",\"%s\")" % (m.text, m.chat.id)).fetchall()
                                    f.commit()
                                    tb.send_message(m.chat.id, "Action completed successfully!")
                                except sqlite3.IntegrityError:
                                    tb.send_message(m.chat.id, "E-mail already registered.")
                if m.chat.id in Array and Array[m.chat.id] == "link":
                    link = f.execute("SELECT link FROM SiteAlert WHERE name = \"%s\"" % (m.text)).fetchone()
                    tb.send_message(m.chat.id, "To " + m.text + " corresponds: " + link[0], reply_markup=markup)
                    Array[m.chat.id] = ""
        else:
            tb.send_message(m.chat.id, "Data not allowed.")


tb = telebot.TeleBot(TOKEN)
tb.set_update_listener(listener)


@tb.message_handler(commands=['ping'])
def ping(m):
    tb.send_message(m.chat.id, "Pong")


@tb.message_handler(commands=['show'])
def show(m):
    tb.send_message(m.chat.id, overrideStdout("show", m, ""))


@tb.message_handler(commands=['check'])
def check(m):
    global Array, f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
    if credentials is not None:
        Array[m.chat.id] = "check"
        tb.send_message(m.chat.id, "Ok, how we should call it?")
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['addme'])
def addme(m):
    global Array, f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
    if credentials is not None:
        Array[m.chat.id] = "addme"
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        dirs = f.execute(
            "SELECT name FROM SiteAlert EXCEPT SELECT name FROM Registered, Users WHERE Registered.mail = Users.mail AND telegram = \"%d\" ORDER BY name" % (
            m.chat.id)).fetchall()
        for dir in dirs:
            markup.add(dir[0])
        tb.send_message(m.chat.id, "Ok, to...?", reply_markup=markup)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['removeme'])
def removeme(m):
    global Array, f
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
    if credentials is not None:
        Array[m.chat.id] = "removeme"
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        dirs = f.execute(
            "SELECT name FROM Registered, Users WHERE Registered.mail = Users.mail AND telegram = \"%d\" ORDER BY name" % (
            m.chat.id)).fetchall()
        for dir in dirs:
            markup.add(dir[0])
        tb.send_message(m.chat.id, "Ok, to...?", reply_markup=markup)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['register'])
def register(m):
    global Array
    Array[m.chat.id] = "register"
    tb.send_message(m.chat.id, "Tell me your e-mail: ")


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
    global Array, f
    Array[m.chat.id] = "link"
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    dirs = f.execute("SELECT name FROM SiteAlert ORDER BY name").fetchall()
    for dir in dirs:
        markup.add(dir[0])
    tb.send_message(m.chat.id, "Of which site?", reply_markup=markup)


@tb.message_handler(commands=['cancel'])
def cancel(m):
    global Array
    Array[m.chat.id] = ""
    Array[m.chat.id, 0] = ""
    markup = types.ReplyKeyboardHide()
    tb.send_message(m.chat.id, "Ok, I forgot everything!", reply_markup=markup)


@tb.message_handler(commands=['help', 'start'])
def help(m):
    tb.send_message(m.chat.id,
                    "Hello, " + m.chat.first_name + " " + m.chat.last_name + "!\nWelcome to @SiteAlert_bot.\nCommands available:\n/ping - Pong\n/show - Print the list of saved sites\n/check - Check new website\n/addme - Notify me on an already registered site\n/removeme - Reverse action\n/register - Register your email\n/registered - Check if you are alredy registered, and show your subscribed sites\n/link - Print the link associated to a website\n/help - Print help message")


tb.polling(none_stop=True)
