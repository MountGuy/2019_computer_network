import random
import sys
import signal

from threading import Thread
from player import Player
from room import Room
from protocol import send, recieve, newSocket, port

from pseudoClient import PseudoClient 


def boardToString(board):
  string = ['', '', '', '', '']
  for i in range(0, 5):
    string[i] = '{} {} {} {} {}\n'.format(board[i][0], board[i][1], board[i][2], board[i][3], board[i][4])
  return '{}{}{}{}{}'.format(string[0], string[1], string[2], string[3], string[4])

def distribute(server, msg):
  for sock in server.sockets:
    send(sock, msg)

class Server :
  def __init__(self):
    self.rooms = [Room('room1')]
    self.roomNum = 1
    self.roomDict = {'room1': 0}

    self.playerNum = 5
    self.playerDict = {}

    self.threads = []
    self.sockets = []

    self.serverSock = newSocket()
    self.serverSock.bind(('', port))
    self.serverSock.listen(5)
    self.copSock = None
    self.order = random.sample(range(0, 5), 5)
    self.turn = 0


  
  def collectClient(self):
    positions = ['main culprit','copartner']

    for i in range(self.playerNum):
      position = 'None'
      conSock, (ip, _) = self.serverSock.accept()
      
      while True:
        parse = recieve(conSock).split('\0')
        if parse[0] != 'ID':
          send(conSock, 'Invalid request at this status.')
          conSock.close()
          i -= 1
          continue
        id = parse[1]
        if id in self.playerDict:
          send(conSock, 'FAIL')
        else:
          send(conSock, 'SUCCESS')
          break
      
      print('>> {} logged in'.format(id))

      msg = 'ROOM'
      for room in self.rooms:
        msg += '\0{}'.format(room.roomName)
      send(conSock, msg)

      while True:
        parse = recieve(conSock).split('\0')
        if parse[0] != 'ROOM':
          send(conSock, 'Invalid request at this status.')
          conSock.close()
          i -= 1
          continue
        if parse[1] in self.roomDict:
          send(conSock, 'SUCCESS')
          break
        else:
          send(conSock, 'FAIL')
      
      room = self.rooms[self.roomDict[parse[1]]]

      self.sockets.append(conSock)
      self.playerDict[id] = i
      room.addPlayer(id)

      print(">> {} joined the game".format(id))
      if ip != '127.0.0.1':
        position = positions.pop(0)
        send(conSock, 'POSI\0{}'.format(position))
      
      msg = boardToString(self.rooms[0].getBoard(id))
      send(conSock, msg)

      if position == 'copartner':
        self.copSock = conSock

      t = Thread(target = self.handleClient, args = (i, conSock, id, position))
      t.daemon = True
      self.threads.append(t)
      t.start()

  def handleClient(self, order, conSock, id, position):
    while True:
      parse = recieve(conSock).split('\0')

      if parse[0] == 'PICK':
        if order == self.order[self.turn]:
          self.turn = (self.turn + 1) % self.playerNum

          self.rooms[0].pickNumber(int(parse[1]))
          print(">> {} picked {}".format(id, int(parse[1])))
          self.rooms[0].printStatus(5)
          
          print("=====================================================================")
          
          distribute(self, 'PICK\0{}\0{}'.format(parse[1], id))
          if position == 'main culprit':
            send(self.copSock, 'MESS\0{}\0{}'.format('main culprit', parse[2]))

          (end, winners) = self.rooms[0].checkBingo()
          if end:
            for id in winners:
              distribute(self, 'BINGO\0{}'.format(id))
            distribute(self, 'DONE')
          else:
            send(self.sockets[self.order[self.turn]], 'TURN')
        else:
          send(conSock, 'MESS\0{}\0{}'.format('Server', 'It\'s not your turn now.'))
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
      distribute(self, 'START')
      send(self.sockets[self.order[self.turn]], 'TURN')
      
      for t in self.threads:
        t.join()
      self.threads = []

      self.roomNum += 1
      self.rooms[0] = Room('room{}'.format(self.roomNum))
      self.roomDict = {'room{}'.format(self.roomNum):0}
      
      self.playerDict = {}

      for sock in self.sockets:
        sock.close()
      self.sockets = []

  def end(self):
    for sock in self.sockets:
      sock.close()
    self.serverSock.close
    sys.exit()



server = Server()
server.service()
signal.signal(signal.SIGINT, Server.end)
