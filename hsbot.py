#!/usr/bin/python
# -*- coding: utf-8 -*-
import json,os,sys,logging,socket
from thread import start_new_thread as thread
from subprocess import call
from time import sleep,localtime,time
from Tkinter import *
from random import randint,randrange

import sleekxmpp
from optparse import OptionParser

import RPi.GPIO as g
#import GPdummy as g #brauch ich wenn ich per VM teste weils da kein GPIO gibt

import paho.mqtt.client as mossub
import paho.mqtt.publish as mospub

import config as c

lastStatus = 0 # wann das letzte mal der space status geändert wurde
prioToast = False # wenn ein prioritäts Toast da ist werden sachen wie countdown ausgeblendet
lastTrain = 0 #letzter Zeug
lastMoin = 0 #wann das letzte mal begrüßt wurde
noPony = 0 #Bis wann keine Ponychat nachrichten mehr kommen sollen
sensors = {} #gesendete sensorik
ponyPressed = 0

#gpio einstellungen
g.setwarnings(False)
g.setmode(g.BOARD)

# erkennt und verteilt befehle weiter
def befehl(nick,msg):
	b = str(msg).split(" ",1)
	b[0] = b[0].lower()
	
	if len(b) == 2:
		param = b[1]
	else:
		param = '';
	try:
		if b[0] == ':ponies':
			thread(makePony,(param,))
		elif b[0] == ':status':
			thread(makeStatus,())
		elif b[0] == ':toast':
			jabber.sendTo("[TOAST] "+ nick +" mag Toast")
			thread(makeToast,(param,10))
		elif b[0] == ':trains':
			makeTrains(nick)
		elif b[0] == ':countdown':
			thread(makeCountdown,(nick,param))	
		elif b[0] == ':blink':
			if param == '!':
				io.blink_stop()
			else:
				io.blink_start(int(param),0.1)
		elif b[0] == ':sensor':
			thread(makeSensor,(param,))
	except:
		pass
		
def makeMoin(nick):
	global lastMoin
	sleep(2)
	try:
		if nick in open(c.CACPATH+'/moin.txt').read():
			if lastMoin < (time()-300):
				jabber.sendTo("[GREETING] Hallo")
				lastMoin = time()
		else:
			with open(c.CACPATH+'/moin.txt', "a") as myfile:
				myfile.write(nick+";")

			jabber.sendTo("[GREETING] Hallo "+nick+". Ich bin hier der Bot. Was können wir für dich tun? Bitte bedenke, dass wir nicht immer sofort antworten können, bleib also einfach online, wir antworten schon früher oder später.")
			lastMoin = time()
	except:
		jabber.sendTo("[GREETING] Hi "+nick+"!")
		
	mospub.single(c.MQTTDEBU, payload="moin", hostname=c.MQTTSRV)
	
def makePony(p):
	global noPony
	global ponyPressed
	global sensors

	ponyPressed = ponyPressed +1
	sensors['pony_faktor/innen'] = randint(-1000,2000) * randint(1,ponyPressed) / 10

	if p == "!":
		noPony = time() + 7200
	else:
		x = 1
		r = randrange(0,x)
		if r == 0:
			if noPony < time():
				jabber.sendTo("[PONIES] Ponies wurden an die USA ausgeliefert.")
			makeFullImg('/media/pony.png',10)
		elif r == 1:
			if noPony < time():
				jabber.sendTo("[PONIES] Ponies!!!!!!")
			makeFullAni('/media/pony1.gif')
		elif r == 2:
			if noPony < time():
				jabber.sendTo("[PONIES] PONYPONYPONY")
			makeFullAni('/media/pony2.gif')
		mospub.single(c.MQTTDEBU, payload="pony", hostname=c.MQTTSRV)
		
def makeTrains(nick):
	global lastTrain
	global jabber

	if lastTrain < (time()-300):
		lastTrain = time()
		jabber.sendTo("[TRAIN] "+ nick +" mag Züge")
	
	sleep(5)
	antw = ("Zug hat verspätung."
	, "Zug macht Pause."
	, "Zug hat keine Lust."
	, "Im Zug ist die Heizung ausgefallen."
	, "Zugtüren lassen sich nicht schließen."
	, "Zug heute in umgekehrter Reihenfolge."
	, "Zug heute abweichend von Gleis 2 auf Gleis 238."
	, "Zugbeleuchtung wurde auf halbdunkel gestellt,damit wir noch genug Strom für die Klimaanlagen haben."
	, "Bitte stellen sie keine Gepäckstücke vor die Türen, diese dienen dem Zugpersonal als Fluchtweg."
	, "Sehr geehrte Fahrgäste, heute bekommen sie für ihr Geld 20Minuten mehr Fahrzeit geboten."
	, "Sollten sie auf der Suche nach Wagen 9 sein, den haben wir heute ganz geschickt zwischen Wagen 5 und 6 versteckt."
	, "Weitere Informationen entnehmen sie bitte dem Zugpersonal."
	, "Bitte nehmen sie Ihre Regenschirme wieder mit. Die Bahn hat mittlerweile ausreichend."
	, "Im gesamten Zug herrscht absolutes Nichtraucherverbot."
	, "For Anschluss-Connections please listen to the Lautsprecheransagen"
	, "Ich bitte um Gehör: die 8 Minuten für das Baguette sind um."
	, "Liebe Fahrgäste, heute steht das S in S-Bahn für schleichen!"
	, "Wir haben den Bahnhof mit Verspätung verlassen, da die Verkehrsleitung mir nicht gesagt hat, dass ich diesen Zug fahren darf."
	, "Bitte niemand aussteigen! Außer die Frau, die eigentlich nach Nürtingen will. Die darf."
	, "Der Zug verspätet sich auf Grund eines liegen gebliebenen Zugbegleiters."
	, "Bitte beachten Sie: W-Lan benötigt keine Steckverbindung."
	, "Für alle neu zugestiegenen Fahrgäste ohne Platzreservierung: willkommen auf unserer Stehparty!"
	, "Der Zug vor uns hat zwar 800 PS mehr als wir, aber dafür fünf Türen weniger. Da dauert das Ein- und Aussteigen!"
	, "Denken Sie an Pinguine! Dann ist die kaputte Klimaanlage nicht so schlimm."
	, "Weil 50 Leute an einer Tür einsteigen, verzögert sich die Abfahrt. Wir bitten diese Dummheit zu entschuldigen."
	, "Durch eine äußerst seltene Verkettung glücklicher Umstände werden wir unser Ziel unerwartet plangemäß erreichen."
	, "Auf Klo 1 bitte den richtigen Spülknopf benutzen und nicht permanent den Notfall-Knopf drücken!"
	, "Wenn die Damen die Modenschau unterlassen und die Tüten aus den Türen nehmen würden, könnten wir weiterfahren."
	, "Nachdem wir uns den Güterbahnhof Wanne-Eickel angucken durften, jetzt noch der Exklusiv-Anblick eines Güterzuges vor uns."
	, "Soeben ist unsere ofenfrische Brezelverkäuferin zugestiegen. Sie möchte Sie im Speisewagen gerne erwarten."
	, "Reisende, die sportlich unterwegs sind und nicht zu viel Gepäck haben, sollten den Anschlusszug noch erreichen."
	, "Müll und Ehemänner bitte nicht im Zug zurücklassen! Vielen Dank."
	, "Das ist nicht der Knopf für die Freisprechanlage. - Doch. Wenn ich's dir doch sage. Das ist der Knopf!"
	, "Dies ist ein Personenzug, kein Güterzug. Im Güterzug ist es egal, wenn die Schweine ihre Beine oben haben. Hier nicht!"
	, "Wenn Ihre Kopfhörer nicht dicht sind, schalten Sie das Geschrammel lieber ab. Sonst drehe ICH mal auf!"
	, "Guten Tag meine Damen und Herren, im Namen der Deutschen Bahn muss ich Sie auf der Reise im Zug nach Köln begrüßen."
	, "Ich weise darauf hin, dass unsere Bremsen nicht funktionieren. Nächster Halt? Dort wo wir ausgerollt sind!"
	, "Der Zug des Lokführers ist ausgefallen. Er kommt jetzt mit dem Taxi."
	, "Die Kollegen im Bistro geben wieder alles. Ich habe vorhin ein Stück Kuchen gegessen und würde Ihnen raten, das auch zu tun.")
	jabber.sendTo("[TRAIN] "+ antw[randrange(0,len(antw)-1)])
	mospub.single(c.MQTTDEBU, payload="train", hostname=c.MQTTSRV)

# zeigt den countdown mit low prio (bedeutet, wenn tost kommt wird der countdown ausgesetzt)
def makeCountdown(nick,timecode):
	global toast
	global prioToast
	
	
	#mospub.single(c.MQTTDEBU, payload="countdown start", hostname=c.MQTTSRV)

	time = str(timecode).split(":")
	l = len(time)
	m = 0
	if(l == 3):
		m = int(time[0])*3600+int(time[1])*60+int(time[2])
	elif(l == 2):
		m = int(time[0])*60+int(time[1])
	elif(l == 1):
		m = int(time[0])
	
	#toast.grid_remove()
	if m > 0:
		while m > 0:
			if not prioToast:
				mod = m%3600
				std = (m-mod)/3600
				sek = mod%60
				min = (mod-sek)/60

				c = ""
				if std > 0:
					if std < 10:
						c = c+"0"+str(std)+":"
					else:
						c = c+str(std)+":"

				if min < 10:
					c = c+"0"+str(min)+":"
				else:
					c = c+str(min)+":"

				if sek < 10:
					c = c+"0"+str(sek)
				else:
					c = c+str(sek)

				toast.grid(row=0,column=0)
				to.set(str(c))
			sleep(1)
			debugMsg("[COUNTDOWN] "+ str(m))
			m=m-1
		jabber.sendTo("[COUNTDOWN] @"+nick +" Dein Countdown ist abgelaufen.")
		#mospub.single(c.MQTTDEBU, payload="countdown end", hostname=c.MQTTSRV)
		toast.grid_remove()

#sendet toast an display
def makeToast(msg,time):
	global toast
	global to
	global prioToast
	
	
	prioToast = True
	try:
		mospub.single(c.MQTTTOPTOUT, payload=msg, hostname=c.MQTTSRV)
	except:
		pass
	to.set(str(msg))
	toast.grid(row=0,column=0)
	sleep(time)
	toast.grid_remove()
	prioToast = False
	
#zeigt ein fullscreen bild
def makeFullImg(img, sec):
	global f
	
	photo = PhotoImage(file=os.path.dirname(os.path.realpath(__file__)) + img)
	fulli = Label(image=photo)
	fulli.grid(row=0,column=0,rowspan=3,columnspan=3)
	sleep(sec)
	fulli.grid_remove()
	
# stellt gif animation einmal da
def makeFullAni(img,wait=0.04):
	global f
	okay = True
	num = 0

	photo = PhotoImage(file=os.path.dirname(os.path.realpath(__file__)) + img, format="gif - {}".format(num))
	fulli = Label(image=photo)
	fulli.grid(row=0,column=0,rowspan=3,columnspan=3)
	sleep(0.2)
	
	while okay:
		try:
			sleep(wait)
			photo = PhotoImage(file=os.path.dirname(os.path.realpath(__file__)) + img, format="gif - {}".format(num))
			fulli.configure(image = photo)
			fulli.image = photo

			num += 1
			debugMsg("[GIF]"+img+" - "+str(num))
		except:
			okay = False
			debugMsg("[GIF]"+img+" - end")

	fulli.grid_remove()

#sendet zurück welchen Status der Space grade hat	
def makeStatus():
	if g.input(15):
		jabber.sendTo("[STATUS] Der Space ist aktuell geschlossen.")
	else:
		jabber.sendTo("[STATUS] Der Space ist aktuell geöffnet.")
	
def makeSensor(pattern):
	global sensors
	keys = sensors.keys()
	s = ""
	for k in keys:
		if k.startswith(pattern):
			s = s +"\n"+ str(k) +": "+ str(sensors[k])
		
	jabber.sendTo("[SENSOR]"+ s)
	
def setTopic(tpc):
	pass
	
#def incMsg(msg,nick=''):
#	if not nick == '':
#		msg = nick+": "+msg
	#todo

# schliebs ne nachricht über mqtt topic debug
def debugMsg(msg,fkt='DEBUG-BOT'):
	pl = "["+str(fkt)+"]: "+str(msg)
	if c.DEBUG >= 2:
		print(pl)
	if c.DEBUG >= 1:
		mospub.single(c.MQTTDEBU, payload=pl, hostname=c.MQTTSRV)

#mosquito Klasse
class MQTT():
	client = mossub.Client()

	print("MQTT start")	
	def __init__(self):
		self.client = mossub.Client()
		self.client.on_connect = self.on_connect
		self.client.on_message = self.on_message
		
	def run(self):
		self.client.connect(c.MQTTSRV, 1883, 60)
		while True:
			print("MQTT loop")
			self.client.loop_forever()

	def on_connect(self,client, userdata, flags, rc):
		debugMsg("MQTT Start: "+str(rc))
		self.client.subscribe(c.MQTTTOPI)
		self.client.subscribe(c.MQTTTOPJ)
		self.client.subscribe(c.MQTTTOPT)
		self.client.subscribe(c.MQTTSENSOR+"/#")
		self.client.subscribe("test")

	def on_message(self,client, userdata, msg):
		debugMsg("MQTT Msg: "+msg.topic+" "+str(msg.payload))
		if(msg.topic == c.MQTTTOPT):
			makeToast(msg.payload,10)
			
		if msg.topic == 'test' and msg.payload == 'blue':
			thread(makeFullImg,('/media/bluescreen.png',10))
			print("trigger Blue")
		
		if msg.topic == 'test' and msg.payload == 'red':
			thread(makeFullAni,('/media/test.gif',0.04))
			
		if msg.topic == 'test' and msg.payload == 'virus':
			thread(makeFullAni,('/media/id4-virus.gif',0.04))

		if msg.topic == c.MQTTTOPI or msg.topic == c.MQTTTOPJ:
			sendMsg("[MQTT]: "+str(msg.payload))
			
		if msg.topic == c.MQTTTOPC:
			global jabber
			jabber.sendTo("[MQTT]: "+ str(msg.payload))
			
		if msg.topic.startswith(c.MQTTSENSOR):
			global sensors
			l = len(c.MQTTSENSOR)+1
			sname = msg.topic[l:]
			swert = msg.payload
			sensors[sname] = swert
			

	def incMsg(msg,nick=''):
		pass

# xmpp klasse
class Jabber(sleekxmpp.ClientXMPP):
	logging.basicConfig(level=logging.ERROR)
	XMPP_CA_CERT_FILE = c.JCERT		#Setze Certificat fuer xmpp
	auto_reconnect = True

	def __init__(self):
		sleekxmpp.ClientXMPP.__init__(self, c.JUSER, c.JPASS)
		self.register_plugin('xep_0030') # Service Discovery
		self.register_plugin('xep_0045') # Multi-User Chat
		self.register_plugin('xep_0199') # XMPP Ping
		
	def run(self):
		self.newSession()
		sleep(10)
		vers = open('version.txt').read()
		self.sendTo("[STATUS] Reboot erfolgreich... (HSBot "+vers[:-1]+")")
		
		while True:
			sleep(30)
			self.send_presence()
				
	def newSession(self): 
		while not self.connect():
			sleep(0.1)
		self.process()

			
		self.add_event_handler("session_start", self.onStart)
		self.add_event_handler("groupchat_message", self.muc)
		self.add_event_handler("diconnected", self.newSession)
		#self.add_event_handler("groupchat_subject", self.onSubj)
		self.add_event_handler("presence_available",self.onPresence)
				
	def onStart(self, event):
		debugMsg('[start]')
		self.get_roster()
		self.send_presence()
		self.plugin['xep_0045'].joinMUC(c.JROOM, c.JNICK,wait=True)		
		
	def onPresence(self,event):
		#debugMsg('[presence]'+str(event['from'].bare))
		if event['from'].bare == c.JUSER:
			pass
			#io.blink_stop()
			#debugMsg('[timeup]'+ str(time()))
				
	def onSubj(self,event):
		if not event["muc"]["nick"] == c.JNICK:
			self.changeSubj(False)
		
	def sendTo(self,txt):
		debugMsg("[XMPP] "+str(txt))
		self.send_message(mto=c.JROOM,mbody=txt,mtype='groupchat')
		sendMsg(txt,txt,"bot")
		
	def sendPrivate(self,nick,text):
		self.send_message(mto=c.JROOM+"/"+nick,mbody=txt,mtype='groupchat')
		
	def changeSubj(self,subj):
		if subj:
			self.TOPIC = str(subj)

		self.send_raw("<message from='"+c.JROOM+"/"+c.JNICK+"' id='lh2bs617' to='"+c.JROOM+"' type='groupchat'><subject>"+self.TOPIC+"</subject></message>")
		
	def muc(self, msg):
		#try:
			if msg['mucnick'] != c.JNICK and msg['from'].bare.startswith(c.JROOM):
				t = localtime()
				h = t[3]
				if h < 10:
					h = "0"+ str(h)
				else:
					h = str(h)
					
				m = t[4]
				if m < 10:
					m = "0"+ str(m)
				else:
					m = str(m)
					
				s = t[5]
				if s < 10:
					s = "0"+ str(s)
				else:
					s = str(s)
					
				sendMsg(h+":"+m+" "+ msg['mucnick'] +": "+ msg['body'],h+":"+m+" "+ msg['mucnick'] +":","nick")
				if msg['body'].startswith(':'):
					befehl(msg['mucnick'],msg['body'])
				
				l = msg['body'].lower()
				if l.startswith("guten morgen") or l.startswith("moin") or l.startswith("hallo") or l.startswith("guten tag") or l.startswith("guten abend") or l.startswith("nabend") or l.startswith("hi ") or l.startswith("hi.") or l.startswith("hi!") or l.startswith("achja guten morgen"):
					makeMoin(msg['mucnick'])
				
		#except:
			pass
			
# diese klasse überwacht alle GPIO ports und reagiert nach wunsch
class IOPorts():
	blinking = False
	lastPony = 0

	def __init__(self):
		g.setup(11, g.OUT) #Botlampe
		g.setup(15, g.IN, pull_up_down=g.PUD_UP) #Botschalter Hi=off
		g.setup(13, g.IN, pull_up_down=g.PUD_UP) #Bottaster
		
		if g.input(15):
			#monitor off 
			call(["./monitor.sh","off"])
			g.output(11,0)
		else:
			#monitor on 
			call(["./monitor.sh","on"])
			g.output(11,1)
			thread(makeFullImg,('/media/bluescreen.png',10))
		
		g.add_event_detect(15, g.BOTH, callback=self.makeSpaceStatus, bouncetime=300)
		g.add_event_detect(13, g.FALLING, callback=self.doPony,bouncetime=30000)
		

	def doPony(self,ch):
		debugMsg(str(self.lastPony),'LASTPONY')
		if self.lastPony < (time()-10):
			self.lastPony = time()
			makePony("")

	def blinking(self,interval,ratio):
		while self.blinking:
			a = interval*ratio
			b = interval-a
			g.output(11,1)
			sleep(a)
			g.output(11,0)
			sleep(b)
		
	def blink_start(self,interval,ratio=0.5):
		self.blinking = True
		thread(self.blinking,(interval,ratio))

	def blink_stop(self):
		self.blinking = False
	
	def makeSpaceStatus(self,ch):
		if g.input(15):
			#monitor on 
			call(["./monitor.sh","off"])
			sleep(5)
			
			# spacestatus close
			call(['curl','-d status=close', "https://hackerspace-bielefeld.de/spacestatus/spacestatus.php"])
			
			# port 15 off
			g.output(11,0)
			
			
			# in chat schreiben, dass spcae geschlossen
			jabber.sendTo("[STATUS] Der Space ist nun geschlossen.")
			debugMsg("Space geschlossen")
		else:
			#monitor on 
			call(["./monitor.sh","on"])
			thread(makeFullImg,('/media/bluescreen.png',10))
			# etwas show
			#jabber.disconnect()
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			g.output(11,1)
			sleep(0.1)
			g.output(11,0)
			sleep(0.1)
			
			
			#jabber.newSession()
			# spacestatus open
			call(['curl','-d status=open', "https://hackerspace-bielefeld.de/spacestatus/spacestatus.php"])

			
			# port 11 on
			g.output(11,1)
			
			sleep(5)
			# in chat schreiben, dass space offen
			jabber.sendTo("[STATUS] Der Space ist nun geöffnet.")
			debugMsg("Space offen")
		lastStatus = time() #TODO

# GUI anlegen
f = Tk()
h = f.winfo_screenheight()
w = f.winfo_screenwidth()
debugMsg(w,h)

#Fenster
f.title('HSBot2')
f.geometry(str(w)+"x"+str(h)+"+0+0")
f.wm_overrideredirect(True)
f.resizable(False, False)
f.config(bg="#000000")

# Label-Variablen
ts = StringVar()
ts.set("XX:XX")

ti = StringVar()
ti.set("------------")

to = StringVar()
to.set("TOAST")

st = StringVar()
st.set("STATUS")

font = "Arial"

#Textfelder
chat = Text(f,bg="#000000",fg="#ffffff",font=(font,32),bd=2,height=19,width=29)
clock = Label(f,textvariable=ts,fg="#ffffff", bg="#000000", bd=2,font=("CyberFunk",135),width=5)
infoh = Label(f,textvariable=ti,fg="#ffffff", bg="#000000",font=("fraulein hex",51))
infot = Text(f,bg="#000000",fg="#ffffff",font=(font,24),bd=2,height=18,width=22)	
toast = Label(f,textvariable=to,fg="#ffffff", bg="#000000", bd=2,font=(font,108),width=8)
status = Label(f,textvariable=st,fg="#ffffff", bg="#000000", bd=2,font=(font,32))


chat.tag_add("all", "1.0", END)
chat.tag_config("all",wrap=WORD)
chat.tag_config('bot',foreground='#ddffdd')
chat.tag_config('nick',foreground='#ddddff')
chat.tag_config('sys',background='#007700')
chat.grid(row=0,column=0,rowspan=3,sticky=N,padx=7)

# Clock
clock.grid(row=0,column=1,sticky=NE)

# Info Header
infoh.grid(row=1,column=1,sticky=S)

# Info Text
infot.tag_config("all",wrap=WORD)
infot.grid(row=2,column=1,sticky=SE)
f.rowconfigure(2, minsize=548)

#status fußzeile
status.grid(row=3,column=0,columnspan=2,sticky=S)

data = "Chatfenster"

# sorgt fr die uhr
def getClock():
	global ts
	tag = (0,0,0)
	while True:
		lt = localtime()
		ts.set("%02i:%02i" % (lt.tm_hour,lt.tm_min))
		if not tag == lt.tm_mday:
			tag = lt.tm_mday
			sendMsg("[CLOCK] --- "+ str(lt.tm_mday) +"."+ str(lt.tm_mon) +". ---------------------","[CLOCK] --- "+ str(lt.tm_mday) +"."+ str(lt.tm_mon) +". ---------------------","sys")
		sleep(5)

# cycelt infos durch
def getInfo():
	global infot 
	global infoh
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
			infot.insert(END, infos[j])
			infot.tag_add("all", "1.0", END)
			ti.set(j)
			infot.update()
			sleep(30)
			
def getGWP():
	global st
	while True:
		try:
			with open (c.CACPATH+"/gwp.txt", "r") as myfile:
				tmp = " | ".join(myfile.readlines())
				st.set(tmp)
		except:
			pass
		sleep(60)
		#debugMsg("[SETSTATUS]")

	
#sendet nachricht an display	
def sendMsg(msg,colstr=False,tag="nothing"):
	global chat
	try:
		chat.insert(END, msg + "\n")
		chat.tag_add("all", "1.0", END)
		chat.see(END)
		if colstr:
			pos = chat.search(colstr,END,backwards=True)
			epos = pos.split('.')[0] +'.'+ str(len(colstr))
			#debugMsg(pos,epos)
			chat.tag_add(tag,pos,epos)
		chat.update()
		f.update_idletasks()
		mospub.single(c.MQTTTOPC, payload=msg, hostname=c.MQTTSRV)
	except:
		pass
	
io = IOPorts()
	
thread(getClock,())
thread(getInfo,())
thread(getGWP,())
print("preMQTT")
mqtt = MQTT()
jabber = Jabber()
thread(jabber.run,())
thread(mqtt.run,())




mainloop()
