'''
Created on 21 Jan 2015

@author: Josy
'''

import os

import  myhdl

import hdlutils

# this must be a global declaration
# a Game-Of-Life cell is either
gol_states = myhdl.enum( 'DEAD' , 'ALIVE' )

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

    staten, statep = [myhdl.Signal( gol_states.DEAD ) for _ in range( 2 )]
#     nn, nne, ne, nse, ns, nsw, nw, nnw = [myhdl.intbv(0)[1:] for _ in range(8)]
    
    @myhdl.always_comb
    def smcomb():
        # forward the current state to the output
        State.next = statep
        # how many neighbours are ALIVE?
#         if USE_FUNCTIONS :
        sumneighbours = ( ( to_integer( NeighbourN ) + to_integer( NeighbourNE ) ) + ( to_integer( NeighbourE ) + to_integer( NeighbourSE ) ) ) \
                      + ( ( to_integer( NeighbourS ) + to_integer( NeighbourSW ) ) + ( to_integer( NeighbourW ) + to_integer( NeighbourNW ) ) )        
# #         elif USE_TERNARY :
#         nn  = 1 if NeighbourN  == gol_states.ALIVE else 0
#         nne = 1 if NeighbourNE == gol_states.ALIVE else 0
#         ne  = 1 if NeighbourE  == gol_states.ALIVE else 0
#         nse = 1 if NeighbourSE == gol_states.ALIVE else 0
#         ns  = 1 if NeighbourS  == gol_states.ALIVE else 0
#         nsw = 1 if NeighbourSW == gol_states.ALIVE else 0
#         nw  = 1 if NeighbourW  == gol_states.ALIVE else 0
#         nnw = 1 if NeighbourNW == gol_states.ALIVE else 0
#         sumneighbours = ( (nn + nne) + (ne + nse)) + ((ns + nsw) + (nw + nnw))

# #         else:
#         # write it all out
#         nn = 0
#         if NeighbourN  == gol_states.ALIVE :
#             nn = 1
#         
#         nne = 0
#         if NeighbourNE  == gol_states.ALIVE :
#             nne = 1
#         
#         ne = 0
#         if NeighbourE  == gol_states.ALIVE :
#             ne = 1
#         
#         nse = 0
#         if NeighbourSE  == gol_states.ALIVE :
#             nse = 1
#         
#         ns = 0
#         if NeighbourN  == gol_states.ALIVE :
#             ns = 1
#         
#         nsw = 0
#         if NeighbourSW  == gol_states.ALIVE :
#             nsw = 1
#         
#         nw = 0
#         if NeighbourW  == gol_states.ALIVE :
#             nw = 1
#         
#         nnw = 0
#         if NeighbourNW  == gol_states.ALIVE :
#             nnw = 1
#         
#         sumneighbours = ( (nn + nne) + (ne + nse)) + ((ns + nsw) + (nw + nnw))
                               
                          

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

    @myhdl.always_seq( Clk.posedge, reset = Reset )
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

    lreg = myhdl.Signal(bool(0))

    @myhdl.always_seq(Clk.posedge, reset = Reset)
    def reg():
        if ShiftInOut or Rotate :
            if ShiftInOut:
                lreg.next = SerialIn
            else:
                lreg.next = to_bool(NeighbourN)

    @myhdl.always_comb
    def comb():
        SerialOut.next = lreg
        if Load:
            NeighbourS.next = to_gol_states(lreg)
#             NeighbourS.next = gol_states.ALIVE if lreg else gol_states.DEAD
#             if lreg :
#                 NeighbourS.next = gol_states.ALIVE
#             else :
#                 NeighbourS.next = gol_states.DEAD
        else:
            NeighbourS.next = NeighbourN

    return reg, comb


def pygol( HORIZONTAL , VERTICAL, Clk, Reset,
           ShiftInOut, Load, Rotate, Evolve,
           SerialIn, SerialOut ):
    """ now we build the Game-Of-Life system
        Evolve performs a single evolution step
        ShiftInOut allows to shift out observation data, or to shift in new pattern data
        Load pushes new shifted-in data into the array
        Rotate rotates the array row-wise while loading the shift-register with the top row data
    """

    loadorrotate = myhdl.Signal(bool(0))
    feeders = [None for _ in range(HORIZONTAL)]
    south = [myhdl.Signal( gol_states.DEAD ) for _ in range( HORIZONTAL )]
    serialin = [myhdl.Signal( bool(0) ) for _ in range( HORIZONTAL - 1)]

    @myhdl.always_comb
    def comb():
        #loadorrotate.next = Load or Rotate
        if Load or Rotate:
            loadorrotate.next = 1
        else:
            loadorrotate.next = 0


    if USE_2D:
#         states     = [[myhdl.Signal( gol_states.DEAD ) for _ in range( HORIZONTAL )] for __ in range(VERTICAL)]
        states = myhdl.Array( (VERTICAL, HORIZONTAL), gol_states.DEAD)
        
        cells      = [[None for _ in range(HORIZONTAL)] for __ in range(VERTICAL)]

        feeders[0] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1)][  0], serialin[0], SerialOut, south[0] )
        for i in range(1,HORIZONTAL-1):
            feeders[i] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1)][i], serialin[i], serialin[i-1], south[i] )
        feeders[HORIZONTAL-1] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1)][ HORIZONTAL - 1], SerialIn , serialin[HORIZONTAL-2], south[HORIZONTAL-1] )

        def North(j):
            return (VERTICAL + j + 1) % VERTICAL

        def East(i):
            return (HORIZONTAL + i + 1) % HORIZONTAL

        def South(j):
            return (VERTICAL + j - 1) % VERTICAL

        def West(i):
            return (HORIZONTAL + i - 1) % HORIZONTAL

        for i in range(HORIZONTAL):
            cells[0][i] = CA( Clk, Reset,
                              Evolve, loadorrotate,
                              states[North(0)][i] ,
                              states[North(0)][East(i)] ,
                              states[0][East(i)] ,
                              states[South(0)][East(i)] ,
                              south[i] ,
                              states[South(0)][West(i)] ,
                              states[0][West(i)] ,
                              states[North(0)][West(i)] ,
                              states[0][i]
                            )
        for j in range(1,VERTICAL):
            for i in range(HORIZONTAL):
                cells[j][i] = CA( Clk, Reset,
                                  Evolve, loadorrotate,
                                  states[North(j)][i] ,
                                  states[North(j)][East(i)] ,
                                  states[j][East(i)] ,
                                  states[South(j)][East(i)] ,
                                  states[South(j)][i] ,
                                  states[South(j)][West(i)] ,
                                  states[j][West(i)] ,
                                  states[North(j)][West(i)] ,
                                  states[j][i]
                                )

    else:
        #flatten the 2D arrays to 1D arrays
        states = [myhdl.Signal( gol_states.DEAD ) for _ in range( HORIZONTAL * VERTICAL)]
        cells  = [None for _ in range(HORIZONTAL * VERTICAL)]

        feeders[0] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1) * HORIZONTAL + 0], serialin[0], SerialOut, south[0] )
        for i in range(1,HORIZONTAL-1):
            feeders[i] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1) * HORIZONTAL + i], serialin[i], serialin[i-1], south[i] )
        feeders[HORIZONTAL-1] = feeder(Clk, Reset, ShiftInOut, Load, Rotate, states[(VERTICAL - 1) * HORIZONTAL + HORIZONTAL - 1], SerialIn , serialin[HORIZONTAL-2], south[HORIZONTAL-1] )


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


def tb_pygol():
    Clk = myhdl.Signal( bool( 0 ) )
    Reset = myhdl.ResetSignal( 0, active = 1, async = True )
    ShiftInOut, Load, Rotate, Evolve, SerialIn, SerialOut = [ myhdl.Signal( bool( 0 ) ) for _ in range( 6 ) ]

    dut = pygol( HORIZONTAL , VERTICAL,
                 Clk, Reset,
                 ShiftInOut, Load, Rotate, Evolve,
                 SerialIn, SerialOut )

    tCK = 10
    ClkCount = myhdl.Signal(myhdl.intbv(0)[32:])


    @myhdl.instance
    def clkgen():
        yield hdlutils.genClk(Clk, tCK, ClkCount)

    @myhdl.instance
    def resetgen():
        yield hdlutils.genReset(Clk, tCK, Reset)

    @myhdl.instance
    def stimulusin():
        yield Clk.negedge
        pass

    @myhdl.instance
    def stimulusout():
        yield Clk.negedge
        pass

    @myhdl.instance
    def resultMonitor():
        yield Clk.negedge
        pass

    return dut, clkgen, resetgen, stimulusin, stimulusout, resultMonitor


def convert():

    Clk = myhdl.Signal( bool( 0 ) )
    Reset = myhdl.ResetSignal( 0, active = 1, async = True )
    ShiftInOut, Load, Rotate, Evolve, SerialIn, SerialOut = [ myhdl.Signal( bool( 0 ) ) for _ in range( 6 ) ]

    # Convert
    myhdl.toVHDL( pygol,
            HORIZONTAL , VERTICAL,
            Clk, Reset,
            ShiftInOut, Load, Rotate, Evolve,
            SerialIn, SerialOut )

    myhdl.toVerilog( pygol,
            HORIZONTAL , VERTICAL,
            Clk, Reset,
            ShiftInOut, Load, Rotate, Evolve,
            SerialIn, SerialOut )


if __name__ == '__main__':
    USE_2D = True
#     USE_FUNCTIONS = False
#     USE_TERNARY = False
    HORIZONTAL = 3
    VERTICAL = 3
    print "Running?"
    os.chdir( "./out" )

#     hdlutils.simulate( 3000, tb_pygol )
    convert()
    print "Done!"
