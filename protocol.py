import socket

### port number which is shared between client and server
port = 20332

### send wrapping function
def send(sock, msg):
  ### send 4 characters which means the length of body first
  length = '{:4d}'.format(len(msg))
  sock.send(length.encode('utf-8'))

  ### then send the body
  sock.send(msg.encode('utf-8'))

def recieve(sock):
  ### read 4 characters from socket first
  n = int(sock.recv(4).decode('utf-8'))

  ### then read n characters
  string = sock.recv(n).decode('utf-8')
  return string

### create socket wrapping function
def newSocket():
  return socket.socket(socket.AF_INET, socket.SOCK_STREAM)