import random
from player import Player

class Room:
  def __init__(self, roomName):
    self.roomName = roomName
    self.players = []
    return

  def addPlayer(self, playerID):
    numbers = range(1, 26)
    numbers = random.sample(range(1,100), 25)
    board = [numbers[0:5], numbers[5:10], numbers[10:15], numbers[15:20], numbers[20:25]]
    self.players.append(Player(playerID, board))

  def printStatus(self, hinge):
    for player in self.players:
      print('{:16s}'.format(player.id), end = '')
      print(' ' * hinge, end = '')
    print()
    for i in range(5):
      for player in self.players:
        print('{} '.format(player.nthLine(i)), end = '')
        print(' ' * hinge, end = '')
      print()

  def pickNumber(self, n):
    for player in self.players:
      player.pickNumber(n)

  def checkBingo(self):
    result = False
    winner = []
    for player in self.players:
      if player.checkBingo():
        print('{} wins the game!'.format(player.id))
        winner.append(player.id)
        result = True
    return (result, winner)

  def getPackedBoard(self, playerID):
    for player in self.players:
      if player.id == playerID:
        return player.packedBoard()
