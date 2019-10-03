import curses

from threading import Thread
from curses.textpad import rectangle

from protocol import send, recieve, newSocket, port
from player import Player

### locations of components

### log box
logx, logy = 1, 1
logwidth, logheight = 43, 20

### player input locates just below of the log box
inputx, inputy = logx, logy + logheight + 1
inputlength = 30

### bingo board
boardx, boardy = 46, 1

serverIP = '147.46.240.95'
localIP = '127.0.0.1'

### color constant
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

    ### empty log
    self.logs = [['']] * logheight
    self.sets = [[white]] * logheight
    
    ### draw basic ui
    rectangle(self.stdscr, boardy - 1, boardx - 1, boardy + 5, boardx + 15)
    rectangle(self.stdscr, logy - 1, logx - 1, logy + logheight, logx + logwidth)
    self.cPrint(inputx, inputy, ['>> '], [white])
    
    self.stdscr.refresh()

    ### connect to server
    self.clientSock = newSocket()
    self.clientSock.connect((serverIP, port))

  ### convenient print function
  def cPrint(self, x, y, strList, setList):
    ### print each strings in string list by color constant in sets
    i = 0
    for (string, setting) in zip(strList, setList):
      self.stdscr.addstr(y, x + i, string, curses.color_pair(setting))

      ### increase i in order to move cursor
      i += len(string)
    self.stdscr.refresh()

  ### input function
  def cInput(self):
    ### get input from player; it's location is constant during process
    curses.echo()
    msg = self.stdscr.getstr(inputy, inputx + 3, inputlength).decode('utf-8')
    curses.noecho()

    ### clear the player input from screen
    self.cPrint(inputx + 3, inputy, [' ' * inputlength], [white])
    return msg

  ### convenient print log function
  def printLog(self, newLog, newSets):
    ### clear the log box
    for i in range(logheight):
      self.cPrint(logx, logy + i, [' ' * logwidth], [white])
    
    ### shift the existing log by one
    for i in range(logheight - 1):
      self.logs[i] = self.logs[i + 1]
      self.sets[i] = self.sets[i + 1]
    
    ### add new log and setting
    self.logs[logheight - 1] = newLog
    self.sets[logheight - 1] = newSets
    
    ### print it again
    for i in range(logheight):
      self.cPrint(logx, logy + i, self.logs[i], self.sets[i])

  ### print board function
  def printBoard(self):
    for i in range(5):
      self.cPrint(boardx, boardy + i, [self.player.nthLine(i)], [green])

  ### from ID input to get bingo board
  def join(self):
    ### get ID from player until server says okay
    while True:
      self.printLog(['Submit your ID.'], [white])
      id = self.cInput()

      send(self.clientSock, id)
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

    ### get room ID from player until server says okay
    roomNames = recieve(self.clientSock).split('\0')[1:]
    while True:
      ### print the room list inside a box
      self.printLog(['┌' +  '─' * (logwidth - 2) + '┐'], [green])
      self.printLog(['│', 'Room lists', ' ' * (logwidth - 12), '│'], [green, white, white, green])
      
      for roomName in roomNames:
        self.printLog(
          ['│','>> ', '[{}]'.format(roomName), ' ' * (logwidth - len(roomName) - 7), '│'],
          [green, blue, yellow, white, green]
        )
      
      self.printLog(['└' + '─' * (logwidth - 2) + '┘'], [green])
      self.printLog(['Select your room to join.'], [white])

      ### get input from player
      room = self.cInput()
      send(self.clientSock, room)
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

    ### get position from server
    self.position =  recieve(self.clientSock)
    self.printLog(
      ['Your position is ', '{}'.format(self.position), '.'],
      [white, red, yellow]
    )
    
    ### wait for the server's start signal
    self.printLog(
      ['Wait for another players to join.'], [white]
    )

    recieve(self.clientSock)
    self.printLog(['Game start!'], [cyan])
    
    ### get board from server
    boardData = recieve(self.clientSock).split()
    numbers = list(map(lambda x : int(x), boardData))
    board = [numbers[0:5], numbers[5:10], numbers[10:15], numbers[15:20], numbers[20:25]]

    self.player = Player(id, board)
    self.printBoard()
  
  ### game process function
  def run(self, sock):
    while True:
      command = recieve(sock).split('\0')

      if command[0] == 'PICK':
        ### apply other player's pick and print log
        self.player.pickNumber(int(command[1]))
        self.printBoard()

        self.printLog(
          ['[{}]'.format(command[2]), ' picked ', '{}'.format(command[1]), '.'],
          [yellow, white, green, white])

      elif command[0] == 'MESS':
        ### print the message from other player or server
        self.printLog(
          ['Message from ', '[{}]'.format(command[1]), ': ', '\"{}\"'.format(command[2])],
          [white, yellow, white, red])

      elif command[0] == 'BINGO':
        ### print the player ID who achieved bingo
        self.printLog(
          ['[{}]'.format(command[1]), ' achieved ', 'bingo!'],
          [yellow, white, red])

      elif command[0] == 'TURN':
        ### turn process
        self.printLog(['Your turn!'], [cyan])
        self.printLog(['Submit your pick.'], [white])

        ### get valid number input from player
        while True:
          num = self.cInput()
          if not(num.isdigit()):
            self.printLog(['Invalid number. try it again.'], [white])
          else:
            self.printLog(
              ['Your pick is ', '{}'.format(num), '.'],
              [white, green, white]
            )
            break

        if self.position == 'main culprit':
          ### if player is main culprint, also get message as an input
          self.printLog(['Submit your message to send:'], [white])
          msg = self.cInput()
          send(sock, '{}\0{}\0{}'.format('PICK', num, msg))
        else:
          ### if player is not main culprint, just send None as a place holder
          send(sock, '{}\0{}\0{}'.format('PICK', num, 'None'))
          
      elif command[0] == 'DONE':
        ### reflect the done signal to server
        send(sock, 'DONE')
        break
    self.printLog(['Press any key to exit.'], [cyan])
    self.stdscr.getch()

def main(scr):
  ### bind the color setting to color constants
  curses.use_default_colors()
  curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
  curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
  curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
  curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

  ### create and run the client
  client = Client(scr)  
  client.join()
  client.run(client.clientSock)
  client.clientSock.close()
 
if __name__ == "__main__":
    curses.wrapper(main)