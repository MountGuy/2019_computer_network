from threading import Thread
from protocol import send, recieve, newSocket, port
from player import Player

serverIP = '147.46.240.95'
localIP = '127.0.0.1'

class Client:
  def __init__(self):
    self.clientSock = newSocket()
    self.clientSock.connect((localIP, port))
    id = input('submit your id:')
    send(self.clientSock, 'ID\0{}'.format(id))
    data = recieve(self.clientSock)
    roomNames = data.split('\0')[1:]

    print('<rooms>')
    for roomName in roomNames:
      print(roomName)

    room = input('select room to join:')
    send(self.clientSock, 'ROOM\0{}'.format(room))

    parse = recieve(self.clientSock).split('\0')
    print('Your position is {}.'.format(parse[1]))

    strs = recieve(self.clientSock).split()
    numbers = list(map(lambda x : int(x), strs))
    board = [numbers[0:5], numbers[5:10], numbers[10:15], numbers[15:20], numbers[20:25]]
    self.player = Player(id, board)
    self.player.printBoard()
    self.turn = False

  def run(self):
    t1 = Thread(target = self.listen, args = (self.clientSock, ))
    t2 = Thread(target = self.call, args = (self.clientSock, ))
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
      elif parse[0] == 'BINGO':
        print('{} achieved bingo!'.format(parse[1]))
      elif parse[0] == 'TURN':
        print('Your turn!')
        self.turn = True
      elif parse[0] =='POSI':
        print('Your position is {}.'.format(parse[1]))
      elif parse[0] == 'DONE':
        send(sock, 'DONE')
        break

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
      else:
        print('Invalid command.')

client = Client()
client.run()

client.clientSock.close()