from protocol import send, recieve, newSocket, port

serverIP = '147.46.240.95'
localIP = '127.0.0.1'

class PseudoClient:
  def __init__(self, id):
    self.clientSock = newSocket()
    self.clientSock.connect((localIP, port))
    self.id = id
    send(self.clientSock, 'ID\0{}'.format(id))

    data = recieve(self.clientSock)
    roomNames = data.split('\0')[1:]
    room = roomNames[0]
    send(self.clientSock, 'ROOM\0{}'.format(room))

    data = recieve(self.clientSock)
    strs = data.split()
    self.numbers = list(map(lambda x : int(x), strs))
    self.selected = [False] * 25

  def run(self):
    while True:
      msg = recieve(self.clientSock)
      parse = msg.split()
      if parse[0] == 'PICK':
        n = int(parse[0])
        for i in range(25):
          if self.numbers[i] == n:
            self.selected[i] = True
      elif parse[0] == 'BINGO':
        print('bingo message recieved')
      elif parse[0] == 'TURN':
        for i in range(25):
          if self.selected[i] == False:
            send(self.clientSock, 'PICK\0{}'.format(self.numbers[i]))
      elif parse[0] == 'DONE':
        send(self.clientSock, 'DONE')
        break
    return
