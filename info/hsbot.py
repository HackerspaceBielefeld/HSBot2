#!/usr/bin/python
# -*- coding: utf-8 -*-
import json,os,thread,sys,logging
from thread import start_new_thread as thread
from subprocess import call
from time import sleep,localtime
from Tkinter import *

import sleekxmpp

from telegram import Updater,Bot
from optparse import OptionParser

import paho.mqtt.client as mossub
import paho.mqtt.publish as mospub

import config as c

def setTopic(tpc):
	pass
	
def incMsg(msg,nick=''):
	if not nick == '':
		msg = nick+": "+msg
	#todo

def debugMsg(msg,fkt=''):
	pl = "["+str(fkt)+"]: "+str(msg)
	mospub.single(c.MQTTDEBU, payload=pl, hostname=c.MQTTSRV)

class Jabber(sleekxmpp.ClientXMPP):
	logging.basicConfig(level=logging.ERROR)
	XMPP_CA_CERT_FILE = c.JCERT						#Setze Certificat fuer xmpp

	def __init__(self):
		sleekxmpp.ClientXMPP.__init__(self, c.JUSER, c.JPASS)
		self.register_plugin('xep_0030') # Service Discovery
		self.register_plugin('xep_0045') # Multi-User Chat
		self.register_plugin('xep_0199') # XMPP Ping
		
		self.newSession()
		
	def run(self):
		while True:
			sleep(60)
			self.get_roster()
			self.send_presence()
				
	def newSession(self):
		#print(str(localtime())+": session")
		if self.connect():#use_ssl=True):
			self.process()

			self.add_event_handler("session_start", self.start)
			self.add_event_handler("groupchat_message", self.muc)
			self.add_event_handler("diconnected", self.newSession)
			#self.add_event_handler("got_online", self.onOnline)
			#self.add_event_handler("got_offline", self.onOffline)
			#self.add_event_handler("groupchat_subject", self.onSubject)
			
	def start(self, event):
		self.get_roster()
		self.send_presence()
		self.plugin['xep_0045'].joinMUC(c.JROOM, c.JNICK,wait=True)		
		
	def onSubject(self,event):
		if not event["muc"]["nick"] == c.JNICK:
			self.changeSubj(False)
		
	def onOnline(self,event):
		if len(event['muc']['nick']) <25:
			print(event['muc']['nick'] +" online ...")
		
	def onOffline(self,event):
		if len(event['muc']['nick']) <25:
			print(event['muc']['nick'] +" offline ...")
		
	def sendTo(self,text):
		if nick == c.JNICK:
			txt = text
		else:
			txt = nick +": "+ text
			
		self.send_message(mto=c.JROOM,mbody=txt,mtype='groupchat')
		
	def sendPrivate(self,nick,text):
		self.send_message(mto=c.JROOM+"/"+nick,mbody=txt,mtype='groupchat')
		
	def changeSubj(self,subj):
		if subj:
			self.TOPIC = str(subj)

		self.send_raw("<message from='"+c.JROOM+"/"+c.JNICK+"' id='lh2bs617' to='"+c.JROOM+"' type='groupchat'><subject>"+self.TOPIC+"</subject></message>")
		
	def muc(self, msg):
		if msg['mucnick'] != c.JNICK and msg['from'].bare.startswith(c.JROOM):
			sendMsg(msg['body'],'jabber',msg['mucnick'])
	
class MQTT():
	def __init__(self):
		client = mossub.Client()
		client.on_connect = self.on_connect
		client.on_message = self.on_message

		client.connect(c.MQTTSRV, 1883, 60)
		thread.start_new_thread(client.loop_forever,())

	def on_connect(self,client, userdata, flags, rc):
		print("MQTT Start: "+str(rc))
		client.subscribe(c.MQTTTOP)

	def on_message(self,client, userdata, msg):
		print("MQTT Msg: "+msg.topic+" "+str(msg.payload))
		sendMsg(str(msg.payload),'mqtt',"[MQTT]")
		
	def incMsg(msg,nick=''):
		pass

class Telegram():
	FOLLOWER = ()
	NAME = "telegram"

	def __init__(self):
		updater = Updater(token=c.TOKEN)
		dispatcher = updater.dispatcher
		f = open(c.TFILE, 'r')
		self.FOLLOWER = f.read().split(",")
		f.close()
		if "" in self.FOLLOWER:
			while "" in self.FOLLOWER:
				self.FOLLOWER.remove("")
			f = open(c.TFILE, 'w')
			f.write(",".join(self.FOLLOWER))
			f.close()

		dispatcher.addTelegramCommandHandler('delete', self.deleteme)
		dispatcher.addTelegramCommandHandler('add', self.addme)
		dispatcher.addTelegramMessageHandler(self.echo)
		dispatcher.addUnknownTelegramCommandHandler(self.notunderstand)

		start_new_thread(updater.start_polling,(5,))

	def echo(self,bot, update):
		#print(update)
		sID = str(update.message.chat.id)
		sName = update.message.chat.first_name
		sText = update.message.text
		#TODO hier fehlt irgendwie die sender var
		print(sID)
		print(sName)
		print(sText)
		self.sendPublic(sName+": "+sText,bot,sID)
		self.toController(sText,sName)

	def deleteme(self,bot,update):
		#print("d")
		user = str(update.message.chat_id)
		#print("user: "+user)
		#print("follower: "+str(self.FOLLOWER))
		if user in self.FOLLOWER:
			#print("ja")
			while user in self.FOLLOWER:
				self.FOLLOWER.remove(user)
				print("entferne")
			f = open(c.TFILE, 'w')
			f.write(",".join(self.FOLLOWER))
			f.close()
			#print("follower: "+str(self.FOLLOWER))
			self.sendPrivat(update.message.chat_id,"Bis Bald ...",bot)
		else:
			self.sendPrivat(update.message.chat_id,"Du bist nicht in meiner Liste.",bot)

	def addme(self,bot,update):
		#print("a")
		user = str(update.message.chat_id)
		if user in self.FOLLOWER:
			self.sendPrivat(update.message.chat_id,"Du bist schon in meiner Liste.",bot)
			
		else:
			f = open(c.TFILE, 'a')
			if len(self.FOLLOWER) == 0:
				f.write(str(user))
			else:
				f.write(","+str(user))                  
			f.close()
			self.FOLLOWER.append(user)
			#print("follower: "+str(self.FOLLOWER))
			self.sendPrivat(update.message.chat_id,"Du wurdest hinzugefügt.",bot)

	def notunderstand(self,bot,update):
		bot.sendMessage(chat_id=update.message.chat_id, text="/add : dich anmelden\n/delete : dich abmelden")

	def sendPublic(self,sendtext,bot=False,sender=0):
		#print("3")
		if not bot:
			#print("6")
			bot = Bot(token=c.TOKEN)
		#print("7")
			
		if sender == 0 or sender in self.FOLLOWER:
			#print("4")
			for i in self.FOLLOWER:
				if i != sender:
					#print("1")
					bot.sendMessage(chat_id=i, text=sendtext)
		else:
			#print("5")
			self.sendPrivat(sender,"Du bist nicht teil der Gruppe: tippe /add um beizutreten",bot)

	def sendPrivat(self,reciever,sendtext,bot=False):
		if not bot:
			bot = Bot(token=c.TOKEN)
		#print("Privat: "+sendtext)
		bot.sendMessage(chat_id=reciever, text=sendtext)

	def heartbeat(self):
		return True
	
	def sendTo(self,nick,uid,text):
		if nick == c.JNICK:
			txt = text
		else:
			txt = nick +": "+ text
			
		self.sendPublic(txt)
		
	def toController(self,text,nick):
		HOST = '127.0.0.1'
		PORT = c.CMSGPORT
		
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((HOST, PORT))
			data = {'service':self.NAME,'text':str(text),'nick':str(nick)}
			s.sendall(json.dumps(data))
			data = s.recv(1024)
			s.close()
			return data
		except Exception as e:
			print("ERROR")
			print(e)
			print(sys.exc_info()[0])	
			return False

f = Tk()
h = f.winfo_screenheight()
w = f.winfo_screenwidth()

#Fenster
f.title('HSBot2')
f.geometry(str(w)+"x"+str(h)+"+0+0")
f.wm_overrideredirect(True)
f.resizable(False, False)
f.config(bg="#000000")

#Variablen
ts = StringVar()
ts.set("XX:XX")

ti = StringVar()
ti.set("------------")

chat = Text(f,bg="#000000",fg="#ffffff",font=("Arial",32),bd=2,height=20,width=29)

clock = Label(f,textvariable=ts,fg="#ffffff", bg="#000000", bd=2,font=("Arial",108),width=5)

infoh = Label(f,textvariable=ti,fg="#ffffff", bg="#000000",font=("Arial",32))

infot = Text(f,bg="#000000",fg="#ffffff",font=("Arial",24),bd=2,height=19,width=22)
	

chat.tag_add("all", "1.0", END)
chat.tag_config("all",wrap=WORD)
chat.grid(row=0,column=0,rowspan=3,sticky=NW)

# Clock
clock.grid(row=0,column=1,sticky=NE)

# Info Header
infoh.grid(row=1,column=1,sticky=S)

# Info Text
infot.tag_config("all",wrap=WORD)
infot.grid(row=2,column=1,sticky=SE)
f.rowconfigure(2, minsize=548)

data = "Chatfenster"



def getClock():
	while True:
		lt = localtime()
		ts.set("%02i:%02i" % (lt.tm_hour,lt.tm_min))
		f.update_idletasks()
		sleep(5)

def getInfo():
	while True:
		infos = {}
		tmp = os.listdir(c.INFPATH)
		for i in tmp:
			if not i.startswith(".") and i.endswith('.txt'):
				with open (c.INFPATH+"/"+i, "r") as myfile:
					data="".join(myfile.readlines())
					infos[i[:-4]] = data
			
		for j in infos:
			infot.delete("1.0",END)
			#infot.tag_config("all",wrap=WORD)
			infot.insert(END, infos[j])
			infot.tag_add("all", "1.0", END)
			ti.set(j)
			infot.update()
			sleep(10)

def sendMsg(msg,service='',nick=''):
	global jabber;
	
	if nick == '' or nick == c.JNICK:
		data = str(msg)
	else:
		data = str(nick) +": "+ str(msg)
		
	if not service == 'jabber':
		jabber.sendTo(data)
		
	chat.insert(END, data + "\n")
	chat.tag_add("all", "1.0", END)
	chat.see(END)
	chat.update()

	f.update_idletasks()
	
thread(getClock,())
thread(getInfo,())
jabber = Jabber()
thread(jabber.run,())

mainloop()