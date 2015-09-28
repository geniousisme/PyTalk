import select
import socket
import sys

from utils import User
from utils import RECV_BUFFER, NEED_USR_N_PASS, USR_PASS_ERROR, \
                  CLIENT_IP_BLOCK, USR_PASS_KEY
from utils import create_socket, msg_parser,  load_usr_pass

localhost    = "127.0.0.1"
default_port = 8080

class Server(object):
      
      def __init__(self, host=localhost, port=default_port):
          self.server_socket = create_socket((host, port))
          self.connections   = [self.server_socket]
          self.usr_database  = load_usr_pass()
          self.login_count   = {}
          print "PyTalk server started on port " + str(port)

      def server_loop(self):
          status = 1;
          while status:
                try:
                    read_users, write_users, error_sockets =                  \
                                     select.select(self.connections, [], [], 0)
                    for user in read_users:
                        if user is self.server_socket: # new client join
                           new_user, addr = self.server_socket.accept()
                           new_user       = User(new_user)
                           self.connections.append(new_user)
                           new_user.socket.send(NEED_USR_N_PASS)
                           self.login_count[new_user] = 0
                           print "Client %s at %s now join!" % (new_user, addr)
                        else: # new message
                           msg = user.socket.recv(RECV_BUFFER)
                           if msg:
                              if USR_PASS_KEY in msg:
                                 if self.is_usr_login(user, msg):
                                    user.socket.send("Welcome %s to join PyTalk!\n" % user.name)
                                    self.broadcast(user, "User: %s now joining PyTalk\n" % user.name)
                              else:    
                                 msg_parser(user, msg)
                                 self.broadcast(user, "\r" + '[' + str(user.socket.getpeername()) + '] ' + msg)
                           else: # no msg, user down, close connection
                              self.remove_user(user)

                    for socket in error_sockets:
                        socket.close()
                        self.connections.remove(socket)

                except KeyboardInterrupt, SystemExit:
                       print "\nPyTalk Server Close..."
                       status = 0
          
          self.server_socket.close()  

      def is_usr_login(self, user, msg):
          if self.is_usr_pass_correct(user, msg):
             self.login_count[user] = 0
             return True
          else:
             self.login_count[user] += 1
             if self.login_count[user] < 3:
                user.socket.send(USR_PASS_ERROR)
             else:
                user.socket.send(CLIENT_IP_BLOCK)
                self.remove_user(user)
                del self.login_count[user]   
             return False
             
          
      def is_usr_pass_correct(self, user, msg):
          key, username, password = msg.split('#')
          if self.usr_database.get(username) != password:
             return False
          else:
             user.name = username
             return True

      def remove_user(self, user):
          user.socket.close()
          if user in self.connections:
             self.connections.remove(user)

      def broadcast(self, user, message):
          for usr in self.connections:
              if usr != self.server_socket and usr != user:
                 try:
                    usr.socket.send(message)
                 except:
                    self.remove_user(sock)
          
      def run(self):
          self.server_loop();


if __name__ == "__main__":
   server = Server(port = 8080 if len(sys.argv) < 2 else int(sys.argv[1]))
   server.run()