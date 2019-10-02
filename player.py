class Player:
  def __init__(self, id, board):
    self.numberBoard = board
    self.id = id
    list = [False] * 25
    self.selectBoard = [list[0:5], list[5:10], list[10:15], list[15:20], list[20:25]]

  ### returns a string of board to send with socket
  def packedBoard(self):
    string = ['', '', '', '', '']
    board = self.numberBoard
    for i in range(0, 5):
      string[i] = '{} {} {} {} {}\n'.format(board[i][0], board[i][1], board[i][2], board[i][3], board[i][4])
    return '{}{}{}{}{}'.format(string[0], string[1], string[2], string[3], string[4])

  ### returns a string of nth line of board
  def nthLine(self, n):
    result = ''
    for i in range(5):
      if self.selectBoard[n][i] == False:
        result += '{:2d} '.format(self.numberBoard[n][i])
      else:
        result += '[] '
    return result

  ### basic functions of bingo game
  def pickNumber(self, n):
    for i in range(0, 5):
      for j in range(0, 5):
        if self.numberBoard[i][j] == n:
          self.selectBoard[i][j] = True
          return

  def checkBingo(self):
    for i in range(0, 5):
      check = True
      for j in range(0, 5):
        if self.selectBoard[i][j] == False:
          check = False
      if check:
        return True
    for j in range(0, 5):
      check = True
      for i in range(0, 5):
        if self.selectBoard[i][j] == False:
          check = False
      if check:
        return True
    return False