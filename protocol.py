utf = 'utf-8'

def send(sock, msg):
  length = '{:4d}'.format(len(msg))
  sock.send(length.encode(utf))
  sock.send(msg.encode(utf))

def recieve(sock):
  n = int(sock.recv(4).decode(utf))
#  print('recieved message length:', n)
  string = sock.recv(n).decode(utf)
#  print('recieved string:', string)
  return string
