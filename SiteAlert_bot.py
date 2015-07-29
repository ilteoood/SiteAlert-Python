__author__ = 'ilteoood'

import sys
import SiteAlert
import telebot
import sqlite3
import os

from io import StringIO
from os.path import expanduser

TOKEN = 'YOUR TOKEN HERE'
db = expanduser("~") + os.sep + "SiteAlert.db"


def overrideStdout(funcName, msg, credentials, dirs="", leng=""):
    f = sqlite3.connect(db)
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    param = msg.text.split(" ")
    if funcName == "mostra":
        SiteAlert.displaySites(dirs, leng)
    elif funcName == "controlla":
        if len(param) > 4:
            if credentials is None or credentials[0] == param[5]:
                SiteAlert.addSite(f, param[3], param[1], param[5], msg.chat.id)
            else:
                print("Not allowed to use this mail.")
        else:
            if type(credentials) is not None:
                SiteAlert.addSite(f, param[3], param[1], credentials[0], msg.chat.id)
            else:
                print("User not registered!")
    sys.stdout = old_stdout
    f.close()
    return result.getvalue()


def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            f = sqlite3.connect(db)
            dirs = f.execute("SELECT name FROM SiteAlert").fetchall()
            leng = len(dirs)
            credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (m.chat.id)).fetchone()
            mymsg = str.lower(m.text[0]) + m.text[1:]
            param = mymsg.split(" ")
            if mymsg == "ping":
                tb.send_message(m.chat.id, "Pong")
            elif mymsg.startswith("mostra"):
                tb.send_message(m.chat.id, overrideStdout("mostra", m, credentials, dirs, leng))
            elif mymsg.startswith("controlla"):
                tb.send_message(m.chat.id, overrideStdout("controlla", m, credentials))
            elif mymsg.startswith("aggiungimi"):
                if len(param) > 2:
                    if credentials is None or param[2] == credentials[0]:
                        f.execute("INSERT INTO Registered VALUES(\"%s\", \"%s\",\"%s\")" % (
                            param[1], param[2], m.chat.id)).fetchall()
                    else:
                        print("Not allowed to use this mail.")
                else:
                    if credentials is not None:
                        f.execute(
                            "INSERT INTO Registered VALUES(\"%s\", \"%s\",\"%s\")" % (
                                param[1], credentials[0], m.chat.id))
                        tb.send_message(m.chat.id, "Action completed successfully!")
                    else:
                        tb.send_message(m.chat.id, "User not registered!")
            elif mymsg.startswith("rimuovimi"):
                if len(param) > 2:
                    if credentials is None or param[2] == credentials[0]:
                        f.execute("DELETE FROM Registered WHERE mail=\"%s\" AND name=\"%s\"" % (
                            param[2], param[1])).fetchall()
                        tb.send_message(m.chat.id, "Action completed successfully!")
                    else:
                        tb.send_message(m.chat.id, "Not allowed to use this mail.")
                else:
                    if credentials is not None:
                        f.execute(
                            "DELETE FROM Registered WHERE mail=\"%s\" AND name=\"%s\"" % (
                                credentials[0], param[1])).fetchall()
                        tb.send_message(m.chat.id, "Action completed successfully!")
                    else:
                        tb.send_message(m.chat.id, "User not registered!")
            elif mymsg.startswith("registrami"):
                tg = f.execute("SELECT telegram FROM Users WHERE mail = \"%s\"" % (param[1])).fetchone()
                if credentials is None and tg is None:
                    f.execute("INSERT INTO Users VALUES(\"%s\",\"%s\")" % (param[1], m.chat.id)).fetchall()
                    tb.send_message(m.chat.id, "Action completed successfully!")
                elif credentials is not None and tg is None and credentials[0] != param[1]:
                    f.execute("UPDATE Users SET mail = \"%s\" WHERE telegram =\"%s\"" % (param[1], m.chat.id))
                    tb.send_message(m.chat.id, "E-mail updated!")
                else:
                    tb.send_message(m.chat.id, "You already own an account.")
            elif mymsg == "registrato":
                if credentials is None:
                    tb.send_message(m.chat.id, "You don't own any account!")
                else:
                    i = 1
                    mymsg = "You have registered this e-mail: " + credentials[0] + "\nYou are registered to:"
                    for site in f.execute(
                                    "SELECT name FROM Registered WHERE mail = \"%s\"" % (credentials[0])).fetchall():
                        mymsg = mymsg + "\n" + str(i) + ") " + site[0]
                        i += 1
                    tb.send_message(m.chat.id, mymsg)
            elif mymsg == "cancellami":
                f.execute("DELETE from Users WHERE telegram = \"%s\"" % (m.chat.id))
                tb.send_message(m.chat.id, "Registration deleted successfully!")
            elif mymsg.startswith("link"):
                link = f.execute("SELECT link FROM SiteAlert WHERE name = \"%s\"" % (param[1])).fetchone()
                tb.send_message(m.chat.id, "A " + param[1] + " corrisponde: " + link[0])
            else:
                tb.send_message(m.chat.id,
                                "Ciao, " + m.chat.first_name + " " + m.chat.last_name + "!\nBenvenuto nel bot di SiteAlert.\nComandi disponibili:\ncontrolla _link_ chiamandolo _nome_ avvisandomi _mail_\naggiungimi _nome_ avvisandomi _mail_\nmostra\nrimuovimi _nome_ _mail_\nregistrami _mail_\nregistrato\ncancellami\nlink _name_\nTest: ping")
            f.commit()
            f.close()
        else:
            tb.send_message(m.chat.id, "Data not allowed.")


tb = telebot.TeleBot(TOKEN)
tb.set_update_listener(listener)  # register listener
tb.polling()
tb.polling(none_stop=True)
tb.polling(interval=1)

while True:  # Don't let the main Thread end.
    pass
