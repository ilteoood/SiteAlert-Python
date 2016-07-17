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
import hashlib
import os
import platform
import re
import smtplib
import socket
import sqlite3
import sys
import time
import urllib.request
from os.path import expanduser

import telebot
from bs4 import BeautifulSoup


class SiteAlert:
    def __init__(self):
        self.__db = expanduser("~") + os.sep + "SiteAlert.db"
        if not os.path.isfile(self.__db):
            print("[WARNING]: No db found, creating a new one.")
            connection = sqlite3.connect(self.__db)
            connection.execute(
                "CREATE TABLE `SiteAlert` (`name` TEXT NOT NULL UNIQUE,`link` TEXT NOT NULL,`hash` TEXT NOT NULL,PRIMARY KEY(link));")
            connection.execute(
                "CREATE TABLE 'Registered'('name' TEXT NOT NULL,'mail' TEXT NOT NULL, PRIMARY KEY(name, mail));")
            connection.execute(
                "CREATE TABLE Users ('mail' TEXT NOT NULL, 'telegram' TEXT NOT NULL UNIQUE, 'mailnotification' BOOLEAN NOT NULL DEFAULT TRUE, 'telegramnotification' BOOLEAN NOT NULL DEFAULT TRUE, PRIMARY KEY (mail));")
            connection.close()
        self.__connection = sqlite3.connect(self.__db, check_same_thread=False)
        self.__header = [('User-Agent',
                          'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
                         ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                         ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'),
                         ('Accept-Encoding', 'none'),
                         ('Accept-Language', 'en-US,en;q=0.8'),
                         ('Connection', 'keep-alive')]
        self.__TOKEN = os.environ['SITE_ALERT_TOKEN']
        self.__MAIL = os.environ['SITE_ALERT_MAIL']
        self.__PSW = os.environ['SITE_ALERT_PASSWORD']
        self.__tb = telebot.TeleBot(self.__TOKEN)
        self.saved_on_db()

    def display_sites(self):
        self.saved_on_db()
        leng = len(self.__sites)
        if leng != 0:
            i = 1
            for site in self.__sites:
                print(str(i) + ") " + site[0])
                i += 1
        else:
            print("You haven't checked any site!")

    def clean_db(self):
        nameSite = self.execute_fetch_all(
            "SELECT name FROM SiteAlert EXCEPT SELECT name FROM Registered GROUP BY name", ())
        for name in nameSite:
            print("Removing \"%s\"..." % (name))
            self.execute_query("DELETE FROM SiteAlert WHERE name = ?", (name[0],))

    def __std_url(self, site):
        if not site.startswith("http://") and not site.startswith("https://"):
            site = "http://" + site
        return site

    def __url_encode(self, read):
        read = BeautifulSoup(read, "html.parser")
        read = re.sub("<!--[\s\S]*?-->", "", read.get_text())
        read = re.sub("(?s)/\\*.*?\\*/", "", read)
        return hashlib.md5(bytes(read, 'utf-8')).hexdigest()

    def __save_file(self, nameSite, link, mail, telegram, hash):
        try:
            self.execute_query("INSERT INTO SiteAlert (name,link,hash) VALUES (?,?,?)", (
                nameSite, link, hash))
            mail = mail.split(";")
            for m in mail:
                self.execute_query("INSERT INTO Registered (name, mail) VALUES (?,?)", (
                    nameSite, m))
            print("Site saved correctly!")
        except sqlite3.IntegrityError:
            self.execute_query("UPDATE SiteAlert SET hash=? WHERE name=?", (hash, nameSite))
            print("Already exist a site with this credentials.")

    def add_site(self, nameSite, link, mail='', telegram=''):
        if link == "" or nameSite == "":
            link = input("Insert the link for the site: ")
            nameSite = input("Insert a name for the site: ")
            mail = input(
                "Insert the email where you want to be informed (if you want to add other mail, separate them with \";\"): ")
        try:
            link = self.__std_url(link)
            urli = urllib.request.build_opener()
            urli.addheaders = self.__header
            urli = urli.open(link, timeout=10.0)
            responseCode = urli.getcode()
            if responseCode == 200:
                self.__save_file(nameSite, link, mail, telegram, self.__url_encode(urli.read()))
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

    def __send_mail(self, nameSite, link):
        server = smtplib.SMTP("smtp.gmail.com:587")
        server.starttls()
        try:
            server.login(self.__MAIL, self.__PSW)
            subj = "The site \"" + nameSite + "\" has been changed!"
            msg = "Subject: " + subj + "\n" + subj + "\nLink: " + link
            mail = self.execute_fetch_all(
                "SELECT Registered.mail FROM Users, Registered WHERE Registered.mail = Users.mail AND mailnotification = 'True' AND name=?",
                (nameSite,))
            for address in mail:
                try:
                    server.sendmail(self.__MAIL, address, msg)
                except smtplib.SMTPRecipientsRefused:
                    print("Error with this e-mail destination address: " + address)
            server.close()
            telegram = self.execute_fetch_all(
                "SELECT telegram FROM Users, Registered WHERE telegramnotification = 'True' AND name=? AND Users.mail = Registered.mail",
                (nameSite,))
            for t in telegram:
                try:
                    self.__tb.send_message(t[0], subj + "\nLink: " + link)
                except telebot.apihelper.ApiException:
                    print("Bot kicked from " + t[0], ", removing from DB...")
                    self.execute_query(
                        "DELETE FROM Registered WHERE mail = (SELECT mail FROM Users WHERE telegram = ?)",
                        (t[0],))
                    self.execute_query("DELETE FROM Users WHERE telegram = ?", (t[0],))
        except smtplib.SMTPAuthenticationError:
            print("Error in the login process")

    def check_site(self):
        self.saved_on_db()
        if len(self.__sites) > 0:
            for site in self.__sites:
                site = site[0]
                query = self.execute_fetch_all("SELECT hash,link FROM SiteAlert WHERE name=?", (site,))[0]
                hash = query[0]
                link = query[1]
                urli = urllib.request.build_opener()
                urli.addheaders = self.__header
                try:
                    urli = urli.open(link, timeout=10.0)
                    if hash == self.__url_encode(urli.read()):
                        print("The site \"" + site + "\" hasn't been changed!")
                    else:
                        print("The site \"" + site + "\" has been changed!")
                        self.add_site(site, link, "")
                        self.__send_mail(site, link)
                except urllib.error.URLError:
                    print("[ERROR]: Network error: " + site)
                except ConnectionResetError:
                    print("[ERROR]: Connection reset by peer: " + site)
                except socket.timeout:
                    print("[ERROR]: Connection timeout: " + site)

        else:
            print("You haven't checked any site.")
            return True
        return False

    def execute_query(self, query, parameters):
        self.__connection.execute(query, parameters)
        self.__connection.commit()

    def execute_fetch_all(self, query, parameters):
        saved_sites = self.__connection.execute(query, parameters).fetchall()
        self.__connection.commit()
        return saved_sites

    def saved_on_db(self):
        self.__sites = self.execute_fetch_all("SELECT name FROM SiteAlert", ())
        return self.__sites

    def number_req(self):
        s = -1
        self.display_sites()
        while s <= 0 or s > len(self.__sites):
            print("Number of the site: ", )
            try:
                s = int(input())
            except ValueError:
                s = -1
        return s

    def close_connection(self):
        self.__connection.close()

    def delete_site(self, name):
        self.execute_query("DELETE FROM SiteAlert WHERE name=?", (name,))
        self.execute_query("DELETE FROM Registered WHERE name=?", (name,))


def clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def display_menu():
    clear_screen()
    print(
        "What do you want to do?\n1) Display sites\n2) Add new site to check\n3) Fetch site\n4) Check sites\n5) Add e-mail to notification\n6) Remove e-mail from notification\n7) Delete a site\n8) Clean database\n9) Exit")


def choice():
    clear_screen()
    try:
        x = -1
        while not 1 <= x <= 9:
            if x != 9:
                display_menu()
            x = int(input())
        return x
    except ValueError:
        return 9


def main():
    c = 1
    n = len(sys.argv)
    site_alert = SiteAlert()
    while True:
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
        clear_screen()
        if x == 0:
            print(
                "Usage:\n-a -> add a new site\n-am -> add new e-mail address\n-b -> continuous check\n-c -> check once\n-cl -> clean database\n-d -> delete a site\n-e -> exit\n-h -> print this help\n-r -> remove e-mail address\n-s -> show the list of the sites")
        elif x == 1:
            site_alert.display_sites()
        elif x == 2:
            site_alert.add_site("", "")
        elif x == 3:
            saved = site_alert.saved_on_db()
            if len(saved) != 0:
                print("Write the number of the site that you want to fetch.")
                nameSite = saved[site_alert.number_req() - 1][0]
                query = site_alert.execute_fetch_all("SELECT link FROM SiteAlert WHERE name=?", (nameSite,))[0]
                link = query[0]
                site_alert.add_site(nameSite, link)
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
                if site_alert.check_site() or s != "y":
                    break
                else:
                    time.sleep(30)
                    site_alert.clean_db()
        elif x == 5 or x == 6:
            saved = site_alert.saved_on_db()
            if len(saved) != 0:
                print("Write the number of the site.")
                nameSite = saved[site_alert.number_req() - 1][0]
                mail = input("Insert e-mail: ")
                if x == 5:
                    site_alert.execute_query("INSERT INTO Registered VALUES(?, ?)", (nameSite, mail))
                else:
                    site_alert.execute_query("DELETE FROM Registered WHERE mail=? AND name=?", (mail, nameSite))
                print("Action completed successfully!")
            else:
                print("You haven't checked any site.")
        elif x == 7:
            saved = site_alert.saved_on_db()
            if len(saved) != 0:
                print("Write the number of the site that you want to delete.")
                index = site_alert.number_req() - 1
                site_alert.delete_site(saved[index][0])
                print("Site deleted successfully!")
            else:
                print("You haven't checked any site!")
        elif x == 8:
            site_alert.clean_db()
        elif x != 9:
            print("Unknown command: \"" + arg + "\"")
        if x == 9:
            site_alert.close_connection()
            sys.exit(0)
        input("Press enter to continue...")


if __name__ == "__main__":
    main()
