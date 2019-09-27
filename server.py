import random
import sys
import signal

from threading import Thread
from player import Player
from room import Room
from protocol import send, recieve, newSocket, port

from pseudoClient import PseudoClient 

def handler(signum, f):
  print(signum)
  sys.exit()

signal.signal(signal.SIGINT, handler)

def boardToString(board):
  string = ['', '', '', '', '']
  for i in range(0, 5):
    string[i] = '{} {} {} {} {}\n'.format(board[i][0], board[i][1], board[i][2], board[i][3], board[i][4])
  return '{}{}{}{}{}'.format(string[0], string[1], string[2], string[3], string[4])

class Server :
  def __init__(self):
    self.rooms = [Room('room1')]
    self.serverSock = newSocket()
    self.serverSock.bind(('', port))
    self.serverSock.listen(5)
    self.threads = []
    self.sockets = []
    self.roomNum = 1
    self.roomDict = {'room1': 0}
    self.playerDict = {}
    self.playerN = 5
    self.turn = random.randrange(0, self.playerN - 1)

  def distribute(self, msg):
    for sock in self.sockets:
      send(sock, msg)
  
  def collectClient(self):
    job = ['main culprit','copartner']
    for i in range(self.playerN):
      conSock, (ip, _) = self.serverSock.accept()
      
      parse = recieve(conSock).split('\0')
      if parse[0] != 'ID':
        conSock.close()
        i -= 1
        continue
      id = parse[1]
      print('>> {} logged in'.format(id))

      msg = 'ROOM'
      for room in self.rooms:
        msg += '\0{}'.format(room.roomName)
      send(conSock, msg)

      parse = recieve(conSock).split('\0')
      if parse[0] != 'ROOM':
        conSock.close()
        i -= 1
        continue
      room = self.rooms[self.roomDict[parse[1]]]

      self.sockets.append(conSock)
      self.playerDict[id] = i
      room.addPlayer(id)
      print(">> {} joined the game".format(id))
      if ip != '127.0.0.1':
        send(conSock, 'POSI\0{}'.format(job.pop(0)))
      
      msg = boardToString(self.rooms[0].getBoard(id))
      send(conSock, msg)
      
      t = Thread(target = self.handleClient, args = (i, conSock, id))
      t.daemon = True
      self.threads.append(t)
      t.start()

  def handleClient(self, i, conSock, id):
    while True:
      msg = recieve(conSock)
      parse = msg.split('\0')
      if parse[0] == 'PICK':
        if i == self.turn:
          self.turn = (self.turn + 1) % self.playerN
          self.rooms[0].pickNumber(int(parse[1]))
          print(">> {} picked {}".format(id, int(parse[1])))
          self.rooms[0].printStatus(5)
          print("=====================================================================")
          self.distribute('PICK\0{}\0{}'.format(parse[1], id))
          (end, winners) = self.rooms[0].checkBingo()
          if end:
            for id in winners:
              self.distribute('BINGO\0{}'.format(id))
            self.distribute('DONE')
          else:
            send(self.sockets[self.turn], 'TURN')
        else:
          send(conSock, 'MESS\0{}\0{}'.format('Server', 'It\'s not your turn now.'))
      elif parse[0] == 'MESS':
        j = self.playerDict[parse[1]]
        send(self.sockets[j], 'MESS\0{}\0{}'.format(id, parse[2]))
      elif parse[0] == 'DONE':
        break
    return

  def service(self):
    while True:
      collectClient = Thread(target = self.collectClient)
      collectClient.start()

      for i in range(0, 3):
        print('>> pseudo player {} created'.format(i + 1))
        pc = PseudoClient('pseudo_player_' + str(i + 1))
        t = Thread(target = pc.run)
        t.daemon = True
        t.start()
      
      collectClient.join()
      send(self.sockets[self.turn], 'TURN')
      
      for t in self.threads:
        t.join()

      self.roomNum += self.roomNum
      #self.rooms[0] = Room('room #{}'.format(self.roomNum))
      self.rooms[0] = Room('room{}'.format(self.roomNum))
      self.threads = [None, None, None, None, None]
      self.sockets = []
      self.playerDict = {'room{}'.format(self.roomNum):0}
      for sock in self.sockets:
        sock.close()


server = Server()
server.service()