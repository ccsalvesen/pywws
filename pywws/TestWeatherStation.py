#!/usr/bin/env python

# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Test connection to weather station.

This is a simple utility to test communication with the weather
station. If this doesn't work, then there's a problem that needs to be
sorted out before trying any of the other programs. Likely problems
include not properly installing the USB libraries, or a permissions
problem. The most unlikely problem is that you forgot to connect the
weather station to your computer! ::

%s
"""

__usage__ = """
 usage: python -m pywws.TestWeatherStation [options]
 options are:
       --help           display this help
  -c | --change         display any changes in "fixed block" data
  -d | --decode         display meaningful values instead of raw data
  -h | --history count  display the last "count" readings
  -l | --live           display 'live' data
  -m | --logged         display 'logged' data
  -u | --unknown        display unknown fixed block values
  -v | --verbose        increase amount of reassuring messages
                        (repeat for even more messages e.g. -vvv)
"""

__doc__ %= __usage__

__usage__ = __doc__.split('\n')[0] + __usage__

import datetime
import getopt
import sys
import time

from pywws.Logger import ApplicationLogger
from pywws import WeatherStation

def raw_dump(pos, data):
    print "%04x" % pos,
    for item in data:
        print "%02x" % item,
    print
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(
            argv[1:], "cdh:lmuv",
            ('help', 'change', 'decode', 'history=', 'live', 'logged',
             'unknown', 'verbose'))
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # check arguments
    if len(args) != 0:
        print >>sys.stderr, 'Error: no arguments allowed\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    # process options
    change = False
    history_count = 0
    decode = False
    live = False
    logged = False
    unknown = False
    verbose = 0
    for o, a in opts:
        if o == '--help':
            print __usage__.strip()
            return 0
        elif o in ('-c', '--change'):
            change = True
        elif o in ('-d', '--decode'):
            decode = True
        elif o in ('-h', '--history'):
            history_count = int(a)
        elif o in ('-l', '--live'):
            live = True
            logged = False
        elif o in ('-m', '--logged'):
            live = False
            logged = True
        elif o in ('-u', '--unknown'):
            unknown = True
        elif o in ('-v', '--verbose'):
            verbose += 1
    # do it!
    logger = ApplicationLogger(verbose)
    ws = WeatherStation.weather_station()
    raw_fixed = ws.get_raw_fixed_block()
    if not raw_fixed:
        print "No valid data block found"
        return 3
    if decode:
        # dump entire fixed block
        print ws.get_fixed_block()
        # dump a few selected items
        print "min -> temp_out ->", ws.get_fixed_block(['min', 'temp_out'])
        print "alarm -> hum_out ->", ws.get_fixed_block(['alarm', 'hum_out'])
        print "rel_pressure ->", ws.get_fixed_block(['rel_pressure'])
        print "abs_pressure ->", ws.get_fixed_block(['abs_pressure'])
    else:
        for ptr in range(0x0000, 0x0100, 0x20):
            raw_dump(ptr, raw_fixed[ptr:ptr+0x20])
    if unknown:
        for k in sorted(ws.fixed_format):
            if 'unk' in k:
                print k, ws.get_fixed_block([k])
        for k in sorted(ws.fixed_format):
            if 'settings' in k or 'display' in k or 'alarm' in k:
                bits = ws.get_fixed_block([k])
                for b in sorted(bits):
                    if 'bit' in b:
                        print k, b, bits[b]
    if history_count > 0:
        fixed_block = ws.get_fixed_block()
        print "Recent history"
        ptr = fixed_block['current_pos']
        date = datetime.datetime.now().replace(second=0, microsecond=0)
        for i in range(history_count):
            if decode:
                data = ws.get_data(ptr)
                print date, data
                date = date - datetime.timedelta(minutes=data['delay'])
            else:
                raw_dump(ptr, ws.get_raw_data(ptr))
            ptr = ws.dec_ptr(ptr)
    if change:
        while True:
            new_fixed = ws.get_raw_fixed_block(unbuffered=True)
            for ptr in range(len(new_fixed)):
                if new_fixed[ptr] != raw_fixed[ptr]:
                    print datetime.datetime.now().strftime('%H:%M:%S'),
                    print ' %04x (%d)  %02x -> %02x' % (
                        ptr, ptr, raw_fixed[ptr], new_fixed[ptr])
            raw_fixed = new_fixed
            time.sleep(0.5)
    if live:
        for data, ptr, logged in ws.live_data():
            print "%04x" % ptr,
            print data['idx'].strftime('%H:%M:%S'),
            del data['idx']
            print data
    if logged:
        for data, ptr, logged in ws.live_data(logged_only=True):
            print "%04x" % ptr,
            print data['idx'].strftime('%H:%M:%S'),
            del data['idx']
            print data
    del ws
    return 0
if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
