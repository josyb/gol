#  This file, hdlutils.py, is a Python utility package for use with MyHDL 
#
#  Copyright (C) 2014-2015 Josy Boelen
#
#  This utility is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 3.0 of the
#  License, or (at your option) any later version.
#
#  This utility is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

'''
Created on 13 Apr 2014

@author: Josy
'''

import math, os, string
from random import randrange
from myhdl import traceSignals, Simulation, Signal, intbv, delay, concat


def widthu( v ):
    if v < 0:
        #using signed numbers requires double
        tv = -v * 2
    else :
        # unsigned
        tv = v

    if tv < 2:
        raise ValueError("Need at least 2")

    return int(math.ceil( math.log( tv, 2 ) ))


def widthr( v ):
    if v < 0:
        #using signed numbers requires double
        tv = -v * 2
    else :
        # unsigned
        tv = v

    if tv < 2:
        raise ValueError("Need at least 2")

    exp = math.ceil( math.log(tv,2) )
    if math.pow(2, exp) == tv :
        exp += 1

    return int(exp)



def tobin( v , i , f = 0):
    bins = []
    for j in range(i+f):
        bit = (v >> (i+f-j-1)) & 1
        bins.append( "%d" % bit )

    if f != 0:
        bins.insert(i, '.')

    return "".join(bins)


def genClk( Clk, tCK , ClkCount = None ):
    """ generate a clock and possible associate a clockcounter with it """
    while True:
        Clk.next = 1
        yield delay( int( tCK / 2 ))
        Clk.next = 0
        if not (ClkCount is None):
            ClkCount.next = ClkCount + 1
        yield delay( int( tCK / 2 ))


def genReset(Clk, tCK, Reset):
    """ although not strictly needed generates an asynchronous Reset with valid deassert"""
    Reset.next = 1
    yield delay( int( tCK * 3.5))
    Reset.next = 0


def waitsig(Clk, tCK, Sig, State = True):
    yield Clk.posedge
    while Sig != State :
        yield Clk.posedge


def pulsesig(Clk, tCK, signal , ACTIVE = 1 , count = 1):
    """ pulse signal """
    signal.next = ACTIVE
    while count:
        yield Clk.posedge
        count = count -1

    yield delay( int( tCK / 4))
    signal.next = not ACTIVE


def simulate(timesteps, mainclass):
    """Runs simulation for MyHDL Class"""
    # Remove old vcd File
    filename = (mainclass.__name__ +".vcd")
    if os.access(filename,  os.F_OK):
        os.unlink(filename)

    # Run Simulation
    tb = traceSignals(mainclass)
    sim = Simulation(tb)
    sim.run(timesteps)




if __name__ == '__main__':
    #testing widthu, widthr
    for i in range(17):
        try:
            print "%d - widthu %d withr %d" %(i, widthu(i), widthr(i))
        except ValueError as e:
            print e
