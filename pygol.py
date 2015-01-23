'''
Created on 21 Jan 2015

@author: Josy
'''

import os
from myhdl import *
import hdlutils
from myhdl._always_seq import always_seq

# this must be a global declaration
# a Game-Of-Life cell is either
gol_states = enum( 'DEAD' , 'ALIVE' )

# we need to count the neighbours
def to_integer( g ):
# MyHDL convert doesn't like these ternary constructs
#     return 1 if g == gol_states.ALIVE else 0
    if g ==  gol_states.ALIVE:
        return 1
    else:
        return 0
    
def to_gol_states( l ):
#     return gol_states.ALIVE if l else gol_states.DEAD
    if l:
        return  gol_states.ALIVE
    else:
        return gol_states.DEAD


def to_bool( g ):
    return g == gol_states.ALIVE



def CA ( Clk, Reset,
        SEvolve, SShift ,
        NeighbourN, NeighbourNE, NeighbourE, NeighbourSE, NeighbourS, NeighbourSW, NeighbourW, NeighbourNW,
        State ):
    """ This is our Cellular Automaton 
        SEvolve performs a single evolution step
        SShift will shift the contents up by one row, to load a new pattern or to rotate the pattern for observation
    """
    
    staten, statep = [Signal( gol_states.DEAD ) for _ in range( 2 )]

    @always_comb
    def smcomb():
        # forward the current state to the output
        State.next = statep
        # how many neighbours are ALIVE?
        sumneighbours = ( ( to_integer( NeighbourN ) + to_integer( NeighbourNE ) ) + ( to_integer( NeighbourE ) + to_integer( NeighbourSE ) ) ) \
                      + ( ( to_integer( NeighbourS ) + to_integer( NeighbourSW ) ) + ( to_integer( NeighbourW ) + to_integer( NeighbourNW ) ) )

        if statep == gol_states.DEAD :
            if sumneighbours == 3 :
                staten.next = gol_states.ALIVE
            else:
                staten.next = gol_states.DEAD
            # ModelSim finds this OK, but Quartus II doesn't
            # staten <= ALIVE when (sum = 3) else DEAD ;
            # analogous Python finds the next OK, but it converts to something VHDL (or is it Quartus?) doesn't like
            # staten.next = gol_states.ALIVE if sumneighbours == 3 else gol_states.DEAD

        elif statep == gol_states.ALIVE:
            if sumneighbours == 2 or sumneighbours == 3 :
                staten.next = gol_states.ALIVE
            else:
                staten.next = gol_states.DEAD

    @always_seq( Clk.posedge, reset = Reset )
    def smreg( ):
        statep.next = staten
        if SShift or SEvolve :
            if SShift:
                statep.next = NeighbourS  ;
            else :
                statep.next = staten ;

    return smcomb, smreg


def feeder(Clk, Reset, ShiftInOut, Load, Rotate, NeighbourN, SerialIn, SerialOut, NeighbourS):
    """ we need  to load/monitor the cells """
    
    lreg = Signal(bool(0))
    
    @always_seq(Clk.posedge, reset = Reset)
    def reg():
        if ShiftInOut or Rotate :
            if ShiftInOut:
                lreg.next = SerialIn
            else:
                lreg.next = to_bool(NeighbourN)
                
    @always_comb
    def comb():
        SerialOut.next = lreg
        if Load:
            NeighbourS.next = to_gol_states(lreg)
        else:
            NeighbourS.next = NeighbourN
    
    return reg, comb


def pygol( HORIZONTAL , VERTICAL, Clk, Reset,
           ShiftInOut, Load, Rotate, Evolve,
           SerialIn, SerialOut ):
    """ now we build the Game-Of-Life system 
        Evolve performs a single evolution step
        ShiftInOut allows shifts out observation data, or shifts in new pater data
        Load pushes new shifted-in data into the array
        Rotate rotates the array row-wise while loading the shift-register with the top row data
    """

#     if USE_2D:    
#         states     = [[Signal( gol_states.DEAD ) for _ in range( HORIZONTAL )] for __ in range(VERTICAL)]
#         cells      = [[None for _ in range(HORIZONTAL)] for __ in range(VERTICAL)]
#         def North(j):
#             return (VERTICAL + j + 1) % VERTICAL
#          
#         def East(i):
#             return (HORIZONTAL + i + 1) % HORIZONTAL
#          
#         def South(j):
#             return (VERTICAL + j - 1) % VERTICAL
#          
#         def West(i):
#             return (HORIZONTAL + i - 1) % HORIZONTAL
#         
#         for j in range(VERTICAL):
#             for i in range(HORIZONTAL):
#                 cells[j][i] = CA( Clk, Reset, 
#                                   Step, ShiftOrRotate,
#                                   states[North(j)][i] ,
#                                   states[North(j)][East(i)] ,
#                                   states[j][East(i)] ,
#                                   states[South(j)][East(i)] ,
#                                   states[South(j)][i] if j != 0 else ( to_gol_states( loadreg(i) ) if LoadnotRotate else states[VERTICAL-1][i]),
#                                   states[South(j)][West(i)] ,
#                                   states[j][West(i)] ,
#                                   states[North(j)][West(i)] ,
#                                   states[j][i]
#                                 ) 
# 
#          
#     else:
    #flatten the 2D arrays to 1D arrays
    states = [Signal( gol_states.DEAD ) for _ in range( HORIZONTAL * VERTICAL)]
    cells  = [None for _ in range(HORIZONTAL * VERTICAL)]
    feeders = [None for _ in range(HORIZONTAL)]
    south = [Signal( gol_states.DEAD ) for _ in range( HORIZONTAL )]
    serialin = [Signal( bool(0) ) for _ in range( HORIZONTAL - 1)]
    loadorrotate = Signal(bool(0)) 
    
    @always_comb
    def comb():
        #loadorrotate.next = Load or Rotate
        if Load or Rotate:
            loadorrotate.next = 1
        else:
            loadorrotate.next = 0
        
    # and compute the indexes 
    def North(j,i):
        return ((VERTICAL + j + 1) % VERTICAL) * HORIZONTAL + i
    
    def NorthEast(j,i):
        return ((VERTICAL + j + 1) % VERTICAL) * HORIZONTAL + (HORIZONTAL + i + 1) % HORIZONTAL
    
    def East(j,i):
        return j * HORIZONTAL + (HORIZONTAL + i + 1) % HORIZONTAL 
    
    def SouthEast(j,i):
        return ((VERTICAL + j - 1) % VERTICAL) * HORIZONTAL + (HORIZONTAL + i + 1) % HORIZONTAL
    
    def South(j,i):
        return ((VERTICAL + j - 1) % VERTICAL) * HORIZONTAL + i
    
    def SouthWest(j,i):
        return ((VERTICAL + j - 1) % VERTICAL) * HORIZONTAL + (HORIZONTAL + i - 1) % HORIZONTAL
    
    def West(j,i):
        return j * HORIZONTAL + (HORIZONTAL + i - 1) % HORIZONTAL 
    
    def NorthWest(j,i):
        return ((VERTICAL + j + 1) % VERTICAL) * HORIZONTAL + (HORIZONTAL + i - 1) % HORIZONTAL

    def Centre(j,i):
        return j * HORIZONTAL + i
    
    feeders[0] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1) * HORIZONTAL + 0], serialin[0], SerialOut, south[0] )   
    for i in range(1,HORIZONTAL-1): 
        feeders[i] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1) * HORIZONTAL + i], serialin[i], serialin[i-1], south[i] )   
    feeders[HORIZONTAL-1] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1) * HORIZONTAL + HORIZONTAL - 1], SerialIn , serialin[HORIZONTAL-2], south[HORIZONTAL-1] )   

    # the bottom row is different as we feed a new pattern from here
    for i in range(HORIZONTAL): 
        cells[i] = CA( Clk, Reset, 
                                            Evolve, loadorrotate,
                                            states[North(0,i)] ,
                                            states[NorthEast(0,i)] ,
                                            states[East(0,i)] ,
                                            states[SouthEast(0,i)] ,
                                            south[i], 
                                            states[SouthWest(0,i)] ,
                                            states[West(0,i)] ,
                                            states[NorthWest(0,i)] ,
                                            states[Centre(0,i)]
                                          ) 
    for j in range(1, VERTICAL):
        for i in range(HORIZONTAL):           
            cells[j * HORIZONTAL + i] = CA( Clk, Reset, 
                                            Evolve, loadorrotate,
                                            states[North(j,i)] ,
                                            states[NorthEast(j,i)] ,
                                            states[East(j,i)] ,
                                            states[SouthEast(j,i)] ,
                                            states[South(j,i)] ,
                                            states[SouthWest(j,i)] ,
                                            states[West(j,i)] ,
                                            states[NorthWest(j,i)] ,
                                            states[Centre(j,i)]
                                          )   
        
    return comb, cells, feeders



def test_pygol():
  
    dut = pygol( HORIZONTAL , VERTICAL, 
                 Clk, Reset,
                 ShiftInOut, Load, Rotate, Evolve,
                 SerialIn, SerialOut )
    
    tCK = 10
    ClkCount = Signal(intbv(0)[32:])
    
    @instance
    def clkgen():
        yield hdlutils.genClk(Clk, tCK, ClkCount)
    
    @instance
    def resetgen():
        yield hdlutils.genReset(Clk, tCK, Reset)
    
    @instance
    def stimulusin():
        yield Clk.negedge
        pass
    
    @instance
    def stimulusout():
        yield Clk.negedge
        pass

    @instance
    def resultMonitor():
        yield Clk.negedge
        pass

    return dut, clkgen, resetgen, stimulusin, stimulusout, resultMonitor


def convert():
#     # force std_logic_vectors instead of unsigned in Interface
#     toVHDL.numeric_ports = False
    # Convert
    toVHDL( pygol, 
            HORIZONTAL , VERTICAL, 
            Clk, Reset,
            ShiftInOut, Load, Rotate, Evolve,
            SerialIn, SerialOut )


if __name__ == '__main__':
    USE_2D = False
    HORIZONTAL = 4
    VERTICAL = 3
    Clk = Signal( bool( 0 ) )
    Reset = ResetSignal( 0, active = 1, async = True )
    ShiftInOut, Load, Rotate, Evolve, SerialIn, SerialOut = [ Signal( bool( 0 ) ) for _ in range( 6 ) ]  
    print "Running?"
    os.chdir( "./out" )
    
#     hdlutils.simulate( 3000, test_pygol )
    convert()

