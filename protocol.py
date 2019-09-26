import socket

port = 8080

def send(sock, msg):
  length = '{:4d}'.format(len(msg))
  sock.send(length.encode('utf-8'))
  sock.send(msg.encode('utf-8'))

def recieve(sock):
  n = int(sock.recv(4).decode('utf-8'))
#  print('recieved message length:', n)
  string = sock.recv(n).decode('utf-8')
#  print('recieved string:', string)
  return string

def newSocket():
  return socket.socket(socket.AF_INET, socket.SOCK_STREAM)