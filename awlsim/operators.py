# -*- coding: utf-8 -*-
#
# AWL simulator - operators
# Copyright 2012-2013 Michael Buesch <m@bues.ch>
#
# Licensed under the terms of the GNU General Public License version 2.
#

from awlsim.datatypes import *
from awlsim.statusword import *
from awlsim.util import *


class AwlOperator(object):
	enum.start	# Operator types

	IMM		= enum.item	# Immediate value (constant)
	IMM_REAL	= enum.item	# Real
	IMM_S5T		= enum.item	# S5T immediate
	IMM_TIME	= enum.item	# T# immediate
	IMM_DATE	= enum.item	# D# immediate
	IMM_TOD		= enum.item	# TOD# immediate
	IMM_PTR		= enum.item	# Pointer immediate

	MEM_E		= enum.item	# Input
	MEM_A		= enum.item	# Output
	MEM_M		= enum.item	# Flags
	MEM_L		= enum.item	# Localstack
	MEM_VL		= enum.item	# Parent localstack (indirect access)
	MEM_DB		= enum.item	# Global datablock
	MEM_DI		= enum.item	# Instance datablock
	MEM_T		= enum.item	# Timer
	MEM_Z		= enum.item	# Counter
	MEM_PA		= enum.item	# Peripheral output
	MEM_PE		= enum.item	# Peripheral input

	MEM_STW		= enum.item	# Status word bit read
	MEM_STW_Z	= enum.item	# Status word "==0" read
	MEM_STW_NZ	= enum.item	# Status word "<>0" read
	MEM_STW_POS	= enum.item	# Status word ">0" read
	MEM_STW_NEG	= enum.item	# Status word "<0" read
	MEM_STW_POSZ	= enum.item	# Status word ">=0" read
	MEM_STW_NEGZ	= enum.item	# Status word "<=0" read
	MEM_STW_UO	= enum.item	# Status word "UO" read

	LBL_REF		= enum.item	# Label reference

	BLKREF_FC	= enum.item	# FC reference
	BLKREF_SFC	= enum.item	# SFC reference
	BLKREF_FB	= enum.item	# FB reference
	BLKREF_SFB	= enum.item	# SFB reference
	BLKREF_DB	= enum.item	# DB reference
	BLKREF_DI	= enum.item	# DI reference

	NAMED_LOCAL	= enum.item	# Named local reference (#abc)
	INTERF_DB	= enum.item	# Interface-DB access (translated NAMED_LOCAL)

	INDIRECT	= enum.item	# Indirect access

	# Virtual operators used for debugging of the simulator
	VIRT_ACCU	= enum.item	# Accu
	VIRT_AR		= enum.item	# AR

	enum.end	# Operator types

	def __init__(self, type, width, value):
		self.type = type
		self.width = width
		self.value = value
		self.labelIndex = None
		self.insn = None
		self.setExtended(False)

	def setInsn(self, newInsn):
		self.insn = newInsn

	def setExtended(self, isExtended):
		self.isExtended = isExtended

	def setType(self, newType):
		self.type = newType

	def setOffset(self, newByteOffset, newBitOffset):
		#TODO
		self.value = AwlOffset(newByteOffset, newBitOffset)

	def setWidth(self, newWidth):
		self.width = newWidth

	@property
	def label(self):
		return self.value

	def setLabelIndex(self, newLabelIndex):
		self.labelIndex = newLabelIndex

	def assertType(self, types, lowerLimit=None, upperLimit=None):
		if not isinstance(types, list) and\
		   not isinstance(types, tuple):
			types = [ types, ]
		if not self.type in types:
			raise AwlSimError("Operator type is invalid")
		if lowerLimit is not None:
			if self.value < lowerLimit:
				raise AwlSimError("Operator value too small")
		if upperLimit is not None:
			if self.value > upperLimit:
				raise AwlSimError("Operator value too big")

	type2str = {
		MEM_STW_Z	: "==0",
                MEM_STW_NZ	: "<>0",
                MEM_STW_POS	: ">0",
                MEM_STW_NEG	: "<0",
                MEM_STW_POSZ	: ">=0",
                MEM_STW_NEGZ	: "<=0",
                MEM_STW_UO	: "UO",
	}

	type2prefix = {
		MEM_E		: "E",
		MEM_A		: "A",
		MEM_M		: "M",
		MEM_L		: "L",
		MEM_T		: "T",
		MEM_Z		: "Z",
	}

	def __repr__(self):
		try:
			return self.type2str[self.type]
		except KeyError as e:
			pass
		if self.type == self.IMM:
			if self.width == 16:
				return str(self.value)
			elif self.width == 32:
				return "L#" + str(self.value)
		if self.type == self.IMM_REAL:
			return str(dwordToPyFloat(self.value))
		elif self.type == self.IMM_S5T:
			return "S5T#" #TODO
		elif self.type == self.IMM_TIME:
			return "T#" #TODO
		elif self.type == self.IMM_DATE:
			return "D#" #TODO
		elif self.type == self.IMM_TOD:
			return "TOD#" #TODO
		elif self.type in (self.MEM_A, self.MEM_E,
				   self.MEM_M, self.MEM_L):
			pfx = self.type2prefix[self.type]
			if self.width == 1:
				return "%s %d.%d" %\
					(pfx, self.value.byteOffset, self.value.bitOffset)
			elif self.width == 8:
				return "%sB %d" % (pfx, self.value.byteOffset)
			elif self.width == 16:
				return "%sW %d" % (pfx, self.value.byteOffset)
			elif self.width == 32:
				return "%sD %d" % (pfx, self.value.byteOffset)
		elif self.type == self.MEM_DB:
			if self.width == 1:
				return "DBX %d.%d" % (self.value.byteOffset, self.value.bitOffset)
			elif self.width == 8:
				return "DBB %d" % self.value.byteOffset
			elif self.width == 16:
				return "DBW %d" % self.value.byteOffset
			elif self.width == 32:
				return "DBD %d" % self.value.byteOffset
		elif self.type == self.MEM_DI:
			if self.width == 1:
				return "DIX %d.%d" % (self.value.byteOffset, self.value.bitOffset)
			elif self.width == 8:
				return "DIB %d" % self.value.byteOffset
			elif self.width == 16:
				return "DIW %d" % self.value.byteOffset
			elif self.width == 32:
				return "DID %d" % self.value.byteOffset
		elif self.type == self.MEM_T:
			return "T %d" % self.value.byteOffset
		elif self.type == self.MEM_Z:
			return "Z %d" % self.value.byteOffset
		elif self.type == self.MEM_PA:
			if self.width == 8:
				return "PAB %d" % self.value.byteOffset
			elif self.width == 16:
				return "PAW %d" % self.value.byteOffset
			elif self.width == 32:
				return "PAD %d" % self.value.byteOffset
		elif self.type == self.MEM_PE:
			if self.width == 8:
				return "PEB %d" % self.value.byteOffset
			elif self.width == 16:
				return "PEW %d" % self.value.byteOffset
			elif self.width == 32:
				return "PED %d" % self.value.byteOffset
		elif self.type == self.MEM_STW:
			return "__STW " + S7StatusWord.nr2name[self.value.bitOffset]
		elif self.type == self.LBL_REF:
			return self.label
		elif self.type == self.BLKREF_FC:
			return "FC %d" % self.value.byteOffset
		elif self.type == self.BLKREF_SFC:
			return "SFC %d" % self.value.byteOffset
		elif self.type == self.BLKREF_FB:
			return "FB %d" % self.value.byteOffset
		elif self.type == self.BLKREF_SFB:
			return "SFB %d" % self.value.byteOffset
		elif self.type == self.BLKREF_DB:
			return "DB %d" % self.value.byteOffset
		elif self.type == self.BLKREF_DI:
			return "DI %d" % self.value.byteOffset
		elif self.type == self.NAMED_LOCAL:
			return "#%s" % self.value
		elif self.type == self.INTERF_DB:
			return "__INTERFACE_DB" #FIXME
		elif self.type == self.VIRT_ACCU:
			return "__ACCU %d" % self.value
		elif self.type == self.VIRT_AR:
			return "__AR %d" % self.value
		assert(0)

	@classmethod
	def fetchFromByteArray(cls, array, operator):
		width, byteOff = operator.width, operator.value.byteOffset
		try:
			if width == 1:
				return array[byteOff].getBit(operator.value.bitOffset)
			elif width == 8:
				return array[byteOff].get()
			elif width == 16:
				return (array[byteOff].get() << 8) |\
				       array[byteOff + 1].get()
			elif width == 32:
				return (array[byteOff].get() << 24) |\
				       (array[byteOff + 1].get() << 16) |\
				       (array[byteOff + 2].get() << 8) |\
				       array[byteOff + 3].get()
		except IndexError as e:
			raise AwlSimError("fetch: Operator offset out of range")
		assert(0)

	@classmethod
	def storeToByteArray(cls, array, operator, value):
		width, byteOff = operator.width, operator.value.byteOffset
		try:
			if width == 1:
				array[byteOff].setBitValue(operator.value.bitOffset, value)
			elif width == 8:
				array[byteOff].set(value)
			elif width == 16:
				array[byteOff].set(value >> 8)
				array[byteOff + 1].set(value)
			elif width == 32:
				array[byteOff].set(value >> 24)
				array[byteOff + 1].set(value >> 16)
				array[byteOff + 2].set(value >> 8)
				array[byteOff + 3].set(value)
			else:
				assert(0)
		except IndexError as e:
			raise AwlSimError("store: Operator offset out of range")

class AwlIndirectOp(AwlOperator):
	"Indirect addressing operand"

	# Address register
	enum.start
	AR_NONE		= enum.item		# No address register
	AR_1		= enum.itemAt(1)	# Use AR1
	AR_2		= enum.itemAt(2)	# Use AR2
	enum.end

	# Pointer area constants
	AREA_SHIFT	= 24
	AREA_MASK	= 0xFF << AREA_SHIFT

	# Pointer area encodings
	enum.start	= 0x80
	AREA_NONE	= 0
	AREA_P		= enum.item << AREA_SHIFT  # Peripheral area
	AREA_E		= enum.item << AREA_SHIFT  # Input
	AREA_A		= enum.item << AREA_SHIFT  # Output
	AREA_M		= enum.item << AREA_SHIFT  # Flags
	AREA_DB		= enum.item << AREA_SHIFT  # Global datablock
	AREA_DI		= enum.item << AREA_SHIFT  # Instance datablock
	AREA_L		= enum.item << AREA_SHIFT  # Localstack
	AREA_VL		= enum.item << AREA_SHIFT  # Parent localstack
	enum.end

	# Convert area code to operator type for fetch operations
	area2optype_fetch = {
		AREA_P		: AwlOperator.MEM_PE,
		AREA_E		: AwlOperator.MEM_E,
		AREA_A		: AwlOperator.MEM_A,
		AREA_M		: AwlOperator.MEM_M,
		AREA_DB		: AwlOperator.MEM_DB,
		AREA_DI		: AwlOperator.MEM_DI,
		AREA_L		: AwlOperator.MEM_L,
		AREA_VL		: AwlOperator.MEM_VL,
	}

	# Convert area code to operator type for store operations
	area2optype_store = {
		AREA_P		: AwlOperator.MEM_PA,
		AREA_E		: AwlOperator.MEM_E,
		AREA_A		: AwlOperator.MEM_A,
		AREA_M		: AwlOperator.MEM_M,
		AREA_DB		: AwlOperator.MEM_DB,
		AREA_DI		: AwlOperator.MEM_DI,
		AREA_L		: AwlOperator.MEM_L,
		AREA_VL		: AwlOperator.MEM_VL,
	}

	def __init__(self, area, width, addressRegister, offsetOper):
		AwlOperator.__init__(self,
				     type = AwlOperator.INDIRECT,
				     width = width,
				     value = None)
		assert(width in (1, 8, 16, 32))
		self.area = area
		self.addressRegister = addressRegister
		self.offsetOper = offsetOper

	# Resolve this indirect operator to a direct operator.
	def resolve(self, cpu, store=True):
		offsetOper = self.offsetOper
		# Construct the pointer
		if self.addressRegister == AwlIndirectOp.AR_NONE:
			# Indirect access
			if self.area == AwlIndirectOp.AREA_NONE:
				raise AwlSimError("Area-spanning access not "
					"possible in indirect access without "
					"address register.")
			if offsetOper.type not in (AwlOperator.MEM_M,
						   AwlOperator.MEM_L,
						   AwlOperator.MEM_DB,
						   AwlOperator.MEM_DI):
				raise AwlSimError("Offset operator in indirect "
					"access is not a valid memory offset.")
			if offsetOper.width != 32:
				raise AwlSimError("Offset operator in indirect "
					"access is not of DWORD width.")
			offsetValue = cpu.fetch(offsetOper)
			pointer = (self.area | (offsetValue & 0x00FFFFFF))
		else:
			# Register-indirect access
			if offsetOper.type != AwlOperator.IMM_PTR:
				raise AwlSimError("Offset operator in "
					"register-indirect access is not a "
					"pointer immediate.")
			offsetValue = cpu.fetch(offsetOper)
			if self.area == AwlIndirectOp.AREA_NONE:
				# Area-spanning access
				pointer = (cpu.getAR(self.addressRegister) +\
					   offsetValue) & 0xFFFFFFFF
			else:
				# Area-internal access
				pointer = ((cpu.getAR(operator.addressRegister) +
					    offsetValue) & 0x00FFFFFF) |\
					  self.area
		# Create a direct operator
		try:
			if store:
				optype = AwlIndirectOp.area2optype_store[
						pointer & AwlIndirectOp.AREA_MASK]
			else:
				optype = AwlIndirectOp.area2optype_fetch[
						pointer & AwlIndirectOp.AREA_MASK]
		except KeyError:
			raise AwlSimError("Invalid area code %02Xh" %\
				((pointer & AwlIndirectOp.AREA_MASK) >>\
				 AwlIndirectOp.AREA_SHIFT))
		return AwlOperator(optype, operator.width,
				   AwlOffset.fromPointerValue(pointer))
