# Copyright 2023 Nicolas OBERLI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from .protocol import Protocol
from .common import split


class SDIO(Protocol):
    """
    SDIO protocol handler

    :example:

    >>> import pyHydrabus
    >>> m=pyHydrabus.SDIO('/dev/hydrabus')
    >>> # CMD0 - IDLE
    >>> s.send_no(0,0)

    >>> #CMD8 - OP_COND
    >>> s.send_short(8, 0x000001aa)

    >>> #ACMD41 *2
    >>> s.send_short(55,0)
    >>> s.send_short(41, 0x50ff8000)
    >>> s.send_short(55,0)
    >>> s.send_short(41, 0x50ff8000)

    >>> #CMD2 - GET CID
    >>> cid = s.send_long(2, 0)
    >>> print(f"CID: {cid.hex()}")

    >>> #CMD9 - RADDR
    >>> raddr = int.from_bytes(s.send_short(3, 0), byteorder='little')
    >>> print(f"RADDR: {raddr:08x}")

    >>> #CSD
    >>> csd = s.send_long(9, raddr)
    >>> print(f"CSD: {csd.hex()}")

    >>> #Select card
    >>> print(s.send_short(7, raddr).hex())

    >>> #Get status
    >>> print(s.send_short(13, raddr).hex())

    """

    __SDIO_DEFAULT_CONFIG = 0b0

    def __init__(self, port=""):
        self._config = self.__SDIO_DEFAULT_CONFIG
        super().__init__(name=b"SDI1", fname="SDIO", mode_byte=b"\x0e", port=port)

    def _configure_port(self):
        CMD = 0b10000000
        CMD = CMD | self._config

        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        if self._hydrabus.read(1) == b"\x01":
            return True
        else:
            self._logger.error("Error setting config.")
            return False

    @property
    def bus_width(self):
        """
        Data bus width (1 or 4)
        """
        if self._config & 0b1:
            return 4
        else:
            return 1

    @bus_width.setter
    def bus_width(self, value):
        if value == 1:
            self._config = self._config & ~(1)
        elif value == 4:
            self._config = self._config | (1)
        else:
            print("Invalid value (1 or 4)")
        self._configure_port()

    @property
    def frequency(self):
        """
        Select SDIO clock frequency
            0: Slow (400kHz)
            1: Fast (24MHz)
        """
        if self._config & 0b10:
            return 1
        else:
            return 0

    @frequency.setter
    def frequency(self, value):
        if value == 0:
            self._config = self._config & ~(1<<1)
        elif value == 1:
            self._config = self._config | (1<<1)
        else:
            print("Invalid value (0 or 1)")
        self._configure_port()

    def send_no(self, cmd_id, cmd_arg):
        """
        Send SDIO command with no reply from card

        :param cmd_id: Command ID (1 byte)
        :type cmd_id: int
        :param cmd_arg: Command argument (4 bytes)
        :type cmd_id: int
        """
        CMD = 0b00000100
        self._hydrabus.write(CMD.to_bytes(1, byteorder="little"))
        self._hydrabus.write(cmd_id.to_bytes(1, byteorder="little"))
        self._hydrabus.write(cmd_arg.to_bytes(4, byteorder="little"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        return status == 1

    def send_short(self, cmd_id, cmd_arg):
        """
        Send SDIO command with short reply from card

        :param cmd_id: Command ID (1 byte)
        :type cmd_id: int
        :param cmd_arg: Command argument (4 bytes)
        :type cmd_id: int

        :return: Reply status, None in case of error
        :rtype: bytes
        """
        CMD = 0b00000100
        CMD = 0b00000101
        self._hydrabus.write(CMD.to_bytes(1, byteorder="little"))
        self._hydrabus.write(cmd_id.to_bytes(1, byteorder="little"))
        self._hydrabus.write(cmd_arg.to_bytes(4, byteorder="little"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        if status == 1:
            return self._hydrabus.read(4)
        else:
            return None

    def send_long(self, cmd_id, cmd_arg):
        """
        Send SDIO command with long reply from card

        :param cmd_id: Command ID (1 byte)
        :type cmd_id: int
        :param cmd_arg: Command argument (4 bytes)
        :type cmd_id: int

        :return: Reply status, None in case of error
        :rtype: bytes
        """
        CMD = 0b00000110
        self._hydrabus.write(CMD.to_bytes(1, byteorder="little"))
        self._hydrabus.write(cmd_id.to_bytes(1, byteorder="little"))
        self._hydrabus.write(cmd_arg.to_bytes(4, byteorder="little"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        if status == 1:
            return self._hydrabus.read(16)
        else:
            return None

    def write(self, cmd_id, cmd_arg, data):
        """
        Write SDIO block

        :param cmd_id: Command ID (1 byte)
        :type cmd_id: int
        :param cmd_arg: Command argument (4 bytes)
        :type cmd_id: int
        :param data: Data to be written (512 bytes)
        :type data: bytes

        :return: Transaction status
        :rtype: Boolean
        """
        CMD = 0b00001001

        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        self._hydrabus.write(cmd_id.to_bytes(1, byteorder="little"))
        self._hydrabus.write(cmd_arg.to_bytes(4, byteorder="little"))
        self._hydrabus.write(data)

        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")

        return status == 1

    def read(self, cmd_id, cmd_arg):
        """
        Read SDIO block

        :param cmd_id: Command ID (1 byte)
        :type cmd_id: int
        :param cmd_arg: Command argument (4 bytes)
        :type cmd_id: int

        :return: Read data
        :rtype: bytes
        """
        CMD = 0b00001101
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        self._hydrabus.write(cmd_id.to_bytes(1, byteorder="little"))
        self._hydrabus.write(cmd_arg.to_bytes(4, byteorder="little"))
        status = int.from_bytes(self._hydrabus.read(1), byteorder="little")
        if status == 1:
            return self._hydrabus.read(512)
        else:
            return b''
