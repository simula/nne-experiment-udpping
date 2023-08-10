# =================================================================
#          #     #                 #     #
#          ##    #   ####   #####  ##    #  ######   #####
#          # #   #  #    #  #    # # #   #  #          #
#          #  #  #  #    #  #    # #  #  #  #####      #
#          #   # #  #    #  #####  #   # #  #          #
#          #    ##  #    #  #   #  #    ##  #          #
#          #     #   ####   #    # #     #  ######     #
#
#       ---   The NorNet Testbed for Multi-Homed Systems  ---
#                       https://www.nntb.no
# =================================================================
#
# Container-based UDPPing for NorNet Edge
#
# Copyright (C) 2018-2022 by Thomas Dreibholz
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

FROM --platform=linux/amd64 alpine

COPY files/* /opt/nne/

RUN apk add python3 curl jq

RUN apk add joe less psmisc mlocate bash-completion && updatedb
#RUN echo "export TERM=vt100" >>/root/.bashrc

#RUN apt-get clean

#ENTRYPOINT [ "dumb-init", "--", "/usr/bin/python3", "/opt/monroe/udpping-launcher" ]
#ENTRYPOINT [ "/bin/bash" ]
ENTRYPOINT [ "/opt/nne/udpping-launcher" ]
