from threading import Thread
from protocol import send, recieve, newSocket, port
from player import Player

import curses
from curses.textpad import rectangle

logx, logy = 30, 1
boardx, boardy = 1, 1
logwidth, logheight = 73 - logx, 10
inputx, inputy = logx, logy + 11

serverIP = '147.46.240.95'
localIP = '127.0.0.1'


class Client:

  def __init__(self, stdscr):
    self.position = ''
    self.logi = 0
    self.log = ['', '', '', '', '', '', '', '', '', '']
    self.stdscr = stdscr
    
    rectangle(self.stdscr, boardy - 1, boardx - 1, boardy + 5, boardx + 15)
    rectangle(self.stdscr, logy - 1, logx - 1, logy + logheight, logx + logwidth)
    self.stdscr.refresh()

    self.clientSock = newSocket()
    self.clientSock.connect((serverIP, port))


    while True:
      self.printLog('Submit your id.')
      id = self.nInput(inputx, inputy, 30)
      send(self.clientSock, 'ID\0{}'.format(id))
      result = recieve(self.clientSock)
      if result == 'FAIL':
        self.printLog('ID already exists. Choose another ID')
      else:
        break

    parse = recieve(self.clientSock)
    roomNames = parse.split('\0')[1:]
    self.printLog('Room lists')
    for roomName in roomNames:
      self.printLog(roomName)
    while True:
      self.printLog('Select room to join.')
      room = self.nInput(inputx, inputy, 30)
      send(self.clientSock, 'ROOM\0{}'.format(room))
      result = recieve(self.clientSock)
      if result == 'FAIL':
        self.printLog('{} do not exists. Try it again.'.format(room))
      else:
        break

    parse = recieve(self.clientSock).split('\0')
    self.printLog('Your position is {}.'.format(parse[1]))
    self.position = parse[1]

    strs = recieve(self.clientSock).split()
    numbers = list(map(lambda x : int(x), strs))
    board = [numbers[0:5], numbers[5:10], numbers[10:15], numbers[15:20], numbers[20:25]]
    self.player = Player(id, board)
    string = recieve(self.clientSock)
    self.printBoard()
    self.turn = False

  def nPrint(self, x, y, string):
    self.stdscr.addstr(y, x, string, curses.color_pair(2))
    self.stdscr.refresh()

  def nInput(self, x, y, n):
    curses.echo()
    self.nPrint(x, y, '>> ')
    msg = self.stdscr.getstr(y, x + 3, n).decode('utf-8')
    curses.noecho()
    self.nPrint(x + 3, y, ' ' * n)
    return msg

  def printLog(self, msg):
    for i in range(10):
      self.nPrint(logx, logy + i, ' ' * logwidth)
    for i in range(9):
      self.log[i] = self.log[i + 1]
    self.log[9] = msg
    for i in range(10):
      self.nPrint(logx, logy + i, self.log[i])

  def printBoard(self):
    for i in range(5):
      self.nPrint(boardx, boardy + i, self.player.nthLine(i))

  def run(self, sock):
    while True:
      msg = recieve(sock)
      parse = msg.split('\0')
      if parse[0] == 'PICK':
        self.player.pickNumber(int(parse[1]))
        self.printBoard()
        self.printLog('{} picked {}.'.format(parse[2], parse[1]))
      elif parse[0] == 'MESS':
        self.printLog('Message from {}: {}'.format(parse[1], parse[2]))
      elif parse[0] == 'BINGO':
        self.printLog('{} achieved bingo!'.format(parse[1]))
      elif parse[0] == 'TURN':
        self.printLog('Your turn!')
        self.turn = True
        self.printLog('Submit your pick.')
        while True:
          num = self.nInput(inputx, inputy, 30)
          if not(num.isdigit()):
            self.printLog('Invalid number. try it again.')
          else:
            break
        if self.position == 'main culprit':
          self.printLog('Submit your message to send:')
          msg = self.nInput(inputx, inputy, 30)
          send(sock, '{}\0{}\0{}'.format('PICK', num, msg))
        else:
          send(sock, '{}\0{}\0{}'.format('PICK', num, 'None'))
      elif parse[0] =='POSI':
        self.printLog('Your position is {}.'.format(parse[1]))
        self.position = parse[1]
      elif parse[0] == 'DONE':
        send(sock, 'DONE')
        break
    self.printLog('Press any key to exit.')
    self.stdscr.getch()

def main(scr):
  curses.use_default_colors()
  curses.init_pair(1, curses.COLOR_WHITE,  curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_CYAN,   curses.COLOR_BLACK)
  client = Client(scr)
  client.run(client.clientSock)
  client.clientSock.close()

 
if __name__ == "__main__":
    curses.wrapper(main)