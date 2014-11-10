"""
SiteAlert, what are you waiting for?

Copyright (c) 2014, Matteo Pietro Dazzi <---> ilteoood
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
from os.path import expanduser

db = expanduser("~") + os.sep + "SiteAlert.db"
header = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
       ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
       ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'),
       ('Accept-Encoding', 'none'),
       ('Accept-Language', 'en-US,en;q=0.8'),
       ('Connection', 'keep-alive')]

def clearScreen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def visualizeMenu():
    clearScreen()
    print("What do you want to do?\n1) Display sites\n2) Add new site to check\n3) Fetch site\n4) Check sites\n5) Delete a site\n6) Exit")


def choice():
    clearScreen()
    try:
        x = -1
        while not 1 <= x <= 6:
            if x != 6:
                visualizeMenu()
            x = int(input())
        return x
    except ValueError:
        return 6


def displaySites(dirs):
    i = 1
    for dir in dirs:
        print(str(i) + ") " + dir[0])
        i = i + 1


def stdURL(site):
    if not site.startswith("http://") and not site.startswith("https://"):
        site = "http://" + site
    return site


def URLEncode(read):
    return hashlib.md5(bytes(read)).hexdigest()


def saveFile(f, nameSite, link, mail, hash):
    try:
        f.execute("INSERT INTO SiteAlert (name,link,mail,hash) VALUES (\"%s\",\"%s\",\"%s\",\"%s\")" % (nameSite, link, mail, hash))
    except sqlite3.IntegrityError:
        f.execute("UPDATE SiteAlert SET hash=\"%s\" WHERE name=\"%s\"" % (hash, nameSite))
    f.commit()
    print("Site saved correctly!")


def addSite(f, nameSite, link, mail):
    if link == "" or nameSite == "" or mail == "":
        link = input("Insert the link for the site: ")
        nameSite = input("Insert a name for the site: ")
        mail = input(
            "Insert the email where you want to be informed (if you want to add other mail, separate them with \";\"): ")
    try:
        link=stdURL(link)
        urli = urllib.request.build_opener()
        urli.addheaders = header
        urli = urli.open(link)
        responseCode = urli.getcode()
        if responseCode == 200:
            saveFile(f, nameSite, link, mail, URLEncode(urli.read()))
        elif responseCode == 404:
            print("This page doesn't exist!")
        else:
            print("Generic error.")
    except urllib.request.URLError:
        print("There is an error with the link.")


def sendMail(nameSite, link, mail):
    try:
        server = smtplib.SMTP("smtp.gmail.com:587")
        server.starttls()
        server.login("SiteAlertMailNotification@gmail.com", "SiteAlertMailNotificatio")
        subj = "The site \"" + nameSite + "\" has been changed!"
        msg = "Subject: " + subj + "\n" + subj + "\nLink: " + link
        mail = mail.split(";")
        for address in mail:
            server.sendmail("SiteAlertMailNotification@gmail.com", address, msg)
        server.close()
    except smtplib.SMTPRecipientsRefused:
        print("Error with the e-mail destination address.")


def checkSite(f, dirs):
    if len(dirs) > 0:
        for dir in dirs:
            dir=dir[0]
            query = f.execute("SELECT hash,link,mail FROM SiteAlert WHERE name=\"" + dir + "\"").fetchone()
            hash = query[0]
            link = query[1]
            mail = query[2]
            urli = urllib.request.build_opener()
            urli.addheaders = header
            urli = urli.open(link)
            if hash == URLEncode(urli.read()):
                print("The site \"" + dir + "\" hasn't been changed!")
            else:
                print("The site \"" + dir + "\" has been changed!")
                addSite(f, dir, link, mail)
                sendMail(dir, link, mail)
    else:
        print("You haven't checked any site.")
        return True
    return False


def numberReq(leng, dirs):
    s = -1
    displaySites(dirs)
    while s <= 0 or s > leng:
        print("Number of the site: ", )
        s = int(input())
    return s


def main():
    c = 1; n = len(sys.argv)
    if not os.path.isfile(db):
        print("[WARNING]: No db found, creating a new one.")
        sqlite3.connect(db).execute(
            "CREATE TABLE `SiteAlert` (`name` TEXT NOT NULL,`link` TEXT NOT NULL,`mail` TEXT NOT NULL,`hash` TEXT NOT NULL,PRIMARY KEY(link));").close()
    f = sqlite3.connect(db)
    while True:
        dirs = f.execute("SELECT name FROM SiteAlert").fetchall(); leng = len(dirs); s = ""
        if c < n:
            arg = sys.argv[c]
            x = {"-a": 2, "-b": 4, "-c": 4, "-d": 5, "-e": 6, "-f": 3, "-h": 0, "-s": 1}.get(arg)
            s = {"-b": "n", "-c": "y"}.get(arg)
            c += 1
        else:
            x = choice()
        clearScreen()
        if x == 0:
            print("Usage:\n-a -> add a new site\n-b -> continuous check\n-c -> check once\n-d -> delete a site\n-e -> exit\n-h -> print this help\n-s -> show the list of the sites")
        elif x == 1:
            if leng != 0:
                displaySites(dirs)
            else:
                print("You haven't checked any site!")
        elif x == 2:
            addSite(f, "", "", "")
        elif x == 3:
            if leng != 0:
                print("Write the number of the site that you want to fetch.")
                nameSite = dirs[numberReq(leng, dirs) - 1][0]
                query = f.execute("SELECT link,mail FROM SiteAlert WHERE name=\"" + nameSite + "\"").fetchone()
                link = query[0]
                mail = query[1]
                addSite(f, nameSite, link, mail)
            else:
                print("You haven't checked any site.")
        elif x == 4:
            if s == "":
                s = input("Do you want to check it continually? (Y/n)")
                while len(s) == 0 or ( s[0] != 'n' and s[0] != 'y'):
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
        elif x == 5:
            if leng != 0:
                print("Write the number of the site that you want to delete.")
                s = numberReq(leng, dirs) - 1
                f.execute("DELETE FROM SiteAlert WHERE name=\"" + dirs[s][0] + "\"")
                f.commit()
                print("Site deleted successfully!")
            else:
                print("You haven't checked any site!")
        elif x == 6:
            f.close()
            sys.exit(0)
        else:
            print("Unknown command: \"" + arg + "\"")
        input("Press enter to continue...")


if __name__ == "__main__":
    main()
