import random
import sys
import signal
import queue

from threading import Thread
from player import Player
from room import Room
from protocol import send, recieve, newSocket, port

from pseudoClient import PseudoClient 

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
  
  def distribute(self, msg):
    for sock in self.sockets:
      send(sock, msg)

  def getClient(self, sock, position, queue):

    ### get ID from client.
    while True:
      parse = recieve(sock).split('\0')
      if parse[0] != 'ID':
        send(sock, 'Invalid request at this status.')
        sock.close()
        i -= 1
        continue
      id = parse[1]
      if id in self.playerDict:
        send(sock, 'FAIL')
      else:
        send(sock, 'SUCCESS')
        self.playerDict[id] = 'Exist'
        break
      
    print('>> {} logged in'.format(id))

    ### get room from client
    msg = 'ROOM'
    for room in self.rooms:
      msg += '\0{}'.format(room.roomName)
    send(sock, msg)

    while True:
      parse = recieve(sock).split('\0')
      if parse[0] != 'ROOM':
        send(sock, 'Invalid request at this status.')
        sock.close()
        i -= 1
        continue
      if parse[1] in self.roomDict:
        send(sock, 'SUCCESS')
        break
      else:
        send(sock, 'FAIL')
    
    send(sock, 'POSI\0{}'.format(position))
    
    n = len(self.sockets)
    self.sockets.append(sock)
    self.playerDict[id] = (n, sock, position)

    room = self.rooms[self.roomDict[parse[1]]]
    room.addPlayer(id)
    
    print(">> {} joined the game".format(id))
    queue.put(id)
    
    return

  def collectClient(self):
    positions = ['main culprit','copartner']
    getClientThread = []
    IDRoomInfo = []
    resultQueue = queue.Queue()
    
    for i in range(self.playerNum):
      conSock, (ip, _) = self.serverSock.accept()
    
      if ip != '127.0.0.1':
        position = positions.pop(0)
      else:
        position = 'None'

      if position == 'copartner':
        self.copSock = conSock
      
      t = Thread(target = self.getClient, args = (conSock, position, resultQueue))
      t.daemon = True
      getClientThread.append(t)
      t.start()
    
    for t in getClientThread:
      t.join()

    for i in range(self.playerNum):
      id = resultQueue.get()
      n, sock, position = self.playerDict[id]

      send(sock, 'START')
      room = self.rooms[0]
      msg = room.getPackedBoard(id)
      send(sock, msg)
    #=============

      t = Thread(target = self.handleClient, args = (i, sock, id, position))
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
          
          self.distribute('PICK\0{}\0{}'.format(parse[1], id))
          if position == 'main culprit':
            send(self.copSock, 'MESS\0{}\0{}'.format('main culprit', parse[2]))

          (end, winners) = self.rooms[0].checkBingo()
          if end:
            for id in winners:
              self.distribute('BINGO\0{}'.format(id))
            self.distribute('DONE')
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


if __name__ == "__main__":
  server = Server()
  server.service()
  