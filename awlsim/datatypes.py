# -*- coding: utf-8 -*-
#
# AWL data types
# Copyright 2012-2013 Michael Buesch <m@bues.ch>
#
# Licensed under the terms of the GNU General Public License version 2.
#

from awlsim.util import *
from awlsim.timers import *
from awlsim.datatypehelpers import *


class AwlOffset(object):
	"Memory area offset"

	def __init__(self, byteOffset, bitOffset=0):
		self.byteOffset = byteOffset
		self.bitOffset = bitOffset

class AwlDataType(object):
	# Data type IDs
	enum.start
	TYPE_VOID	= enum.item
	TYPE_BOOL	= enum.item
	TYPE_BYTE	= enum.item
	TYPE_WORD	= enum.item
	TYPE_DWORD	= enum.item
	TYPE_INT	= enum.item
	TYPE_DINT	= enum.item
	TYPE_REAL	= enum.item
	TYPE_S5T	= enum.item
	TYPE_TIME	= enum.item
	TYPE_DATE	= enum.item
	TYPE_TOD	= enum.item
	TYPE_CHAR	= enum.item
	TYPE_ARRAY	= enum.item
	enum.end

	__name2id = {
		"VOID"		: TYPE_VOID,
		"BOOL"		: TYPE_BOOL,
		"BYTE"		: TYPE_BYTE,
		"WORD"		: TYPE_WORD,
		"DWORD"		: TYPE_DWORD,
		"INT"		: TYPE_INT,
		"DINT"		: TYPE_DINT,
		"REAL"		: TYPE_REAL,
		"S5TIME"	: TYPE_S5T,
		"TIME"		: TYPE_TIME,
		"DATE"		: TYPE_DATE,
		"TIME_OF_DAY"	: TYPE_TOD,
		"CHAR"		: TYPE_CHAR,
		"ARRAY"		: TYPE_ARRAY,
	}
	__id2name = pivotDict(__name2id)

	# Width table for trivial types
	type2width = {
		TYPE_VOID	: 0,
		TYPE_BOOL	: 1,
		TYPE_BYTE	: 8,
		TYPE_WORD	: 16,
		TYPE_DWORD	: 32,
		TYPE_INT	: 16,
		TYPE_DINT	: 32,
		TYPE_REAL	: 32,
		TYPE_S5T	: 16,
		TYPE_TIME	: 32,
		TYPE_DATE	: 16,
		TYPE_TOD	: 32,
		TYPE_CHAR	: 8,
	}

	# Signedness table for trivial types
	type2signed = {
		TYPE_VOID	: False,
		TYPE_BOOL	: False,
		TYPE_BYTE	: False,
		TYPE_WORD	: False,
		TYPE_DWORD	: False,
		TYPE_INT	: True,
		TYPE_DINT	: True,
		TYPE_REAL	: True,
		TYPE_S5T	: False,
		TYPE_TIME	: False,
		TYPE_DATE	: False,
		TYPE_TOD	: False,
		TYPE_CHAR	: False,
	}

	@classmethod
	def name2type(cls, nameTokens):
		if isinstance(nameTokens, str):
			nameTokens = [ nameTokens ]
		try:
			return cls.__name2id[nameTokens[0].upper()]
		except (KeyError, IndexError) as e:
			raise AwlSimError("Invalid data type name: " +\
					  nameTokens[0] if len(nameTokens) else "None")

	@classmethod
	def type2name(cls, type):
		#TODO
		try:
			return cls.__id2name[type]
		except KeyError:
			raise AwlSimError("Invalid data type: " +\
					  str(type))

	@classmethod
	def makeByName(cls, nameTokens):
		type = cls.name2type(nameTokens)
		if type == cls.TYPE_ARRAY:
			openIdx = listIndex(nameTokens, "[")
			elipsisIdx = listIndex(nameTokens, "..")
			closeIdx = listIndex(nameTokens, "]")
			ofIdx = listIndex(nameTokens, "OF")
			if len(nameTokens) >= 8 and\
			   openIdx == 1 and elipsisIdx == 3 and\
			   closeIdx == 5 and ofIdx == 6:
				pass#TODO
			else:
				raise AwlSimError("Invalid ARRAY definition")
		else:
			return cls(type = type,
				   width = cls.type2width[type],
				   signed = cls.type2signed[type])

	def __init__(self, type, width, signed,
		     startIndex=None, subType=None):
		self.type = type
		self.width = width
		self.signed = signed
		self.startIndex = startIndex
		self.subType = subType

	def parseImmediate(self, tokens):
		value = None
		if len(tokens) == 9:
			if self.type == self.TYPE_DWORD:
				value, fields = self.tryParseImmediate_ByteArray(
							tokens)
		elif len(tokens) == 5:
			if self.type == self.TYPE_WORD:
				value, fields = self.tryParseImmediate_ByteArray(
							tokens)
		elif len(tokens) == 1:
			if self.type == self.TYPE_BOOL:
				value = self.tryParseImmediate_BOOL(
						tokens[0])
			elif self.type == self.TYPE_BYTE:
				value = self.tryParseImmediate_HexByte(
						tokens[0])
			elif self.type == self.TYPE_WORD:
				value = self.tryParseImmediate_Bin(
						tokens[0])
				if value is None:
					value = self.tryParseImmediate_HexWord(
							tokens[0])
				if value is None:
					value = self.tryParseImmediate_BCD(
							tokens[0])
			elif self.type == self.TYPE_DWORD:
				value = self.tryParseImmediate_Bin(
						tokens[0])
				if value is None:
					value = self.tryParseImmediate_HexDWord(
							tokens[0])
			elif self.type == self.TYPE_INT:
				value = self.tryParseImmediate_INT(
						tokens[0])
			elif self.type == self.TYPE_DINT:
				value = self.tryParseImmediate_DINT(
						tokens[0])
			elif self.type == self.TYPE_REAL:
				value = self.tryParseImmediate_REAL(
						tokens[0])
			elif self.type == self.TYPE_S5T:
				value = self.tryParseImmediate_S5T(
						tokens[0])
			elif self.type == self.TYPE_TIME:
				value = self.tryParseImmediate_TIME(
						tokens[0])
			elif self.type == self.TYPE_DATE:
				pass#TODO
			elif self.type == self.TYPE_TOD:
				pass#TODO
			elif self.type == self.TYPE_CHAR:
				pass#TODO
		if value is None:
			raise AwlSimError("Immediate value '%s' does "
				"not match data type '%s'" %\
				("".join(tokens), self.type2name(self.type)))
		return value

	def __repr__(self):
		return self.type2name(self.type)

	@classmethod
	def tryParseImmediate_BOOL(cls, token):
		token = token.upper().strip()
		if token == "TRUE":
			return 1
		elif token == "FALSE":
			return 0
		return None

	@classmethod
	def tryParseImmediate_INT(cls, token):
		try:
			immediate = int(token, 10)
			if immediate > 32767 or immediate < -32768:
				raise AwlSimError("16-bit immediate overflow")
		except ValueError:
			return None
		return immediate

	@classmethod
	def tryParseImmediate_DINT(cls, token):
		token = token.upper()
		if not token.startswith("L#"):
			return None
		try:
			immediate = int(token[2:], 10)
			if immediate > 2147483647 or\
			   immediate < -2147483648:
				raise AwlSimError("32-bit immediate overflow")
			immediate &= 0xFFFFFFFF
		except ValueError as e:
			raise AwlSimError("Invalid immediate")
		return immediate

	@classmethod
	def tryParseImmediate_BCD_word(cls, token):
		token = token.upper()
		if not token.startswith("C#"):
			return None
		try:
			cnt = token[2:]
			if len(cnt) < 1 or len(cnt) > 3:
				raise ValueError
			a, b, c = 0, 0, 0
			if cnt:
				a = int(cnt[-1], 10)
				cnt = cnt[:-1]
			if cnt:
				b = int(cnt[-1], 10)
				cnt = cnt[:-1]
			if cnt:
				c = int(cnt[-1], 10)
				cnt = cnt[:-1]
			immediate = a | (b << 4) | (c << 8)
		except ValueError as e:
			raise AwlSimError("Invalid C# immediate")
		return immediate

	@classmethod
	def tryParseImmediate_REAL(cls, token):
		try:
			immediate = float(token)
			immediate = pyFloatToDWord(immediate)
		except ValueError:
			return None
		return immediate

	@classmethod
	def __parseGenericTime(cls, token):
		token = token.upper()
		p = token
		seconds = 0.0
		while p:
			if p.endswith("MS"):
				mult = 0.001
				p = p[:-2]
			elif p.endswith("S"):
				mult = 1.0
				p = p[:-1]
			elif p.endswith("M"):
				mult = 60.0
				p = p[:-1]
			elif p.endswith("H"):
				mult = 3600.0
				p = p[:-1]
			elif p.endswith("D"):
				mult = 86400.0
				p = p[:-1]
			else:
				raise AwlSimError("Invalid time")
			if not p:
				raise AwlSimError("Invalid time")
			num = ""
			while p and p[-1] in "0123456789":
				num = p[-1] + num
				p = p[:-1]
			if not num:
				raise AwlSimError("Invalid time")
			num = int(num, 10)
			seconds += num * mult
		return seconds

	@classmethod
	def tryParseImmediate_S5T(cls, token):
		token = token.upper()
		if not token.startswith("S5T#"):
			return None
		seconds = cls.__parseGenericTime(token[4:])
		s5t = Timer.seconds_to_s5t(seconds)
		return s5t

	@classmethod
	def tryParseImmediate_TIME(cls, token):
		token = token.upper()
		if not token.startswith("T#"):
			return None
		seconds = cls.__parseGenericTime(token[2:])
		msec = int(seconds * 1000)
		if msec > 0x7FFFFFFF:
			raise AwlSimError("T# time too big")
		return msec

	@classmethod
	def tryParseImmediate_TOD(cls, token):
		token = token.upper()
		if not token.startswith("TOD#"):
			return None
		raise AwlSimError("TOD# not implemented, yet")#TODO

	@classmethod
	def tryParseImmediate_Date(cls, token):
		token = token.upper()
		if not token.startswith("D#"):
			return None
		raise AwlSimError("D# not implemented, yet")#TODO

	@classmethod
	def tryParseImmediate_Bin(cls, token):
		token = token.upper()
		if not token.startswith("2#"):
			return None
		try:
			string = token[2:].replace('_', '')
			immediate = int(string, 2)
			if immediate > 0xFFFFFFFF:
				raise ValueError
		except ValueError as e:
			raise AwlSimError("Invalid immediate")
		return immediate

	@classmethod
	def tryParseImmediate_ByteArray(cls, tokens):
		tokens = [ t.upper() for t in tokens ]
		if not tokens[0].startswith("B#("):
			return None, None
		try:
			if len(tokens) >= 5 and\
			   tokens[2] == ',' and\
			   tokens[4] == ')':
				fields = 5
				a, b = int(tokens[1], 10),\
				       int(tokens[3], 10)
				if a < 0 or a > 0xFF or\
				   b < 0 or b > 0xFF:
					raise ValueError
				immediate = (a << 8) | b
			elif len(tokens) >= 9 and\
			     tokens[2] == ',' and\
			     tokens[4] == ',' and\
			     tokens[6] == ',' and\
			     tokens[8] == ')':
				fields = 9
				a, b, c, d = int(tokens[1], 10),\
					     int(tokens[3], 10),\
					     int(tokens[5], 10),\
					     int(tokens[7], 10)
				if a < 0 or a > 0xFF or\
				   b < 0 or b > 0xFF or\
				   c < 0 or c > 0xFF or\
				   d < 0 or d > 0xFF:
					raise ValueError
				immediate = (a << 24) | (b << 16) |\
					    (c << 8) | d
			else:
				raise ValueError
		except ValueError as e:
			raise AwlSimError("Invalid immediate")
		return immediate, fields

	@classmethod
	def tryParseImmediate_HexByte(cls, token):
		token = token.upper()
		if not token.startswith("B#16#"):
			return None
		try:
			immediate = int(token[5:], 16)
			if immediate > 0xFF:
				raise ValueError
		except ValueError as e:
			raise AwlSimError("Invalid immediate")
		return immediate

	@classmethod
	def tryParseImmediate_HexWord(cls, token):
		token = token.upper()
		if not token.startswith("W#16#"):
			return None
		try:
			immediate = int(token[5:], 16)
			if immediate > 0xFFFF:
				raise ValueError
		except ValueError as e:
			raise AwlSimError("Invalid immediate")
		return immediate

	@classmethod
	def tryParseImmediate_HexDWord(cls, token):
		token = token.upper()
		if not token.startswith("DW#16#"):
			return None
		try:
			immediate = int(token[6:], 16)
			if immediate > 0xFFFFFFFF:
				raise ValueError
		except ValueError as e:
			raise AwlSimError("Invalid immediate")
		return immediate

class GenericInteger(object):
	def __init__(self, value, width):
		assert(width > 0 and width <= 32)
		self.value = value
		self.mask = ((1 << width) - 1) & 0xFFFFFFFF

	def set(self, value):
		self.value = value & self.mask

	def setByte(self, value):
		self.value = ((self.value & 0xFFFFFF00) |\
			      (value & 0xFF)) &\
			     self.mask

	def setWord(self, value):
		self.value = ((self.value & 0xFFFF0000) |\
			      (value & 0xFFFF)) &\
			     self.mask

	def setDWord(self, value):
		self.value = value & 0xFFFFFFFF & self.mask

	def setPyFloat(self, pyfl):
		self.value = pyFloatToDWord(pyfl)

	def get(self):
		return self.value

	def getByte(self):
		return self.value & 0xFF

	def getWord(self):
		return self.value & 0xFFFF

	def getDWord(self):
		return self.value & 0xFFFFFFFF

	def getSignedByte(self):
		return byteToSignedPyInt(self.value)

	def getSignedWord(self):
		return wordToSignedPyInt(self.value)

	def getSignedDWord(self):
		return dwordToSignedPyInt(self.value)

	def getPyFloat(self):
		return dwordToPyFloat(self.value)

	def setBit(self, bitNumber):
		self.value = (self.value | (1 << bitNumber)) & self.mask

	def clearBit(self, bitNumber):
		self.value &= ~(1 << bitNumber)

	def setBitValue(self, bitNumber, value):
		if value:
			self.setBit(bitNumber)
		else:
			self.clearBit(bitNumber)

	def getBit(self, bitNumber):
		return 1 if (self.value & (1 << bitNumber)) else 0

	def toHex(self):
		if self.mask == 0xFF:
			return "%02X" % self.value
		elif self.mask == 0xFFFF:
			return "%04X" % self.value
		elif self.mask == 0xFFFFFFFF:
			return "%08X" % self.value
		else:
			assert(0)

class GenericByte(GenericInteger):
	def __init__(self, value=0):
		GenericInteger.__init__(self, value, 8)

class GenericWord(GenericInteger):
	def __init__(self, value=0):
		GenericInteger.__init__(self, value, 16)

class GenericDWord(GenericInteger):
	def __init__(self, value=0):
		GenericInteger.__init__(self, value, 32)

class FlagByte(GenericByte):
	"Flag byte"

	def __init__(self):
		GenericByte.__init__(self)

class InputByte(GenericByte):
	"PAE byte"

	def __init__(self):
		GenericByte.__init__(self)

class OutputByte(GenericByte):
	"PAA byte"

	def __init__(self):
		GenericByte.__init__(self)

class LocalByte(GenericByte):
	"L byte"

	def __init__(self):
		GenericByte.__init__(self)

class Accu(GenericDWord):
	"Accumulator register"

	def __init__(self):
		GenericDWord.__init__(self)

class Adressregister(GenericDWord):
	"Address register"

	def __init__(self):
		GenericDWord.__init__(self)