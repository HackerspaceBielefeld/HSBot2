#!/usr/bin/python
# -*- coding: utf-8 -*-

import csv
import requests
from bs4 import BeautifulSoup

outPutFile = open('scraped.csv','w')
outPutWriter = csv.writer(outPutFile)
page = requests.get('https://hackerspace-bielefeld.de')
soup = BeautifulSoup(page.content,'html.parser')

times = soup.find_all("span",class_="ai1ec-event-time")
topics =  soup.find_all("span",class_="ai1ec-event-title")
months = soup.find_all("div",class_="ai1ec-month")
days = soup.find_all("div", class_="ai1ec-day")
weekdays = soup.find_all("div",class_="ai1ec-weekday")
years = soup.find_all ("div",class_="ai1ec-year")
listall = list();
for x in range(0,len(times)):
      listentry = list()
      listentry.append(times[x].text.encode('utf-8').strip())
      listentry.append(topics[x].text.encode('utf-8').strip())
      listentry.append( months[x].text.encode('utf-8').strip())
      listentry.append( days[x].text.encode('utf-8').strip())
      listentry.append( weekdays[x].text.encode('utf-8').strip())
      listentry.append( years[x].text.encode('utf-8').strip())
      listall.append(listentry)


for listentry in listall:
     outPutWriter.writerow(listentry)

outPutFile.close()
