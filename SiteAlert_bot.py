__author__ = 'iLTeoooD'

from io import StringIO

from telebot import types

from SiteAlert import *

TOKEN = os.environ['SITE_ALERT_TOKEN']
site_alert = SiteAlert()
leng = ""
Array = {}
gen_markup = types.ReplyKeyboardHide(selective=False)
wlcm_msg = "!\nWelcome to @SiteAlert_bot.\nCommands available:\n/ping - Pong\n/show - Print the list of saved sites\n/check - Check new website\n/addme - Notify me on an already registered site\n/removeme - Reverse action\n/register - Register your email\n/registered - Check if you are alredy registered, and show your subscribed sites\n/unregister - Delete your registration\n/link - Print the link associated to a website\n/mailoff - Disable mail notification\n/mailon - Reverse action\n/telegramoff - Disable telegram notification\n/telegramon - Reverse action\n/help - Print help message"
tb = telebot.TeleBot(TOKEN)


def overrideStdout(funcName, msg, credentials, nameSite="", link=""):
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    if funcName == "show":
        site_alert.display_sites()
    elif funcName == "check":
        site_alert.add_site(nameSite, link, credentials[0], msg.chat.id)
    sys.stdout = old_stdout
    return result.getvalue()


@tb.message_handler(commands=['ping'])
def ping(m):
    tb.send_message(m.chat.id, "Pong")


@tb.message_handler(commands=['show'])
def show(m):
    tb.send_message(m.chat.id, overrideStdout("show", m, ""))


@tb.message_handler(commands=['check'])
def check(m):
    credentials = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,))[0]
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
        credentials = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,))[0]
        tb.send_message(m.chat.id, overrideStdout("check", m, credentials, Array[m.chat.id], m.text))
        del Array[m.chat.id]
    else:
        tb.send_message(m.chat.id, "Invalid name.")


@tb.message_handler(commands=['addme'])
def addme(m):
    credentials = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,))[0]
    if credentials is not None:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        sites = site_alert.execute_fetch_all(
            "SELECT name FROM SiteAlert EXCEPT SELECT name FROM Registered, Users WHERE Registered.mail = Users.mail AND telegram = ? ORDER BY name COLLATE NOCASE",
            (m.chat.id,))
        for site in sites:
            markup.add(site[0])
        msg = tb.send_message(m.chat.id, "Ok, to...?", reply_markup=markup)
        tb.register_next_step_handler(msg, am)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


def am(m):
    sites = site_alert.execute_fetch_all("SELECT * FROM SiteAlert WHERE name=?", (m.text,))
    if len(sites) > 0:
        credentials = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,))[0]
        try:
            site_alert.execute_query("INSERT INTO Registered VALUES(?, ?)", (m.text, credentials[0]))
            tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=gen_markup)
        except sqlite3.IntegrityError:
            tb.send_message(m.chat.id, "You are already registered to this site!", reply_markup=gen_markup)
    elif not m.text.startswith("/"):
        tb.send_message(m.chat.id, "Invalid input.")


@tb.message_handler(commands=['removeme'])
def removeme(m):
    credentials = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,))[0]
    if credentials is not None:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        sites = site_alert.execute_fetch_all(
            "SELECT name FROM Registered, Users WHERE Registered.mail = Users.mail AND telegram = ? ORDER BY name COLLATE NOCASE",
            (m.chat.id,))
        for site in sites:
            markup.add(site[0])
        msg = tb.send_message(m.chat.id, "Ok, from...?", reply_markup=markup)
        tb.register_next_step_handler(msg, rm)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


def rm(m):
    sites = site_alert.execute_fetch_all("SELECT * FROM SiteAlert WHERE name=?", (m.text,))
    if len(sites) > 0:
        credentials = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,))[0]
        site_alert.execute_query("DELETE FROM Registered WHERE mail=? AND name=?", (credentials[0], m.text))
        tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=gen_markup)
    elif not m.text.startswith("/"):
        tb.send_message(m.chat.id, "Invalid input.")


@tb.message_handler(commands=['register'])
def register(m):
    credentials = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,))[0]
    if credentials is None:
        msg = tb.send_message(m.chat.id, "Tell me your e-mail: ")
        tb.register_next_step_handler(msg, reg)
    else:
        tb.send_message(m.chat.id, "User already registered.\nUse /registered")


def reg(m):
    if re.match("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", m.text) is not None:
        site_alert.execute_query("INSERT INTO Users VALUES(?,?,'True','True')", (m.text, m.chat.id))
        tb.send_message(m.chat.id, "Action completed successfully!")
    else:
        tb.send_message(m.chat.id, "Invalid e-mail.")


@tb.message_handler(commands=['registered'])
def registered(m):
    i = 1
    credentials = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram =?", (m.chat.id,))[0]
    if credentials is not None:
        mymsg = "You have registered this e-mail: " + credentials[0] + "\nYour notification status is:\nE-mail: "
        status = site_alert.execute_fetch_all("SELECT mailnotification FROM Users WHERE mail = ?", (credentials[0],))[
            0]
        mymsg += status[0] + "\nTelegram: "
        status = \
            site_alert.execute_fetch_all("SELECT telegramnotification FROM Users WHERE mail = ?", (credentials[0],))[0]
        mymsg += status[0] + "\nYou are registered to:"
        for site in site_alert.execute_fetch_all("SELECT name FROM Registered WHERE mail = ?", (credentials[0],)):
            mymsg = mymsg + "\n" + str(i) + ") " + site[0]
            i += 1
        tb.send_message(m.chat.id, mymsg)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['link'])
def link(m):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    sites = site_alert.execute_fetch_all("SELECT name FROM SiteAlert ORDER BY name COLLATE NOCASE", ())
    for site in sites:
        markup.add(site[0])
    msg = tb.send_message(m.chat.id, "Of which site?", reply_markup=markup)
    tb.register_next_step_handler(msg, lk)


def lk(m):
    try:
        link = site_alert.execute_fetch_all("SELECT link FROM SiteAlert WHERE name = ?", (m.text,))[0]
        tb.send_message(m.chat.id, "To " + m.text + " corresponds: " + link[0], reply_markup=gen_markup)
    except Exception:
        tb.send_message(m.chat.id, "Invalid link.", reply_markup=gen_markup)


@tb.message_handler(commands=['unregister'])
def unregister(m):
    mail = site_alert.execute_fetch_all("SELECT mail FROM Users WHERE telegram = ?", (m.chat.id,))[0]
    if mail is not None:
        site_alert.execute_query("DELETE FROM Users WHERE mail = ?", (mail[0],))
        site_alert.execute_query("DELETE FROM Registered WHERE mail = ?", (mail[0],))
        tb.send_message(m.chat.id, "Action completed successfully!", reply_markup=gen_markup)
    else:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['mailoff'])
def mailoff(m):
    try:
        site_alert.execute_query("UPDATE Users SET mailnotification = 'False' WHERE telegram = ?", (m.chat.id,))
        tb.send_message(m.chat.id, "Action completed successfully!")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['mailon'])
def mailon(m):
    try:
        site_alert.execute_query("UPDATE Users SET mailnotification = 'True' WHERE telegram = ?", (m.chat.id,))
        tb.send_message(m.chat.id, "Action completed successfully!")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['telegramoff'])
def telegramoff(m):
    try:
        site_alert.execute_query("UPDATE Users SET telegramnotification = 'False' WHERE telegram = ?", (m.chat.id,))
        tb.send_message(m.chat.id, "Action completed successfully!")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['telegramon'])
def telegramon(m):
    try:
        site_alert.execute_query("UPDATE Users SET telegramnotification = 'True' WHERE telegram = ?", (m.chat.id,))
        tb.send_message(m.chat.id, "Action completed successfully!")
    except sqlite3.IntegrityError:
        tb.send_message(m.chat.id, "You must be registered.\nUse /register")


@tb.message_handler(commands=['cancel'])
def cancel(m):
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
