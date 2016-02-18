#userhost interpreted as unknown
#xircon doesnt load names list
#mirc wont show privmsg to channel from all users
from twisted.protocols import basic
import re, socket, copy, os.path

class channel:
  pass

class occupant:
  pass

channels = {}
users = {}

hostname = "inhahe.kicks-ass.net"
version = "PyIRCd-RAN-0.1"
network = "inhahe"

automotd=True

maxchannels = 20
nicklen = 60
maxbans=100
maxchannels=32
channellen=60
topiclen=300
maxexcepts=46
maxinvites=46
maxusers=1000
tmaxdccallow = None
tmaxjoin = None
tmaxkick = None
tmaxnotice = None
tmaxpart = None
tmaxprivmsg = None
tmaxwhois  = None
tmaxwhowas = None

last_channel_number = 0

def matchhost(mask, nick, user, host):
  a=""
  for x in mask:
    if x in "[]{}\.^$+()": x="\\"+x
  if x=="?": x="."
  if x=="*": x=".*"
  return re.match(mask, nick+"!"+user+"@"+host)

class MyChat(basic.LineReceiver):

    def __init__(self):
        self.delimiter='\n'

    def connectionMade(self):
        self.number = len(self.factory.clients)
        self.factory.clients.append(self)
        self.registered = False
        self.nick = None
        self.invisible = False
        self.wallops = False
        self.realname = None
        self.user = None
        self.channels = {}
        self.invites = {}
        self.host = socket.gethostbyaddr(self.transport.hostname)[0]
        self.glop = False #global op
        self.lop = False  #local op
        self.invisible_joinpart = False
        self.hide_oper = False
        self.kix = False
        self.regged = False
        self.no_non_reg = False
        self.whois_paranoia = False
        self.away = False
        print self.number, "connected (%s)" % self.host

    def connectionLost(self, reason):
        print self.number, "disconnected"
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        global last_channel_number

        def motd(self):
          self.send(":%s 375 %s :- %s Message of the day - " % (hostname, self.nick, hostname))
          if os.path.isfile("motd.txt"):
            for line in open("motd.txt","r").readlines():
              self.send(":%s 372 %s :- %s" % (hostname, self.nick, line))
          self.send(":%s 376 %s :End of MOTD command" % (hostname, self.nick))

        def welcome():
#         self.send(":%s 001 %s :%s" % (hostname, self.nick, "You are here."))
          self.send(":%s 001 %s :Welcome to the Internet Relay Network %s!%s@%s" % (hostname, self.nick, self.nick, self.user, self.host))
          self.send(":%s 002 %s :Your host is %s" % (hostname, self.nick, hostname))
          self.send(":%s 003 %s :This server was created Mon Dec 12 2005 at 14:52:32 EST" % (hostname, self.nick))
          self.send(":%s 004 %s %s wioOIHqrRWa iItkmRnALloeb" % (hostname, self.nick, version)), 
          self.send(":%s 005 %s NETWORK=%s MAXBANS=%d MAXCHANNELS=%d CHANNELLEN=%d TOPICLEN=%d CHANLIMIT=#:%d NICKLEN=%d CHANTYPES=# PREFIX=(ov)@+ STATUSMSG=@+" % (hostname, network, maxbans, maxchannels,topiclen, channellen, topiclen, maxchannels, nicklen))
          self.send(":%s 005 %s CASEMAPPING=ascii EXCEPTS CHANMODES=iItkmRnALloeb MAXLIST=b:%d,e:%d,I:%d          TARGMAX=DCCALLOW:%s,JOIN:%s,KICK:%s,NOTICE:%s,PART:%s,PRIVMSG:%s,WHOIS:%s,WHOWAS:%s :are available on this server" % (hostname, self.nick, maxbans, maxexcepts, maxinvites,          ['',str(tmaxdccallow)][tmaxdccallow!=None], ['',str(tmaxjoin)][tmaxjoin!=None], ['',str(tmaxkick)][tmaxkick!=None], ['',str(tmaxnotice)][tmaxnotice!=None], ['',str(tmaxpart)][tmaxpart!=None],['',str(tmaxprivmsg)][tmaxprivmsg!=None],['',str(tmaxwhois)][tmaxwhois!=None],['',str(tmaxwhowas)][tmaxwhowas!=None]))
          self.send(":%s 251 %s :There are %d users and %d invisible on 1 server" % (hostname, self.nick, len([x for x in users.values() if not x.invisible]), len([x for x in users.values() if x.invisible])))
          self.send(":%s 252 %s %d :IRC Operators online" % (hostname, self.nick, len([x for x in users.values() if x.glop or x.lop])))
          self.send(":%s 253 %s %d :unknown connections" % (hostname, self.nick, len([x for x in self.factory.clients if not x.registered])))
          self.send(":%s 254 %s %d :channels formed" % (hostname, self.nick, len(channels)))
          self.send(":%s 255 %s :I have %d clients and 1 servers" % (hostname, self.nick, len(self.factory.clients)))
          self.send(":%s 265 %s :Current local users: %d Max: %d" % (hostname, self.nick, len(users), maxusers))
          self.send(":%s 266 %s :Current global users: %d Max: %d" % (hostname, self.nick, len(users), maxusers))
          if automotd: motd(self)

        print "%d>" % self.number, line
        prefix = None
        if line[0]==':':
          if " " not in line:
            self.send("431")
            return
          prefix, line = line[1:].split(" ", 1)
        command, params1 = line.split(" ", 1)
        command = command.upper()
        if params1[0]==":":
          params = [params1[1:]]
        else:
          params2=params1.split(" :",1)
          params = params2[0].split()
          if len(params2)==2: params.append(params2[1])
        if command=="NICK":
          if not len(params): self.send("431") #fix
          nick = params[0]
          if nick.lower() in users: self.send("433") #fix
          else:
            if len(nick) > nicklen:
              self.send(":%s 432 %s :Nickname too long." % (hostname, nick))
              return
            for x in nick:
              if x in ":":
                self.send("432")#fix
                return
              if ord(x)<=32:
                self.send("432")#fix
                return
            users[nick]=self
            oldnick, self.nick = self.nick, nick
            if self.registered:
              del users[oldnick]
              for n in set([x for y in users[nick].channels for x in y.keys()]):
                users[n].send(":%s!%s@%s NICK :%s" % (self.nick, self.user, self.host, nick))
            else:
              if self.user:
                welcome()
                self.registered=True
 
        elif command=="USER":
          if len(params)<4:
            self.send("461")
            return
          try:
            a = int(params[1])
            self.wallops = a % 2
            self.invisible = ((a & 2) == 2)
          except:
            pass
          self.realname = params[3]
          self.user = params[0]
          if self.nick:
            users[self.nick]=self
            self.registered=True
            welcome()

        elif command=="JOIN":
          if not self.registered:
            self.send("451 JOIN :First issue NICK and USER commands")
            return
          if params==[]:
            self.send("431")
            return
          chans = params[0].split(",")
          keys = None
          if len(params)>1: keys=params[1].split(",")
          for index, name in enumerate(chans):
            chan = name.lower()
            if chan=="0":
              for chan in self.channels:
                for nick, data in channels[chan].users.items():
                  data.connection.send(":%s!%s@%s PART %s" % (self.nick, self.user, self.host, chan))
                del channels[chan].users[self.nick]
              continue
            if not chan in channels:
              channels[chan] = channel()
              channels[chan].users = {}
              channels[chan].users[self.nick] = occupant()
              channels[chan].users[self.nick].connection = self
              channels[chan].users[self.nick].o = True  #op
              channels[chan].users[self.nick].v = False #voiced
              channels[chan].users[self.nick].q = False #quieted
              channels[chan].i = False #invite-only
              channels[chan].I = None  #invitation_mask
              channels[chan].t = False #topic locked
              channels[chan].k = None  #key
              channels[chan].b = {}    #bans
              channels[chan].e = {}    #exceptions
              channels[chan].l = None  #limit
              channels[chan].s = False #secret
              channels[chan].m = False #moderated
              channels[chan].R = False #registered nicks only
              channels[chan].n = False #no outside messages
              channels[chan].anon = False #anonymous
              channels[chan].bs = False #backscroll
              channels[chan].topic = ''
              channels[chan].name = name
              last_channel_number +=1 
              channels[chan].number = last_channel_number
              self.channels[chan] = channels[chan]
            else:
              if channels[chan].i:
                if chan not in self.invites:
                  self.send("473 " + self.nick + " " + chan + " :Channel is invite-only.")
                  continue
              if channels[chan].l and len(channels[chan].users)>=channels[chan].l:
                self.send("471 "+ self.nick + " " + chan + " :Channel is full")
                continue
              for b in channels[chan].b:
                if matchhost(b, self.nick, self.user, self.host):
                  self.send("474 "+ self.nick + " " + chan + " :Your host is banned from this channel. ("+b+")")
                  continue
              if channels[chan].k:
                try:
                  assert keys[index]==channels[chan].k
                except:
                  self.send("475 "+self.nick+" "+chan+" :Need correct key")
                  continue
              if len(self.channels)>=maxchannels:
                self.send("405 "+self.nick+" "+chan+" :Too many channels")
                return
              self.channels[chan]=channels[chan]
              channels[chan].users[self.nick] = occupant()
              channels[chan].users[self.nick].connection = self
              channels[chan].users[self.nick].o = False #op
              channels[chan].users[self.nick].v = False #voiced
              channels[chan].users[self.nick].q = False #quieted
            if channels[chan].topic: self.send("332 "+self.nick+" "+ chan+" :"+channels[chan].topic)
            msg = ":"+hostname+" 353 "
            if channels[chan].s: msg += "@ "
            else: msg += "= "
            msg += chan + " :"  #will use user's capitalization
            buf=msg
            for nick, data in channels[chan].users.items():
              n=nick+" "
              if data.v: n="+"+n
              if data.o: n="@"+n
              if len(buf)+len(n)>=510:
                self.send(buf)
                buf=msg
              else:
                buf+=n
              data.connection.send(":"+self.nick+"!"+self.user+"@"+self.host+" JOIN :"+chan)
            self.send(buf)
            self.send(":%s 366 %s %s :End of /NAMES list." % (hostname, self.nick, chan)) 
        elif command=="PRIVMSG":
          if not self.registered:
            self.send("451 JOIN :First issue NICK and USER commands")
            return
          if len(params)<2:
            self.send("432")
            return
          if params[0][0]=="#":   #need to allow the other channel types
            chan=params[0].lower()
            if chan not in channels:
              self.send("411 "+self.nick+" "+chan+" :No such channel")
              return
            for b in channels[chan].b.keys():
              if matchhost(b, self.nick, self.user, self.host):
                self.send("474 "+ self.nick + " " + chan + " :Cannot send to channel.  Your host is banned. ("+b+")")
                return
            if self.nick in channels[chan].users or channels[chan].n == False:
              for nick, data in channels[chan].users.items():
                if data.connection != self: data.connection.send("%s!%s@%s PRIVMSG %s :%s" % (self.nick, self.user, self.host, channels[chan].name, params[1]))
          else:
            nick = params[0]
            if nick in users:
              users[nick].send(":%s!%s@%s PRIVMSG %s :%s" % (self.nick, self.user, self.host, nick, params[1]))
            else:
              self.send(":%s 401 %s %s :No such nick" % (hostname, self.nick, nick))

        elif command=="USERHOST":
          for nick in params:
            if nick in users:
              self.send(":%s 302 %s :%s%s=%s@%s" % (hostname, self.nick, ['','*'][users[nick].glop or users[nick].lop], nick, users[nick].user, users[nick].host))
            else:
              self.send("302 %s :" % self.nick)

        elif command=="PART":
          if params==[]:
            self.send(":%s 461 :%s" % (hostname, "Need more parameters"))
            return           
          for chan in params[0].split(","):
            if not chan in self.channels:
              self.send(":%s 442 %s :%s" % (hostname, chan, "You're not on that channel."))
              continue
            for nick, data in channels[chan].users.items():
              if len(params)>1:
                data.connection.send(":%s!%s@%s PART %s :%s" % (self.nick, self.user, self.host, chan, param[1]))
              else:
                data.connection.send(":%s!%s@%s PART %s" % (self.nick, self.user, self.host, chan))
            del channels[chan].users[self.nick]

        elif command=="MODE":
          if len(params)==0:
            self.send(":%s 432 :Need more parameters" % hostname)
            return
          if params[0].lower()==self.nick.lower():
            if len(params)==1:
              modes = ""
              if self.wallops: modes="w"
              if self.invisible: modes+="i"
              if self.glop: modes+="o"
              if self.lop: modes+="O"
              if self.invisible_joinpart: modes+="I"
              if self.hide_oper: modes += "H"
              if self.kix: modes += "q"
              if self.regged: modes+="r"
              if self.no_non_reg: modes+="R"
              if self.whois_paranoia: modes+="W"
              if self.away: modes+="a"
              self.send(":%s 221 %s +%s" % (hostname, self.nick, modes))
            else:
              add = 1
              repa = ""
              reps = ""
              ls = copy.deepcopy(self)
              for l in param[1]:
                if l=="+": add=1
                elif l=="-": add=0
                elif l=="w": self.wallops=add
                elif l=="i": self.invisible=add
                elif l=="W": self.whois_paranoia=add
                elif l=="H": self.hide_oper=add
                elif l=="I":
                  if self.glop or self.lop: self.invisible_joinpart=add
              for new, old, symbol in zip(
               [self.wallops, self.invisible, self.whois_paranoia, self.hide_oper, self.invisible_joinpart],
               [ls.wallops, ls.invisible, ls.whois_paranoia, ls.hide_oper, ls.invisible_joinpart],
               "wiWHI"):
               if old ^ new:
                 if new: repa+=symbol
                 else: reps+=symbol
              self.send(":%s MODE %s :%s%s%s%s" % (self.nick, self.nick, ['','+'][repa], repa, ['','-'][reps], reps))
          elif params[0].lower() in self.channels:
            chan = params[0].lower()
            if len(params)==1:
              modes = ""
              parms = ""
              if channels[chan].i: modes+="i"
              if channels[chan].I:
                modes+="I"
                parms += channels[chan].I + " "
              if channels[chan].t: modes+="t"
              if channels[chan].k:
                modes+="k"
                parms += channels[chan].k+" "
              if channels[chan].m: modes+="m"
              if channels[chan].R: modes+="R"
              if channels[chan].n: modes+="n"
              if channels[chan].anon: modes+="A"
              if channels[chan].bs: modes+="L"
              if channels[chan].l:
                modes+="l"
                parms += str(channels[chan].l)+" "
              self.send(":%s 324 %s %s +%s %s" % (hostname, self.nick, channels[chan].name, modes, parms))
              self.send(":%s 329 %s %s %d" % (hostname, self.nick, channels[chan].name, channels[chan].number))
            else:                            
#              if sum(map(params[1].count, "oeklvbI")) < len(params[2:]):
#                self.send(":%s 432 :Need more parameters" % hostname)
#                return
              modes = ""
              parms = ""
              add=1
              for l in params[1]:
                if l=="+": add=1
                elif l=="-": add=0
                elif l=="k":
                  if not add:
                    modes += "-k"
                    if channels[chan].k: parms += channels[chan].k
                    else: parms += params[2]
                    channels[chan].k = None
                  else:
                    if len(params)>2:
                      modes += "+k"
                      parms += params[2]
                      channels[chan].k = params[2]
                      del params[2]
                elif l=="b":
                  if len(params)>2:
                    parms += params[2]
                    if add:
                      channels[chan].b[params[2]] = None
                      modes += "+b"
                    else:
                      modes += "-b"
                      del channels[chan].b[params[2]]
                    del params[2]
                  else:
                    for banned, by in channels[chan].b.items():
                      self.send(":%s 367 %s %s %s %d" % (hostname, self.nick, channels[chan].name, banned, by, channels[chan].number))
                    self.send(":%s 368 %s :End of Channel Ban List" % (hostname, channels[chan].name))
                elif l=="e":
                  if len(params)>2:
                    parms += params[2]
                    if add:
                      channels[chan].e[params[2]] = None
                      modes += "+e"
                    else:
                      modes += "-e"
                      del channels[chan].e[params[2]]
                    del params[2]
                  else:
                    for exempted, by in channels[chan].e.items():
                      self.send(":%s 348 %s %s %s %d" % (hostname, self.nick, channels[chan].name, exempted, by, channels[chan].number))
                    self.send(":%s 349 %s :End of Channel Exempt List" % (hostname, channels[chan].name))
                elif l=="l":
                  if not add:
                    modes += "-l"
                    if len(params)>2: del params[2]
                  else:
                    if len(params)>2:
                      try:
                        channels[chan].l = int(params[2])
                        modes += "+l"
                        parms += param[2]
                      except: pass 
                      del params[2]
                  if not add: channels[chan].l = None
                elif l=="I":
                  if len(params)>2:
                    parms += params[2]
                    if add:
                      channels[chan].I[params[2]] = None
                      modes += "+I"
                    else:
                      modes += "-I"
                      del channels[chan].I[params[2]]
                    del params[2]
                  else:
                    for invited, by in channels[chan].e.items():
                      self.send(":%s 346 %s %s %s %d" % (hostname, self.nick, channels[chan].name, invited, by, channels[chan].number))
                    self.send(":%s 347 %s :End of Channel Invite List" % (hostname, channels[chan].name))
                elif l=="o":
                  if len(params)>2:
                    if channels[chan].users[self.nick].o:
                      try: channels[chan].users[params[2]].o=add
                      except: self.send(":%s 441 %s %s :User not on that channel" % (hostname, params[2], channels[chan].name))
                    else:
                      self.send(":%s 482 %s :You're not a channel operator" % (hostname, channels[chan].name))
                    del params[2]
                elif l=="v":
                  if len(params)>2:
                    if channels[chan].users[self.nick].o:
                      try: channels[chan].users[params[2]].v=add
                      except: self.send(":%s 441 %s %s :User not on that channel" % (hostname, params[2], channels[chan].name))
                    else:
                      self.send(":%s 482 %s :You're not a channel operator" % (hostname, channels[chan].name))
                    del params[2]
                elif l=="i":
                  channels[chan].i = add
                  modes += ["-i","+i"][add]
                elif l=="t":
                  channels[chan].t = add
                  modes += ["-t","+t"][add]
                elif l=="s":
                  channels[chan].s = add
                  modes += ["-s","+s"][add]
                elif l=="m":
                  channels[chan].m = add
                  modes += ["-m","+m"][add]
                elif l=="R":
                  channels[chan].R = add
                  modes += ["-R","+R"][add]
                elif l=="n":
                  channels[chan].n = add
                  modes += ["-n","+n"][add]
              m=modes[:2]
              for i, l in enumerate(modes[2:]):
                if modes[i-2] != l or l not in "+-": m += l
              for data in channels[chan].users.values():
                data.connection.send(":%s!%s@%s MODE %s %s %s" % (self.nick, self.user, self.host, channels[chan].name, m, parms))
          else:
            if params[0][0] in "#!":
              self.send(":%s 403 %s %s :You are not on that channel." % (hostname, self.nick, params[0]))

              print channels.keys()
              print self.channels.keys()
              print params[0]


            else:
              self.send(":%s 502 %s :Can't change mode of other users" % (hostname, self.nick))
                
    def send(self, message):
        print "%d<" % self.number, message
        self.transport.write(message + '\r\n')

from twisted.internet import reactor, protocol
from twisted.application import internet

factory = protocol.ServerFactory()
factory.protocol = MyChat
factory.clients = []

reactor.listenTCP(6667, factory)
reactor.run()
