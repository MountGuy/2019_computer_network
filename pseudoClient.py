from protocol import send, recieve, newSocket, port

serverIP = '147.46.240.95'
localIP = '127.0.0.1'

class PseudoClient:
  def __init__(self, id):
    ### connect to server
    self.clientSock = newSocket()
    self.clientSock.connect((localIP, port))

    ### send id to server
    self.id = id
    send(self.clientSock, id)
    
    ### recieve success sign
    recieve(self.clientSock)

    ### send first room ID to server
    roomID = recieve(self.clientSock).split('\0')[1]
    send(self.clientSock, roomID)

    ### recieve success sign
    recieve(self.clientSock)

    ### recieve position data
    ### for pseudo clients, server send None string as a position
    recieve(self.clientSock)

  def run(self):
    ### game start sign from server
    recieve(self.clientSock)

    ### recieve board from server
    boardData = recieve(self.clientSock).split()
    self.numbers = list(map(lambda x : int(x), boardData))
    self.selected = [False] * 25

    while True:
      command = recieve(self.clientSock).split()

      if command[0] == 'PICK':
        ### apply other player's pick
        n = int(command[0])
        for i in range(25):
          if self.numbers[i] == n:
            self.selected[i] = True

      elif command[0] == 'BINGO':
        ### actually there is nothing to do at this signal
        continue

      elif command[0] == 'TURN':
        ### select first number from it's numbers which is not selected yet
        for i in range(25):
          if self.selected[i] == False:
            send(self.clientSock, 'PICK\0{}'.format(self.numbers[i]))
            
      elif command[0] == 'DONE':
        ### reflect the done signal to server
        send(self.clientSock, 'DONE')
        break
    return
