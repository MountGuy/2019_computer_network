class Player:
  def __init__(self, id, board):
    self.numberBoard = board
    self.id = id
    list = [False] * 25
    self.selectBoard = [list[0:5], list[5:10], list[10:15], list[15:20], list[20:25]]

  def printBoard(self):
    print(self.id)
    for i in range(0, 5):
      for j in range(0, 5):
        if self.selectBoard[i][j] == False:
          print('{:2d} '.format(self.numberBoard[i][j]), end = '')
        else:
          print('□  ', end = '')
      print()

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