# -*- coding: utf-8 -*-
#
# AWL simulator - TCP hardware interface
#
# Copyright 2013 Michael Buesch <m@bues.ch>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from __future__ import division, absolute_import, print_function, unicode_literals

from awlsim.core.hardware import AbstractHardwareInterface, HwParamDesc_bool
from awlsim.core.operators import AwlOperator
from awlsim.core.datatypes import AwlOffset

import threading
import SocketServer


class MyTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        self.request.sendall(self.data.upper())


class HardwareInterface(AbstractHardwareInterface):
    name = "tcp"

    paramDescs = [
        HwParamDesc_bool("dummyParam", description="Unused dummy parameter"),
    ]

    def __init__(self, sim, parameters):
        AbstractHardwareInterface.__init__(self, sim=sim, parameters=parameters)

    def doStartup(self):
        server = SocketServer.TCPServer(('127.0.0.1', 5000), MyTCPHandler)
        t = threading.Thread(target=server.serve_forever)
        t.daemon = True
        t.start()

    def doShutdown(self):
        pass

    def readInputs(self):
        # Get the first input dword and write it back.
        dword = self.sim.cpu.fetch(AwlOperator(AwlOperator.MEM_E, 32, AwlOffset(self.inputAddressBase)))
        dwordBytes = bytearray((((dword >> 24) & 0xFF),
                                ((dword >> 16) & 0xFF),
                                ((dword >> 8) & 0xFF),
                                (dword & 0xFF)))
        self.sim.cpu.storeInputRange(self.inputAddressBase, dwordBytes)

    def writeOutputs(self):
        # Fetch a data range, but don't do anything with it.
        outData = self.sim.cpu.fetchOutputRange(self.outputAddressBase, 512)
        assert outData

    def directReadInput(self, accessWidth, accessOffset):
        if accessOffset < self.inputAddressBase:
            return None
        # Just read the current value from the CPU and return it.
        return self.sim.cpu.fetch(AwlOperator(AwlOperator.MEM_E, accessWidth, AwlOffset(accessOffset)))

    def directWriteOutput(self, accessWidth, accessOffset, data):
        if accessOffset < self.outputAddressBase:
            return False
        # Just pretend we wrote it somewhere.
        return True
