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
        print(">> {} joined the game".format(id))
        send(sock, 'FAIL')
    
    ### send position
    send(sock, 'POSI\0{}'.format(position))
    
    ### add client's data
    self.sockets.append(sock)
    self.playerDict[id] = (sock, position)
    self.rooms[0].addPlayer(id)
    queue.put(id)
    
    return

  def collectPlayers(self):
    positions = ['main culprit','copartner']
    getClientThreads = []
    IDQueue = queue.Queue()
    
    ### get five players
    for i in range(self.playerNum):
      conSock, (ip, _) = self.serverSock.accept()
    
      if ip != '127.0.0.1':
        position = positions.pop(0)
      else:
        position = 'None'

      if position == 'copartner':
        self.copSock = conSock
      
      t = Thread(target = self.getClient, args = (conSock, position, IDQueue))
      t.daemon = True
      getClientThreads.append(t)
      t.start()
    
    ### thread end
    for t in getClientThreads:
      t.join()

    ### put them to room
    order = random.sample(range(0, 5), 5)
    for i in range(self.playerNum):
      id = IDQueue.get()
      sock, position = self.playerDict[id]
      self.sockets[order[i]] = sock

      send(sock, 'START')
      msg = self.rooms[0].getPackedBoard(id)
      send(sock, msg)
      
      t = Thread(target = self.serviceClient, args = (id, order[i]))
      t.daemon = True
      self.threads.append(t)
      t.start()

  def serviceClient(self, id, order):
    sock, position = self.playerDict[id]
    while True:
      parse = recieve(sock).split('\0')

      if parse[0] == 'PICK':
        if order == self.turn:
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
            send(self.sockets[self.turn], 'TURN')
        else:
          send(sock, 'MESS\0{}\0{}'.format('Server', 'It\'s not your turn now.'))
      elif parse[0] == 'DONE':
        break
    return

  def run(self):
    while True:
      collectPlayers = Thread(target = self.collectPlayers)
      collectPlayers.start()

      for i in range(0, 3):
        pc = PseudoClient('ps_player_' + str(i + 1))
        print('>> pseudo player {} created'.format(i + 1))
        t = Thread(target = pc.run)
        t.daemon = True
        t.start()
      
      collectPlayers.join()
      send(self.sockets[self.turn], 'TURN')
      
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
  server.run()
  