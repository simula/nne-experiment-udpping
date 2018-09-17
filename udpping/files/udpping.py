#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Container-based UDPPing for NorNet Edge
#
# Copyright (C) 2018 by Thomas Dreibholz
# Copyright (C) 2012-2017 by Džiugas Baltrūnas
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: dreibh@simula.no


# Ubuntu/Debian dependencies:
# python-netifaces

import socket
import netifaces
import time
import sys
import argparse
import signal
import threading
from datetime import datetime
import logging, logging.config


# ###### Constants ##########################################################
RTT_VALID_MIN = 0     # Minimum valid RTT (in s)
RTT_VALID_MAX = 300   # Maximum valid RTT (in s)


# ###### Global variables ###################################################
running = True
restart = False


# ###### Signal handler #####################################################
def handler(signum, frame):
   global running
   running = False


# ###### Receiver thread ####################################################
class Receiver(threading.Thread):
   # ###### Constructor #####################################################
   def __init__(self, udpSocket, lock, requests, timeout):
      threading.Thread.__init__(self)
      self.udpSocket = udpSocket
      self.udpSocket.settimeout(1)
      self.lock      = lock
      self.requests  = requests
      self.timeout   = timeout
      self.daemon    = True
      self.terminate = threading.Event()

   # ###### Main loop #######################################################
   def run(self):
      global running, restart
      logging.info("Starting receiver thread")

      # ====== Reception loop ===============================================
      while running and not self.terminate.is_set():
         payload = None
         try:
            # ====== Receive response =======================================
            payload          = self.udpSocket.recv(2048)
            receiveTimeStamp = time.time()   # time stamp in s

            # ====== Get RTT ================================================
            [seqNumber, sendTimeStamp] = payload.strip().split(' ')
            sendTimeStamp = int(sendTimeStamp) / 1000000.0   # time stamp in s
            rtt = receiveTimeStamp - sendTimeStamp
            if not ((rtt >= RTT_VALID_MIN) and (rtt <= RTT_VALID_MAX)):
               logging.warn("Invalid RTT: %s", payload)
               continue
            sendTimeStampString = \
               datetime.utcfromtimestamp(sendTimeStamp).strftime('%Y-%m-%d %H:%M:%S.%f')

            # ====== Check for duplicate or expired =========================
            if payload in self.requests:
               e = 0
            else:
               e = 1
               logging.warn("Duplicate or expired, seqNumber=%d sendTimeStampString=%s",
                            int(seqNumber), sendTimeStampString)

            # ====== Log result =============================================
            mlogger.info(
               '%s\t%d\t%d\t<d e="%d"><rtt>%.6f</rtt></d>',
               sendTimeStampString, opts.instance, int(seqNumber), e, rtt
            )

         # ====== Error handling ============================================
         except socket.timeout:
            pass
         except IOError:
            logging.exception("IOError while handling a reply, restarting")
            restart = True
            break
         except:
            logging.exception("Exception while handling a reply")

         # ====== Clean-up ==================================================
         finally:
            # ====== Remove request =========================================
            with self.lock:
               if payload in self.requests: del self.requests[payload]

            # ====== Expire all timed-out requests, logging them as loss ====
            try:
               loss = [p for p in self.requests.keys() if time.time() - self.requests[p] > opts.timeout]
               for payload in loss:
                  [seqNumber, sendTimeStamp] = payload.strip().split(' ')
                  sendTimeStamp       = int(sendTimeStamp) / 1000000.0   # time stamp in s
                  sendTimeStampString = \
                     datetime.utcfromtimestamp(sendTimeStamp).strftime('%Y-%m-%d %H:%M:%S.%f')
                  mlogger.info(
                     '%s\t%d\t%d\t<d e="0"/>',
                     sendTimeStampString, opts.instance, int(seqNumber)
                  )
                  with self.lock:
                     del self.requests[payload]
            except:
               logging.exception("Exception while writing expired packets")

      # ====== Shut down ====================================================
      logging.debug("Stopping receiver thread")



# ###### Main program #######################################################

# ====== Handle arguments ===================================================
op = argparse.ArgumentParser(description='UDP Ping for NorNet Edge')
op.add_argument('-i', '--instance',   help="Measurement instance ID", type=int, required=True)
op.add_argument('-d', '--dport',      help='Destination port',        type=int, default=7)
op.add_argument('-D', '--daddr',      help='Destination IP',          default='128.39.37.70')
op.add_argument('-I', '--iface',      help='Interface name',          required=True)
op.add_argument('-S', '--psize',      help='Payload size',            type=int, default=20)
op.add_argument('-t', '--timeout',    help='Reply timeout',           type=int, default=60)
op.add_argument('-N', '--network_id', help='Network identifier',      type=int, default=None)
opts = op.parse_args()

# FIXME: check if arguments are valid

# ====== Initialise logger ==================================================
MBBM_LOGGING_CONF = {
   'version': 1,
   'handlers': {
      'default': {
         'level': 'DEBUG',
         'class': 'logging.handlers.TimedRotatingFileHandler',
         'formatter': 'standard',
         'filename': '/nne/log/uping_%d.log' % (opts.instance),
         'when': 'D'
      },
      'mbbm': {
         'level': 'DEBUG',
         'class': 'logging.handlers.TimedRotatingFileHandler',
         'formatter': 'mbbm',
         'filename': '/nne/data/uping_%d.dat' % (opts.instance),
         'when': 'S',
         'interval': 15
      }
   },
   'formatters': {
      'standard': {
         'format': '%(asctime)s %(levelname)s [PID=%(process)d] %(message)s'
      },
      'mbbm': {
         'format': '%(message)s',
      }
   },
   'loggers': {
      'mbbm': {
         'handlers': ['mbbm'],
         'level': 'DEBUG',
         'propagate': False,
      }
   },
   'root': {
      'level': 'DEBUG',
      'handlers': ['default'],
   }
}

logging.config.dictConfig(MBBM_LOGGING_CONF)
mlogger = logging.getLogger('mbbm')


# ====== Initialise mutex and signal handlers ===============================
udpSocket = None
recv      = None
requests  = {}
lock      = threading.Lock()

signal.signal(signal.SIGINT,  handler)
signal.signal(signal.SIGTERM, handler)

if opts.network_id:
   sport = 10000 + 10 * int(socket.gethostname()[3:]) + opts.network_id
else:
   sport = 0


# ====== Main loop ==========================================================
seqNumber = 1
while running:
   try:
      if udpSocket:
         udpSocket.close()
         udpSocket = None
      if recv:
         if recv.isAlive():
            recv.terminate.set()
            recv.join()
         recv = None
      if restart:
         restart = False

      sip = netifaces.ifaddresses(opts.iface)[netifaces.AF_INET][0]['addr']

      # ====== Create socket ================================================
      udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      try:
         udpSocket.bind((sip, sport))
      except: # fallback to a random source port
         if sport > 0:
            udpSocket.bind((sip, 0))
      udpSocket.connect((opts.daddr, opts.dport))

      # ====== Create receiver thread =======================================
      recv = Receiver(udpSocket, lock, requests, timeout=opts.timeout)
      recv.start()

      # ====== Send loop ====================================================
      logging.debug("Starting")
      while running and not restart:
         # ====== Send UDP Ping =============================================
         sendTimeStamp = time.time()
         payload       = \
            '%d %d' % (seqNumber, int(sendTimeStamp * 1000000))
         if len(payload) < opts.psize: # FIXME: use struct.pack
            payload = (opts.psize - len(payload)) * '0' + payload
         with lock:
            requests[payload] = sendTimeStamp
         udpSocket.send(payload)

         # ====== Increment sequence number =================================
         if seqNumber >= sys.maxint:
            seqNumber = 1   # roll over
         else:
            seqNumber = seqNumber + 1

         # ====== Wait ======================================================
         time.sleep(1 - (time.time() - sendTimeStamp))

   # ====== Handle error ====================================================
   except:
      logging.exception("Error")
      time.sleep(15)


# ====== Shut down ==========================================================
if recv:
   try:
      recv.join(5000)
   except:
      pass
logging.debug("Exiting")
