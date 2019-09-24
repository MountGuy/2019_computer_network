import threading
from socket import *
from setting import *
from player import Player

serverAddr = '147.46.240.95'
localAddr = '127.0.0.1'

class Client:
  def __init__(self):
    self.clientSock = socket(AF_INET, SOCK_STREAM)
    self.clientSock.connect((serverAddr, 8080))
    id = input('submit your id:')
    send(self.clientSock, id)
    data = recieve(self.clientSock)
    strs = data.split()
    numbers = list(map(lambda x : int(x), strs))
    board = [numbers[0:5], numbers[5:10], numbers[10:15], numbers[15:20], numbers[20:25]]
    self.player = Player(id, board)
    self.player.printBoard()
    self.turn = False

  def run(self):
    t1 = threading.Thread(target = self.listen, args = (self.clientSock, ))
    t2 = threading.Thread(target = self.call, args = (self.clientSock, ))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()
    t1.join()
    return

  def listen(self, sock):
    while True:
      msg = recieve(sock)
      parse = msg.split('\0')
      if parse[0] == 'PICK':
        self.player.pickNumber(int(parse[1]))
        self.player.printBoard()
        print('{} picked {}.'.format(parse[2], parse[1]))
      elif parse[0] == 'MESS':
        print('Message from {}: {}'.format(parse[1], parse[2]))
      elif parse[0] == 'BING':
        print('{} achieved bingo!'.format(parse[1]))
        return
      elif parse[0] == 'TURN':
        print('Your turn!')
        self.turn = True
      elif parse[0] =='POSI':
        print('Your position is {}.'.format(parse[1]))
      else:
        print('Invalid command.')

  def call(self, sock):
    while True:
      command = input()
      if command == 'PICK':
        num = input()
        send(sock, '{}\0{}'.format('PICK', num))
        self.turn = False
      elif command == 'MESS':
        id = input()
        msg = input()
        send(sock, '{}\0{}\0{}'.format('MESS', id, msg))

client = Client()
client.run()

client.clientSock.close()