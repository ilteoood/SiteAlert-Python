"""
SiteAlert, what are you waiting for?

Copyright (c) 2015, Matteo Pietro Dazzi <---> ilteoood
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the
  following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
  the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
========================================================================================================================
"""
__author__ = 'iLTeoooD'
import urllib.request
import hashlib
import sqlite3
import os
import smtplib
import time
import sys
import platform
import socket
import re
from os.path import expanduser

import telebot
from bs4 import BeautifulSoup

db = expanduser("~") + os.sep + "SiteAlert.db"
header = [('User-Agent',
           'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
          ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
          ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'),
          ('Accept-Encoding', 'none'),
          ('Accept-Language', 'en-US,en;q=0.8'),
          ('Connection', 'keep-alive')]
TOKEN = 'YOUR TOKEN HERE'
MAIL = 'YOUR MAIL HERE'
PSW = 'YOUR PASSWORD HERE'
tb = telebot.TeleBot(TOKEN)


def clearScreen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def visualizeMenu():
    clearScreen()
    print(
        "What do you want to do?\n1) Display sites\n2) Add new site to check\n3) Fetch site\n4) Check sites\n5) Add e-mail to notification\n6) Remove e-mail from notification\n7) Delete a site\n8) Clean database\n9) Exit")


def choice():
    clearScreen()
    try:
        x = -1
        while not 1 <= x <= 9:
            if x != 9:
                visualizeMenu()
            x = int(input())
        return x
    except ValueError:
        return 9


def displaySites(dirs, leng):
    if leng != 0:
        i = 1
        for dir in dirs:
            print(str(i) + ") " + dir[0])
            i += 1
    else:
        print("You haven't checked any site!")


def cleanDB(f):
    nameSite = f.execute("SELECT name FROM SiteAlert EXCEPT SELECT name FROM Registered GROUP BY name").fetchall()
    for name in nameSite:
        print("Removing %s..." % (name))
        f.execute("DELETE FROM SiteAlert WHERE name = ?", (name[0],))
    f.commit()


def stdURL(site):
    if not site.startswith("http://") and not site.startswith("https://"):
        site = "http://" + site
    return site


def URLEncode(read):
    read = BeautifulSoup(read, "html.parser")
    read = re.sub("<!--[\s\S]*?-->", "", read.get_text())
    read = re.sub("(?s)/\\*.*?\\*/", "", read)
    return hashlib.md5(bytes(read, 'utf-8')).hexdigest()


def saveFile(f, nameSite, link, mail, telegram, hash):
    try:
        f.execute("INSERT INTO SiteAlert (name,link,hash) VALUES (?,?,?)", (
            nameSite, link, hash))
        mail = mail.split(";");
        for m in mail:
            f.execute("INSERT INTO Registered (name, mail) VALUES (?,?)", (
                nameSite, m))
    except sqlite3.IntegrityError:
        f.execute("UPDATE SiteAlert SET hash=? WHERE name=?", (hash, nameSite))
    f.commit()
    print("Site saved correctly!")


def addSite(f, nameSite, link, mail='', telegram=''):
    if link == "" or nameSite == "":
        link = input("Insert the link for the site: ")
        nameSite = input("Insert a name for the site: ")
        mail = input(
            "Insert the email where you want to be informed (if you want to add other mail, separate them with \";\"): ")
    try:
        link = stdURL(link)
        urli = urllib.request.build_opener()
        urli.addheaders = header
        urli = urli.open(link, timeout=10.0)
        responseCode = urli.getcode()
        if responseCode == 200:
            saveFile(f, nameSite, link, mail, telegram, URLEncode(urli.read()))
        elif responseCode == 404:
            print("This page doesn't exist!")
        else:
            print("Generic error.")
    except urllib.request.URLError:
        print("There is an error with the link.")
    except ConnectionResetError:
        print("[ERROR]: Connection reset by peer: ")
    except socket.timeout:
        print("[ERROR]: Connection timeout")


def sendMail(f, nameSite, link):
    global MAIL, PSW
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.starttls()
    try:
        server.login(MAIL, PSW)
        subj = "The site \"" + nameSite + "\" has been changed!"
        msg = "Subject: " + subj + "\n" + subj + "\nLink: " + link
        mail = f.execute(
            "SELECT Registered.mail FROM Users, Registered WHERE Registered.mail = Users.mail AND mailnotification = 'True' AND name=?",
            (nameSite,)).fetchall()
        for address in mail:
            try:
                server.sendmail(MAIL, address, msg)
            except smtplib.SMTPRecipientsRefused:
                print("Error with this e-mail destination address: " + address)
        server.close()
        telegram = f.execute(
            "SELECT telegram FROM Users, Registered WHERE telegramnotification = 'True' AND name=? AND Users.mail = Registered.mail",
            (nameSite,)).fetchall()
        for t in telegram:
            try:
                tb.send_message(t[0], subj + "\nLink: " + link)
            except telebot.apihelper.ApiException:
                print("Bot kicked from " + t[0], ", removing from DB...")
                f.execute("DELETE FROM Registered WHERE mail = (SELECT mail FROM Users WHERE telegram = ?)", (t[0],))
                f.execute("DELETE FROM Users WHERE telegram = ?", (t[0],))
                f.commit()
    except smtplib.SMTPAuthenticationError:
        print("Error in the login process")


def checkSite(f, dirs):
    if len(dirs) > 0:
        for dir in dirs:
            dir = dir[0]
            query = f.execute("SELECT hash,link FROM SiteAlert WHERE name=\"" + dir + "\"").fetchone()
            hash = query[0]
            link = query[1]
            urli = urllib.request.build_opener()
            urli.addheaders = header
            try:
                urli = urli.open(link, timeout=10.0)
                if hash == URLEncode(urli.read()):
                    print("The site \"" + dir + "\" hasn't been changed!")
                else:
                    print("The site \"" + dir + "\" has been changed!")
                    addSite(f, dir, link, "")
                    sendMail(f, dir, link)
            except urllib.error.URLError:
                print("[ERROR]: Network error: " + dir)
            except ConnectionResetError:
                print("[ERROR]: Connection reset by peer: " + dir)
            except socket.timeout:
                print("[ERROR]: Connection timeout: " + dir)

    else:
        print("You haven't checked any site.")
        return True
    return False


def numberReq(leng, dirs):
    s = -1
    displaySites(dirs, leng)
    while s <= 0 or s > leng:
        print("Number of the site: ", )
        s = int(input())
    return s


def main():
    c = 1
    n = len(sys.argv)
    x = 0
    if not os.path.isfile(db):
        print("[WARNING]: No db found, creating a new one.")
        f = sqlite3.connect(db)
        f.execute(
            "CREATE TABLE `SiteAlert` (`name` TEXT NOT NULL UNIQUE,`link` TEXT NOT NULL,`hash` TEXT NOT NULL,PRIMARY KEY(link));")
        f.execute(
            "CREATE TABLE 'Registered'('name' TEXT NOT NULL,'mail' TEXT NOT NULL, PRIMARY KEY(name, mail));")
        f.execute(
            "CREATE TABLE Users ('mail' TEXT NOT NULL, 'telegram' TEXT NOT NULL UNIQUE, 'mailnotification' BOOLEAN NOT NULL DEFAULT TRUE, 'telegramnotification' BOOLEAN NOT NULL DEFAULT TRUE, PRIMARY KEY (mail));")
        f.close()
    f = sqlite3.connect(db)
    while True:
        dirs = f.execute("SELECT name FROM SiteAlert").fetchall()
        leng = len(dirs)
        s = ""
        if c < n:
            arg = sys.argv[c]
            x = {"-a": 2, "-am": 5, "-b": 4, "-c": 4, "-cl": 8, "-d": 7, "-e": 9, "-f": 3,
                 "-h": 0, "-r": 6,
                 "-s": 1}.get(arg)
            s = {"-b": "y", "-c": "n"}.get(arg)
            c += 1
        else:
            x = choice()
        clearScreen()
        if x == 0:
            print(
                "Usage:\n-a -> add a new site\n-am -> add new e-mail address\n-b -> continuous check\n-c -> check once\n-cl -> clean database\n-d -> delete a site\n-e -> exit\n-h -> print this help\n-r -> remove e-mail address\n-s -> show the list of the sites")
        elif x == 1:
            displaySites(dirs, leng)
        elif x == 2:
            addSite(f, "", "", "")
        elif x == 3:
            if leng != 0:
                print("Write the number of the site that you want to fetch.")
                nameSite = dirs[numberReq(leng, dirs) - 1][0]
                query = f.execute("SELECT link FROM SiteAlert WHERE name=\"" + nameSite + "\"").fetchone()
                link = query[0]
                addSite(f, nameSite, link)
            else:
                print("You haven't checked any site.")
        elif x == 4:
            if s == "":
                s = input("Do you want to check it continually? (Y/n)")
                while len(s) == 0 or (s[0] != 'n' and s[0] != 'y'):
                    if len(s) == 0:
                        s = "y"
                        break
                    else:
                        s = input("Wrong input, do you want to check it continually? (Y/n)")
            while True:
                if checkSite(f, dirs) or s != "y":
                    s = "n"
                    break
                else:
                    time.sleep(30)
                    cleanDB(f)
                    dirs = f.execute("SELECT name FROM SiteAlert").fetchall()
        elif x == 5 or x == 6:
            if leng != 0:
                print("Write the number of the site.")
                nameSite = dirs[numberReq(leng, dirs) - 1][0]
                mail = input("Insert e-mail: ")
                if x == 5:
                    f.execute("INSERT INTO Registered VALUES(?, ?)", (nameSite, mail)).fetchall()
                else:
                    f.execute("DELETE FROM Registered WHERE mail=? AND name=?", (mail, nameSite)).fetchall()
                f.commit()
                print("Action completed successfully!")
            else:
                print("You haven't checked any site.")
        elif x == 7:
            if leng != 0:
                print("Write the number of the site that you want to delete.")
                s = numberReq(leng, dirs) - 1
                f.execute("DELETE FROM SiteAlert WHERE name=\"" + dirs[s][0] + "\"")
                f.execute("DELETE FROM Registered WHERE name=\"" + dirs[s][0] + "\"")
                f.commit()
                print("Site deleted successfully!")
            else:
                print("You haven't checked any site!")
        elif x == 8:
            cleanDB(f)
        elif x != 9:
            print("Unknown command: \"" + arg + "\"")
        if x == 9:
            f.close()
            sys.exit(0)
        input("Press enter to continue...")


if __name__ == "__main__":
    main()
