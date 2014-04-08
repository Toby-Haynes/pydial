import SocketServer
import socket
import struct
import time
import platform
import random

from .common import (SSDP_PORT, SSDP_ADDR, SSDP_ST)

UPNP_SEARCH = 'M-SEARCH * HTTP/1.1'
# If we get a M-SEARCH with no or invalid MX value, wait up
# to this many seconds before responding to prevent flooding
CACHE_DEFAULT = 1800
DELAY_DEFAULT = 10
PRODUCT = 'PyDial Server'
VERSION = '0.01'

SSDP_REPLY = 'HTTP/1.1 200 OK\r\n' + \
               'LOCATION: {}\r\n' + \
               'CACHE-CONTROL: {}\r\n' + \
               'EXT:\r\n' + \
               'BOOTID.UPNP.ORG: 1\r\n' + \
               'SERVER: {}/{} UPnP/1.1 {}/{}\r\n' + \
               'ST: {}\r\n'.format(SSDP_ST) + \
               'DATE: {}\r\n' + '\r\n'


class SSDPHandler(SocketServer.BaseRequestHandler):
     """
     RequestHandler object to deal with DIAL UPnP search requests.

     Note that per the SSD protocol, the server will sleep for up
     to the number of seconds specified in the MX value of the 
     search request- this may cause the system to not respond if
     you are not using the multi-thread or forking mixin.
     """
     def __init__(self, request, client_address, server):
          SocketServer.BaseRequestHandler.__init__(self, request, 
                         client_address, server)
          self.max_delay = DELAY_DEFAULT

     def handle(self):
          """
          Reads data from the socket, checks for the correct
          search parameters and UPnP search target, and replies
          with the application URL that the server advertises.
          """
          data = self.request[0].strip().split('\r\n')
          if data[0] != UPNP_SEARCH:
               return
          else:
               dial_search = False
               for line in data[1:]:
                    field, val = line.split(':', 1)
                    if field.strip() == 'ST' and val.strip() == SSDP_ST:
                         print 'valid request'
                         dial_search = True
                    elif field.strip() == 'MX':
                         try:
                              self.max_delay = int(val.strip())
                         except ValueError:
                              # Use default
                              pass
               if dial_search:
                    self._send_reply()

     def _send_reply(self):
          """Sends reply to SSDP search messages."""
          time.sleep(random.randint(0, self.max_delay))
          _socket = self.request[1]
          timestamp = time.strftime("%A, %d %B %Y %H:%M:%S GMT", 
                    time.gmtime())
          reply_data = SSDP_REPLY.format(self.server.device_url,
                    self.server.cache_expire, self.server.os_id,
                    self.server.os_version, self.server.product_id,
                    self.server.product_version, timestamp)

          sent = 0
          while sent < len(reply_data):
               sent += _socket.sendto(reply_data, self.client_address)

          return

class SSDPServer(SocketServer.UDPServer):
     """
     Inherits from SocketServer.UDPServer to implement the SSDP
     portions of the DIAL protocol- listening for search requests
     on port 1900 for messages to the DIAL multicast group and 
     replying with information on the URL used to request app
     actions from the server.

     The following attributes are set by default, but should be
     changed if you want to use this class as the basis for a 
     more complete server:
     product_id - Name of the server/product. Defaults to PyDial server
     product_version - Product version. Defaults to whatever version
          number PyDial was given during the last release.
     os_id - Operating system name. Set via platform.system().
     os_version - Operating system version. Set via platform.release().
     cache_expire - Time (in seconds) before a SSDP reply/advertisement
          expires.
     """
     def __init__(self, device_url, host='', port=SSDP_PORT):
          SocketServer.UDPServer.__init__(self, (host, port), 
                    SSDPHandler, False)
          self.allow_reuse_address = True
          self.server_bind()
          mreq = struct.pack("=4sl", socket.inet_aton(SSDP_ADDR),
                                       socket.INADDR_ANY)
          self.socket.setsockopt(socket.IPPROTO_IP, 
                    socket.IP_ADD_MEMBERSHIP, mreq)
          self.device_url = device_url
          self.product_id = PRODUCT
          self.product_version = VERSION
          self.os_id = platform.system()
          self.os_version = platform.release()
          self.cache_expire = CACHE_DEFAULT

     def start(self):
          self.serve_forever()

class DialServer(object):
     def __init__(self):
          pass

     def add_app(self, app_id, app_path):
          pass
