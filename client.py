from threading import Thread
from protocol import send, recieve, newSocket, port
from player import Player

import curses
from curses.textpad import rectangle

logx, logy = 1, 1
boardx, boardy = 46, 1
logwidth, logheight = 43, 20
inputx, inputy = logx, logy + logheight + 1

serverIP = '147.46.240.95'
localIP = '127.0.0.1'

red = 1
green = 2
yellow = 3
blue = 4
magenta = 5
cyan = 6
white = 7


class Client:

  def __init__(self, stdscr):
    self.position = ''
    self.stdscr = stdscr
    self.logs = [['']] * logheight
    self.sets = [[white]] * logheight
    
    rectangle(self.stdscr, boardy - 1, boardx - 1, boardy + 5, boardx + 15)
    rectangle(self.stdscr, logy - 1, logx - 1, logy + logheight, logx + logwidth)
    self.stdscr.refresh()

    self.clientSock = newSocket()
    self.clientSock.connect((serverIP, port))

    while True:
      self.printLog(['Submit your ID.'], [white])
      id = self.nInput(inputx, inputy, 30)
      send(self.clientSock, 'ID\0{}'.format(id))
      result = recieve(self.clientSock)
      if result == 'FAIL':
        self.printLog(
          ['ID ', '[{}]'.format(id), ' already exists. Choose another.'],
          [white, yellow, white]
        )
      else:
        self.printLog(
          ['Login success. Your ID is ', '[{}]'.format(id), '.'],
          [white, yellow, white]
        )
        break
  
    roomNames = recieve(self.clientSock).split('\0')[1:]
    while True:
      self.printLog(['┌' +  '─' * (logwidth - 2) + '┐'], [green])
      self.printLog(['│', 'Room lists', ' ' * (logwidth - 12), '│'], [green, white, white, green])
      for roomName in roomNames:
        self.printLog(
          ['│','>> ', '[{}]'.format(roomName), ' ' * (logwidth - len(roomName) - 7), '│'],
          [green, blue, yellow, white, green]
        )
      self.printLog(['└' + '─' * (logwidth - 2) + '┘'], [green])
      self.printLog(['Select your room to join.'], [white])
      room = self.nInput(inputx, inputy, 30)
      send(self.clientSock, 'ROOM\0{}'.format(room))
      result = recieve(self.clientSock)
      if result == 'FAIL':
        self.printLog(
          ['Room', '[{}]'.format(room), ' does not exist. Try another.'],
          [white, yellow, white]
        )
      else:
        self.printLog(
          ['You joined to ', '[{}]'.format(room), '.'],
          [white, yellow, white]
        )
        break

    parse = recieve(self.clientSock).split('\0')
    self.printLog(
      ['Your position is ', '{}'.format(parse[1]), '.'],
      [white, red, yellow]
    )
    self.position = parse[1]

    self.printLog(
      ['Wait for rest of player to join.'], [white]
    )

    recieve(self.clientSock)
    self.printLog(['Game start!'], [cyan])
    
    strs = recieve(self.clientSock).split()
    numbers = list(map(lambda x : int(x), strs))
    board = [numbers[0:5], numbers[5:10], numbers[10:15], numbers[15:20], numbers[20:25]]
    self.player = Player(id, board)
    self.printBoard()
    self.turn = False

  def nPrint(self, x, y, strings, sets):
    i = 0
    for (string, setting) in zip(strings, sets):
      self.stdscr.addstr(y, x + i, string, curses.color_pair(setting))
      i += len(string)
    self.stdscr.refresh()

  def nInput(self, x, y, n):
    curses.echo()
    self.nPrint(x, y, ['>> '], [white])
    msg = self.stdscr.getstr(y, x + 3, n).decode('utf-8')
    curses.noecho()
    self.nPrint(x + 3, y, [' ' * n], [white])
    return msg

  def printLog(self, newLog, newSets):
    for i in range(logheight):
      self.nPrint(logx, logy + i, [' ' * logwidth], [white])
    
    for i in range(logheight - 1):
      self.logs[i] = self.logs[i + 1]
      self.sets[i] = self.sets[i + 1]
    
    self.logs[logheight - 1] = newLog
    self.sets[logheight - 1] = newSets
    
    for i in range(logheight):
      self.nPrint(logx, logy + i, self.logs[i], self.sets[i])
    
    rectangle(
      self.stdscr,
      logy - 1, logx - 1,
      logy + logheight, logx + logwidth
    )

  def printBoard(self):
    for i in range(5):
      self.nPrint(boardx, boardy + i, [self.player.nthLine(i)], [green])

  def run(self, sock):
    while True:
      msg = recieve(sock)
      parse = msg.split('\0')

      if parse[0] == 'PICK':
        self.player.pickNumber(int(parse[1]))
        self.printBoard()
        self.printLog(
          ['[{}]'.format(parse[2]), ' picked ', '{}'.format(parse[1]), '.'],
          [yellow, white, green, white])

      elif parse[0] == 'MESS':
        self.printLog(
          ['Message from ', '[{}]'.format(parse[1]), ': ', '\"{}\"'.format(parse[2])],
          [white, yellow, white, red])

      elif parse[0] == 'BINGO':
        self.printLog(
          ['[{}]'.format(parse[1]), ' achieved ', 'bingo!'],
          [yellow, white, red])

      elif parse[0] == 'TURN':
        self.printLog(['Your turn!'], [cyan])
        self.turn = True
        self.printLog(['Submit your pick.'], [white])

        while True:
          num = self.nInput(inputx, inputy, 30)
          if not(num.isdigit()):
            self.printLog(['Invalid number. try it again.'], [white])
          else:
            self.printLog(
              ['Your pick is ', '{}'.format(num), '.'],
              [white, green, white]
            )
            break

        if self.position == 'main culprit':
          self.printLog(['Submit your message to send:'], [white])
          msg = self.nInput(inputx, inputy, 30)
          send(sock, '{}\0{}\0{}'.format('PICK', num, msg))
        else:
          send(sock, '{}\0{}\0{}'.format('PICK', num, 'None'))
          
      elif parse[0] == 'DONE':
        send(sock, 'DONE')
        break
    self.printLog(['Press any key to exit.'], [cyan])
    self.stdscr.getch()

def main(scr):
  curses.use_default_colors()
  curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
  curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
  curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
  curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
  client = Client(scr)
  client.run(client.clientSock)
  client.clientSock.close()

 
if __name__ == "__main__":
    curses.wrapper(main)