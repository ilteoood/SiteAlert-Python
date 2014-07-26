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
import os
import smtplib
import shutil
import time
import sys
import platform
from os.path import expanduser

def findHome():
    return expanduser("~")

path=findHome()+os.sep+"SiteAlert"+os.sep

def clearScreen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def visualizeMenu():
    clearScreen()
    print("What do you want to do?\n1) Display sites\n2) Add new site to check\n3) Fetch a site from the config file\n4) Check sites\n5) Delete a site\n6) Exit")

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

def findDirs():
    if not os.path.exists(path):
        os.mkdir(path)
    return os.listdir(path)

def displaySites():
    try:
        i=1
        print ("0) Exit")
        for dir in os.listdir(findHome()+os.sep+"SiteAlert"+os.sep):
            print (str(i)+") "+dir)
            i=i+1
    except OSError:
        return

def stdURL(site):
    if not site.startswith("http://"):
        site="http://"+site
    return site

def saveFile(path, site, mail, urli):
    fw = open(path, "w")
    fw.write(site)
    fw.write(mail)
    fw.write(str(urli.read()))
    fw.close()
    print ("Site saved correctly!")

def addSite(site, nameSite, mail):
    if site=="" or nameSite=="" or mail=="":
        print ("Insert the link for the site: ")
        site=input()+"\n"
        print ("Insert a name for the site: ")
        nameSite=input()
        print ("Insert the email where you want to be informed: (if you want to add other mail, separate them with \";\")")
        mail=input()+"\n"
    try:
        urli=urllib.request.urlopen(stdURL(site))
        responseCode=urli.getcode()
        if responseCode == 200:
            pathMod=path+nameSite+os.sep
            if not os.path.isdir(pathMod):
                if os.makedirs(pathMod):
                    print ("I can't create the necessary directory!")
                else:
                    saveFile(pathMod+"sito.txt", site, mail, urli)
            else:
                saveFile(pathMod+"sito.txt", site, mail, urli)
        elif responseCode == 404:
            print("This page doesn't exist!")
        else:
            print ("Generic error.")
    except urllib.request.URLError:
        print ("There is an error with the link.")

def sendMail(site,dir,mail):
    try:
        server = smtplib.SMTP("smtp.gmail.com:587")
        server.starttls()
        server.login("SiteAlertMailNotification@gmail.com","SiteAlertMailNotificatio")
        subj = "The site \""+dir+"\" has been changed!"
        msg = "Subject: "+subj+"\n"+subj+"\nLink: "+site
        mail=mail.split(";")
        for address in mail:
            server.sendmail("SiteAlertMailNotification@gmail.com",address,msg)
        server.close()
    except smtplib.SMTPRecipientsRefused:
        print ("Error with the e-mail destination address.")

def checkSite():
    list=os.listdir(path)
    if len(list)!=0:
        for dir in list:
            pathMod=path+dir+os.sep+"sito.txt"
            f=open(pathMod,"r");
            site=f.readline()
            mail=f.readline()
            urli=urllib.request.urlopen(stdURL(site))
            if f.read()==str(urli.read()):
                print ("The site \"" + dir + "\" hasn't been changed!")
            else:
                print ("The site \"" + dir + "\" has been changed!")
                addSite(site,dir,mail)
                sendMail(site,dir,mail)
            f.close()
    else:
        print ("You haven't checked any site.")
        return True
    return False

def numberReq(leng):
    s=-1
    displaySites()
    while s < 0 or s > leng:
        print ("Number of the site: ",)
        s=int(input())
    return s

def main():
    while True:
        x = choice()
        clearScreen()
        dirs=os.listdir(path)
        leng= len(dirs)
        if x==1:
            if leng!=0:
                displaySites()
            else:
                print ("You haven't checked any site!")
        elif x==2:
            addSite("","","")
        elif x==3:
            if leng != 0:
                print ("Write the number of the site that you want to fetch.")
                s=numberReq(leng)-1
                pathMod=path+dirs[s-1]+os.sep+"sito.txt"
                if os.path.exists(pathMod):
                    f=open(pathMod,"r")
                    addSite(f.readline(),dirs[s],f.readline())
                    f.close()
                else:
                    print ("No configuration file found.")
            else:
                print ("You haven't checked any site.")
        elif x==4:
            print ("Do you want to check it continually? (Y/n)")
            s=input()
            while len(s) == 0 or ( s[0] != 'n' and s[0] != 'y'):
                if len(s) == 0:
                    s="y"
                    break
                else:
                    print ("Wrong input, do you want to check it continually? (Y/n)")
                    s=input()
            while True:
                if checkSite() or s!="y":
                    s="n"
                    break
                else:
                    time.sleep(30)
        elif x==5:
            if leng != 0:
                print ("Write the number of the site that you want to delete.")
                s=numberReq(leng)-1
                pathMod=path+dirs[s]+os.sep
                try:
                    shutil.rmtree(pathMod, ignore_errors=True)
                    print ("Site successfully deleted!")
                except shutil.Error:
                    print ("Something went wrong.")
            else:
                print ("You haven't checked any site!")
        elif x==6:
            sys.exit(0)
        input("Press enter to continue...")

if __name__ == "__main__":
    main()