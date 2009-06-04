#
# Copyright (C) 2009 Niek Linnenbank
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

from SCons.Script import *
import os
import os.path

#
# Allow cross compilation.
#
try:
    cross = os.environ['CROSS']
except:
    cross = ""

#
# Command-line options for the target build chain.
# TODO: -Werror
#
targetVars = Variables()
targetVars.AddVariables(
    ('CC',        'Set the target C compiler to use',   cross + 'gcc'),
    ('CXX',       'Set the target C++ compiler to use', cross + 'g++'),
    ('LINK',      'Set the target linker to use',       cross + 'ld'),
    ('CCFLAGS',   'Change target C compiler flags',
		[ '-O0', '-g3', '-nostdinc', '-Wall', '-fno-builtin' ]),
    ('CXXFLAGS',  'Change target C++ compiler flags',
		[ '-fno-rtti', '-fno-exceptions', '-nostdinc' ]),
    ('CPPFLAGS',  'Change target C preprocessor flags', '-isystem include'),
    ('LINKFLAGS', 'Change the flags for the target linker',
		[ '--whole-archive', '-nostdlib', '-T', 'kernel/arch/x86/user.ld' ])
)

#
# Define the default build environment.
#
target = DefaultEnvironment(CPPPATH   = '.',
		            ENV       = {'PATH' : os.environ['PATH'],
                    	                 'TERM' : os.environ['TERM'],
                        	         'HOME' : os.environ['HOME']},
			    variables = targetVars)
Help(targetVars.GenerateHelpText(target))

#
# Temporary environment for flat binary program files.
#
bintarget = target.Clone()
bintarget.Append(LINKFLAGS = [ '--oformat', 'binary' ])

#
# Command-line options for the host build chain.
# TODO: -Werror
#
hostVars = Variables()
hostVars.AddVariables(
    ('HOSTCC',       'Set the host C compiler to use',   'gcc'),
    ('HOSTCXX',      'Set the host C++ compiler to use', 'g++'),
    ('HOSTCCFLAGS',  'Change host C compiler flags',
		[ '-O0', '-g3', '-Wall' ]),
    ('HOSTCXXFLAGS', 'Change host C++ compiler flags',
		[ '' ]),
    ('HOSTCPPFLAGS',  'Change host C preprocessor flags', '-isystem include -DHOST'),
    ('HOSTLINKFLAGS', 'Change the flags for the host linker',
		[ '-Wl,-whole-archive' ])
)

#
# Build environment for programs on the host system.
#
host = Environment(CPPPATH   = '.',
		   CC        = '$HOSTCC',
		   CXX       = '$HOSTCXX',
		   CCFLAGS   = '$HOSTCCFLAGS',
		   CXXFLAGS  = '$HOSTCXXFLAGS',
		   CPPFLAGS  = '$HOSTCPPFLAGS',
		   LINKFLAGS = '$HOSTLINKFLAGS',
		   variables = hostVars)

host.Append(VARIANT = 'host')
host['LINKCOM'] += ' -Wl,--no-whole-archive'
Help(hostVars.GenerateHelpText(host))

#
# Prepares the given environment, using library and server dependencies.
#
def Prepare(env, libs = [], servers = []):
    
    # First create a safe copy.
    e = env.Clone()

    # Setup variant build directory, if needed.    
    try:
	e.VariantDir(e['VARIANT'], '.')
    except:
	pass
    
    # Loop all required libraries.
    for lib in libs:
        
	# Add them to the C preprocessor include path.
        e['CPPFLAGS'] += ' -isystem lib/' + lib
	e['CPPFLAGS'] += ' -include lib/' + lib + '/Default.h'
	
	# Link against the correct library variant.
	try:
	    e.Append(LIBPATH = [ '#lib/' + lib + '/' + e['VARIANT']])
	except:
	    e.Append(LIBPATH = [ '#lib/' + lib ])

	e.Append(LIBS = [ lib ])

    # Add servers to the system include path.
    for srv in servers:
	e['CPPFLAGS'] += ' -isystem srv/' + srv

    # For IPCServer.h. TODO: put this in libcommon!!!
    if len(servers) > 0:
	e['CPPFLAGS'] += ' -isystem srv'

    return e

#
# Adds a phony target to the given environment.
# Also see: http://www.scons.org/wiki/PhonyTargets
#
def PhonyTargets(env, **kw):

    for target,action in kw.items():
        env.AlwaysBuild(env.Alias(target, [], action))