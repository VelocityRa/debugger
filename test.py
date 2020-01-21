#!/usr/bin/env python
#
# unit tests for debugger

import os
import sys

from struct import unpack

sys.path.append('..')
import debugger.helpers as helpers
import debugger.lldb as lldb
import debugger.DebugAdapter as DebugAdapter

RED = '\x1B[31m'
GREEN = '\x1B[32m'
BROWN = '\x1B[33m'
NORMAL = '\x1B[0m'

# globals
adapter = None

#--------------------------------------------------------------------------
# UTILITIES
#--------------------------------------------------------------------------

def get_file_data(fpath):
	with open(fpath, 'rb') as fp:
		return fp.read()

def get_entry(data):
	# little endian macho
	if data[0:4] == b'\xCF\xFA\xED\xFE':
		assert data[4:8] == b'\x07\x00\x00\x01' # CPU_TYPE_X86_X64
		ncmds = unpack('<I', data[16:20])[0]
		#print('ncmds: %d' % ncmds)
		vmaddr = None
		entryoff = None
		offs = 0x20
		for i in range(ncmds):
			cmd = unpack('<I', data[offs:offs+4])[0]
			cmdsize = unpack('<I', data[offs+4:offs+8])[0]
			if cmd == 0x19: # segment_command_64
				if data[offs+8:offs+16] == b'\x5F\x5F\x54\x45\x58\x54\x00\x00': # __TEXT
					vmaddr = unpack('<Q', data[offs+24:offs+32])[0]
					#print('vmaddr: %X' % vmaddr)
			if cmd == 0x80000028: # entry_point_command
				entryoff = unpack('<I', data[offs+8:offs+12])[0]
				#print('entryoff: %X' % entryoff)
			offs += cmdsize
		if not vmaddr:
			raise Exception('couldn\'t locate segment_command_64 (where __TEXT loads)')
		if entryoff == None:
			raise Exception('couldn\'t locate entry_point_command (where main is)')
		return vmaddr + entryoff

if __name__ == '__main__':
	for fname in ['helloworld', 'helloworld_thread', 'helloworld_loop']:
		fpath = os.path.join('testbins', fname)

		data = get_file_data(fpath)	
		entry = get_entry(data)
		
		print('file %s has entrypoint 0x%X' % (fpath, entry))

		print('launching %s' % fpath)
		adapter = helpers.launch_get_adapter(fpath)
		adapter.breakpoint_set(entry)
		adapter.go()
		assert adapter.reg_read('rip') == entry
		print('quiting')
		adapter.quit()

