import random
import threading
import socket as sck

from player import Player
from room import Room
from setting import send, recieve

class Server :
  def __init__(self):
    self.room = Room('room #1')
    self.serverSock = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
    self.serverSock.bind(('', 8080))
    self.serverSock.listen(5)
    self.threads = []
    self.sockets = []
    self.roomNum = 1
    self.dict = {}
    self.turn = random.randrange(0, 4)

  def boardToString(self, board):
    string = ['', '', '', '', '']
    for i in range(0, 5):
      string[i] = '{} {} {} {} {}\n'.format(board[i][0], board[i][1], board[i][2], board[i][3], board[i][4])
    return '{}{}{}{}{}'.format(string[0], string[1], string[2], string[3], string[4])

  def handleClient(self, i, conSock, addr):
    id = recieve(conSock)
    self.dict[id] = i
    self.room.addPlayer(id)
    #print(id)
    msg = self.boardToString(self.room.getBoard(id))
    send(conSock, msg)
    while True:
      msg = recieve(conSock)
      parse = msg.split('\0')
      if parse[0] == 'PICK':
        print(self.turn, ' ', i)
        if i == self.turn:
          self.turn = (self.turn + 1) % 5
          self.room.pickNumber(int(parse[1]))
          self.room.printStatus()
          self.distribute('PICK\0{}\0{}'.format(parse[1], id))
          send(self.sockets[self.turn], 'TURN')
          if self.room.checkBingo():
            break
        else:
          send(conSock, 'MESS\0{}\0{}'.format('Server', 'It\'s not your turn now.'))
      elif parse[0] == 'MESS':
        j = self.dict[parse[1]]
        send(self.sockets[j], 'MESS\0{}\0{}'.format(id, parse[2]))

    return

  def distribute(self, msg):
    for sock in self.sockets:
      send(sock, msg)

  def service(self):
    for i in range(0, 5):
      conSock, addr = self.serverSock.accept()
      self.sockets.append(conSock)
      t = threading.Thread(target=self.handleClient, args=(i, conSock, addr))
      t.daemon = True
      self.threads.append(t)
      t.start()
    send(self.sockets[self.turn], 'TURN')
    for t in self.threads:
      t.join()
    self.roomNum = self.roomNum + 1
    self.room = Room('room #{}'.format(self.roomNum))
    self.threads = []
    self.sockets = []


server = Server()


server.service()
#server.room.addPlayer('per')
#server.room.addPlayer('ma')
#server.room.addPlayer('ri')
#server.room.addPlayer('o')
#
#
#list = random.sample(range(1, 100), 99)
#for i in list:
#  server.room.pickNumber(i)
#  if server.room.checkBingo():
#    server.room.printStatus()
#    break