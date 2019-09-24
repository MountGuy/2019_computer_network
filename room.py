import random
from player import Player

class Room:
  def __init__(self, roomName):
    self.roomName = roomName
    self.playerNum = 0
    self.players = []
    return

  def addPlayer(self, playerID):
    numbers = range(1, 26)
    numbers = random.sample(range(1,100), 25)
    board = [numbers[0:5], numbers[5:10], numbers[10:15], numbers[15:20], numbers[20:25]]
    self.players.append(Player(playerID, board))
    self.playerNum = self.playerNum + 1

  def printStatus(self):
    i = 0
    for player in self.players:
      i = i + 1
      print('#{} {}'.format(i, player.id))
      player.printBoard()
      print()

  def pickNumber(self, n):
    for player in self.players:
      player.pickNumber(n)

  def checkBingo(self):
    result = False
    for player in self.players:
      if player.checkBingo():
        print('{} wins the game!'.format(player.id))
        result = True
    return result

  def getBoard(self, playerID):
    for player in self.players:
      if player.id == playerID:
        return player.numberBoard
