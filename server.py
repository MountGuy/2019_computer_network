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
    self.roomDict = {'room1': self.rooms[0]}

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
    ### get ID from client
    while True:
      id = recieve(sock)
      if id in self.playerDict:
        send(sock, 'FAIL')
      else:
        send(sock, 'SUCCESS')
        ### add id to dictionary early in order to avoid collision
        self.playerDict[id] = 'Exist'
        break
    print('>> {} logged in'.format(id))

    ### get room to join from client
    msg = 'ROOM'
    for room in self.rooms:
      msg += '\0{}'.format(room.roomName)
    send(sock, msg)

    while True:
      roomID = recieve(sock)
      if roomID in self.roomDict:
        send(sock, 'SUCCESS')
        print(">> {} joined the game".format(id))
        break
      else:
        send(sock, 'FAIL')
    
    ### send position to client
    send(sock, position)
    
    ### store client's data
    self.sockets.append(sock)
    self.playerDict[id] = (sock, position, roomID)
    self.roomDict[roomID].addPlayer(id)
    queue.put(id)
    return

  def collectPlayers(self):
    positions = ['main culprit','copartner']
    getClientThreads = []
    IDQueue = queue.Queue()
    
    ### get five players from distinct thread
    for i in range(self.playerNum):
      ### recieve connection from client
      sock, (ip, _) = self.serverSock.accept()
    
      ### local ip address means that client is pseudo client
      ### positions are only given to players
      if ip != '127.0.0.1':
        position = positions.pop(0)
      else:
        position = 'None'

      ### save copartner's socket for simple implementation
      if position == 'copartner':
        self.copSock = sock
      
      t = Thread(target = self.getClient, args = (sock, position, IDQueue))
      t.daemon = True
      getClientThreads.append(t)
      t.start()
    
    ### wait until five clients are collected
    for t in getClientThreads:
      t.join()

    ### put them to room and give random order
    order = random.sample(range(0, 5), 5)

    for i in range(self.playerNum):
      id = IDQueue.get()
      sock, position, roomID = self.playerDict[id]

      ### reallocate sockets to shuffle order
      self.sockets[order[i]] = sock

      ### send game start signal to client
      send(sock, 'START')

      ### send board data to client
      msg = self.roomDict[roomID].getPackedBoard(id)
      send(sock, msg)
      
      ### service client in distinct threads
      t = Thread(target = self.serviceClient, args = (id, order[i], roomID))
      t.daemon = True
      self.threads.append(t)
      t.start()
    send(self.sockets[self.turn], 'TURN')

  def serviceClient(self, id, order, roomName):
    ### id and order of client are passed as a parameter
    ### socket, position and roomID are stored in dictionary
    sock, position, roomID = self.playerDict[id]
    room = self.roomDict[roomID]

    while True:
      command = recieve(sock).split('\0')

      if command[0] == 'PICK':
        ### check if PICK request was sended from proper client
        if order == self.turn:
          ### increase turn
          self.turn = (self.turn + 1) % self.playerNum

          ### apply client's pick to room and print status
          room.pickNumber(int(command[1]))
          print(">> {} picked {}".format(id, int(command[1])))
          room.printStatus(5)
          print("=====================================================================")
          
          ### notify the pick to every clients
          self.distribute('PICK\0{}\0{}'.format(command[1], id))

          if position == 'main culprit':
            ### if position is main culprint, also send message to copartner
            send(self.copSock, 'MESS\0{}\0{}'.format('main culprit', command[2]))

          ### check if bingo was achieved by someone
          (end, winners) = room.checkBingo()
          if end:
            ### notify the winner to every clients
            for id in winners:
              self.distribute('BINGO\0{}'.format(id))

            ### send done signal to all clients
            self.distribute('DONE')
          else:
            ### send turn signal to next client
            send(self.sockets[self.turn], 'TURN')
        else:
          ### at now, this code cannot be executed if player uses client without modifying
          send(sock, 'MESS\0{}\0{}'.format('Server', 'It\'s not your turn now.'))
      elif command[0] == 'DONE':
        ### terminate the thread since client sended done signal
        break
    return

  def run(self):
    while True:
      ### run the collect player thread
      collectPlayers = Thread(target = self.collectPlayers)
      collectPlayers.start()

      ### make three pseudo client
      for i in range(0, 3):
        pc = PseudoClient('ps_player_' + str(i + 1))
        t = Thread(target = pc.run)
        t.daemon = True
        t.start()
      
      ### after collect players thread end,
      ### 5 peer thread can control the progress of the game
      collectPlayers.join()
      
      ### wait until 5 service thread terminate
      for t in self.threads:
        t.join()

      ### reset data for next game
      self.threads = []
      self.roomNum += 1
      self.rooms[0] = Room('room{}'.format(self.roomNum))
      self.roomDict = {'room{}'.format(self.roomNum):self.rooms[0]}
      self.playerDict = {}

      ### close socket
      for sock in self.sockets:
        sock.close()
      self.sockets = []


if __name__ == "__main__":
  server = Server()
  server.run()
  