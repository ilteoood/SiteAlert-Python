import tgl
import os
import pprint
from functools import partial
import SiteAlert
import sqlite3
import sys

from io import StringIO
from os.path import expanduser

db = expanduser("~") + os.sep + "SiteAlert.db"
our_id = 0
pp = pprint.PrettyPrinter(indent=4)
binlog_done = False;
f = sqlite3.connect(db)


def on_binlog_replay_end():
    binlog_done = True;


def on_get_difference_end():
    pass


def on_our_id(id):
    our_id = id
    return "Set ID: " + str(our_id)


def msg_cb(success, msg):
    pp.pprint(success)
    pp.pprint(msg)


HISTORY_QUERY_SIZE = 100


def history_cb(msg_list, peer, success, msgs):
    print(len(msgs))
    msg_list.extend(msgs)
    print(len(msg_list))
    if len(msgs) == HISTORY_QUERY_SIZE:
        tgl.get_history(peer, len(msg_list), HISTORY_QUERY_SIZE, partial(history_cb, msg_list, peer));


def cb(success):
    print(success)


def overrideStdout(funcName, msg, credentials, dirs="", leng=""):
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    param = msg.text.split(" ")
    if funcName == "mostra":
        SiteAlert.displaySites(dirs, leng)
    elif funcName == "controlla":
        if len(param) > 4:
            if credentials is None or credentials[0] == param[5]:
                SiteAlert.addSite(f, param[3], param[1], param[5], msg.src.name)
            else:
                print("Not allowed to use this mail.")
        else:
            if type(credentials) is not None:
                SiteAlert.addSite(f, param[3], param[1], credentials[0], msg.src.name)
            else:
                print("User not registered!")
    sys.stdout = old_stdout
    return result.getvalue()


def on_msg_receive(msg):
    if msg.out and not binlog_done:
        return;
    if msg.dest.id == our_id:
        peer = msg.src
    else:
        peer = msg.dest
    dirs = f.execute("SELECT name FROM SiteAlert").fetchall()
    leng = len(dirs)
    credentials = f.execute("SELECT mail FROM Users WHERE telegram =\"%s\"" % (msg.src.name)).fetchone()
    mymsg = str.lower(msg.text[0]) + msg.text[1:]
    param = mymsg.split(" ")
    if mymsg == "ping":
        msg.src.send_msg("Pong")
    elif mymsg.startswith("mostra"):
        msg.src.send_msg(overrideStdout("mostra", msg, credentials, dirs, leng))
    elif mymsg.startswith("controlla"):
        msg.src.send_msg(overrideStdout("controlla", msg, credentials))
    elif mymsg.startswith("aggiungimi"):
        if len(param) > 2:
            if credentials is None or param[2] == credentials[0]:
                f.execute("INSERT INTO Registered VALUES(\"%s\", \"%s\",\"%s\")" % (
                    param[1], param[2], msg.src.name)).fetchall()
            else:
                print("Not allowed to use this mail.")
        else:
            if credentials is not None:
                f.execute(
                    "INSERT INTO Registered VALUES(\"%s\", \"%s\",\"%s\")" % (param[1], credentials[0], msg.src.name))
                msg.src.send_msg("Action completed successfully!")
            else:
                msg.src.send_msg("User not registered!")
    elif mymsg.startswith("rimuovimi"):
        if len(param) > 2:
            if credentials is None or param[2] == credentials[0]:
                f.execute("DELETE FROM Registered WHERE mail=\"%s\" AND name=\"%s\"" % (param[2], param[1])).fetchall()
                msg.src.send_msg("Action completed successfully!")
            else:
                msg.src.send_msg("Not allowed to use this mail.")
        else:
            if credentials is not None:
                f.execute(
                    "DELETE FROM Registered WHERE mail=\"%s\" AND name=\"%s\"" % (credentials[0], param[1])).fetchall()
                msg.src.send_msg("Action completed successfully!")
            else:
                msg.src.send_msg("User not registered!")
    elif mymsg.startswith("registrami"):
        tg = f.execute("SELECT telegram FROM Users WHERE mail = \"%s\"" % (param[1])).fetchone()
        if credentials is None and tg is None:
            f.execute("INSERT INTO Users VALUES(\"%s\",\"%s\")" % (param[1], msg.src.name)).fetchall()
            msg.src.send_msg("Action completed successfully!")
        elif credentials is not None and tg is None and credentials[0] != param[1]:
            f.execute("UPDATE Users SET mail = \"%s\" WHERE telegram =\"%s\"" % (param[1], msg.src.name))
            msg.src.send_msg("E-mail updated!")
        else:
            msg.src.send_msg("You already own an account.")
    elif mymsg == "registrato":
        if credentials is None:
            msg.src.send_msg("You don't own any account!")
        else:
            i = 1
            mymsg = "You have registered this e-mail: " + credentials[0] + "\nYou are registered to:"
            for site in f.execute("SELECT name FROM Registered WHERE mail = \"%s\"" % (credentials[0])).fetchall():
                mymsg = mymsg + "\n" + str(i) + ") " + site[0]
                i += 1
            msg.src.send_msg(mymsg)
    elif mymsg.startswith("cancellami"):
        f.execute("DELETE from Users WHERE telegram = \"%s\"" % (msg.src.name))
        msg.src.send_msg("Registration deleted successfully!")
    else:
        msg.src.send_msg("Ciao, " + msg.src.name.replace("_",
                                                         " ") + "!\nBenvenuto nel bot di @SiteAlert.\nComandi disponibili:\ncontrolla _link_ chiamandolo _nome_ avvisandomi _mail_\naggiungimi _nome_ avvisandomi _mail_\nmostra\nrimuovimi _nome_ _mail_\nregistrami _mail_\nregistrato\ncancellami\nTest: ping")
    f.commit()


def on_secret_chat_update(peer, types):
    return "on_secret_chat_update"


def on_user_update(peer, what_changed):
    pass


def on_chat_update(peer, what_changed):
    pass


# Set callbacks
tgl.set_on_binlog_replay_end(on_binlog_replay_end)
tgl.set_on_get_difference_end(on_get_difference_end)
tgl.set_on_our_id(on_our_id)
tgl.set_on_msg_receive(on_msg_receive)
tgl.set_on_secret_chat_update(on_secret_chat_update)
tgl.set_on_user_update(on_user_update)
tgl.set_on_chat_update(on_chat_update)
