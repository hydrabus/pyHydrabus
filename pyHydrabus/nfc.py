# Copyright 2019 Nicolas OBERLI
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


class NFC(Protocol):
    """
    NFC protocol handler

    :example:

    >>> import pyHydrabus
    >>> n=pyHydrabus.NFC('/dev/hydrabus')
    >>> # Set mode to ISO 14443A
    >>> n.mode = pyHydrabus.NFC.MODE_ISO_14443A
    >>> # Set radio ON
    >>> n.rf = 1
    >>> # Send REQA, get ATQA
    >>> n.write_bits(b'\x26', 7)
    >>> # Send anticol, read ID
    >>> n.write(b'\x93\x20', 0).hex()

    """

    MODE_ISO_14443A = 0
    MODE_ISO_15693 = 1

    def __init__(self, port=""):
        self._rf = 0
        self._mode = 0
        super().__init__(name=b"NFC1", fname="NFC-Reader", mode_byte=b"\x0c", port=port)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        CMD = 0b00000110
        CMD |= value
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        self._mode = value

    @property
    def rf(self):
        return self._rf

    @rf.setter
    def rf(self, value):
        CMD = 0b00000010
        CMD |= value
        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        self._rf = value

    def write(self, data=b"", crc=0):
        """
        Write bytes on NFC
        https://github.com/hydrabus/hydrafw/wiki/HydraFW-binary-NFC-Reader-mode-guide#send-bytes-0b00000101

        :param data: Data to be sent
        :type data: bytes
        """
        CMD = 0b00000101

        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        self._hydrabus.write(crc.to_bytes(1, byteorder="big"))
        self._hydrabus.write(len(data).to_bytes(1, byteorder="big"))
        self._hydrabus.write(data)

        rx_len = int.from_bytes(self._hydrabus.read(1), byteorder="little")

        return self._hydrabus.read(rx_len)

    def write_bits(self, data=b"", num_bits=0):
        """
        Write bits on NFC
        https://github.com/hydrabus/hydrafw/wiki/HydraFW-binary-NFC-Reader-mode-guide#send-bits-0b00000100

        :param data: Data to be sent
        :type data: byte
        :param num_bits: number of bits to send
        :type num_bits: int
        """
        CMD = 0b00000100

        self._hydrabus.write(CMD.to_bytes(1, byteorder="big"))
        self._hydrabus.write(data)
        self._hydrabus.write(num_bits.to_bytes(1, byteorder="big"))

        rx_len = int.from_bytes(self._hydrabus.read(1), byteorder="little")

        return self._hydrabus.read(rx_len)
