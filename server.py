import random

from threading import Thread
from player import Player
from room import Room
from protocol import send, recieve, newSocket

class Server :
  def __init__(self):
    self.room = Room('room #1')
    self.serverSock = newSocket()
    self.serverSock.bind(('', 8080))
    self.serverSock.listen(5)
    self.threads = []
    self.sockets = []
    self.roomNum = 1
    self.dict = {}
    self.playerN = 2
    self.turn = random.randrange(0, self.playerN - 1)

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
          self.turn = (self.turn + 1) % self.playerN
          self.room.pickNumber(int(parse[1]))
          self.room.printStatus()
          self.distribute('PICK\0{}\0{}'.format(parse[1], id))
          send(self.sockets[self.turn], 'TURN')
          (end, winners) = self.room.checkBingo()
          if end:
            for id in winners:
              self.distribute('BING\0{}'.format(id))
            break
        else:
          send(conSock, 'MESS\0{}\0{}'.format('Server', 'It\'s not your turn now.'))
      elif parse[0] == 'MESS':
        j = self.dict[parse[1]]
        send(self.sockets[j], 'MESS\0{}\0{}'.format(id, parse[2]))
      elif parse[0] == 'DONE':
        break

    return

  def distribute(self, msg):
    for sock in self.sockets:
      send(sock, msg)

  def service(self):
    while True:
      for i in range(0, self.playerN):
        conSock, addr = self.serverSock.accept()
        self.sockets.append(conSock)
        t = Thread(target=self.handleClient, args=(i, conSock, addr))
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
      self.dict = {}
      for sock in self.sockets:
        sock.close()


server = Server()


server.service()