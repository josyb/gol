# gol 

#### Dabbling with Conway's *Game of Life*

This code came about following a series of blos/threasds on "All Programmable Planet".com (A Xilinx-supported web-site about FPGA, but because of too much diversity was shamelessly taken off the air without leaving an archive. What an arrogance! The moderator 'UBM' is to blame too. Read their apologies over here:<http://www.eetimes.com/author.asp?section_id=36&doc_id=1319869>)  
On the APP site several incarnations were discussed, like MCU, Picoblaze ..., but no real FPGA/HDL stuff. Out of curiosity I coded my own version in VHDL.  
You will notice there is no test-bench, yet. Test-beches in VHDL are a chore, and in this case we would struggle a lot to represent the rectangular array, so I put that off. Now I had been looking at MyHDL and Python for quite some time and it occurred to me that writing a test-bench in Python would be alot more fun and eventually would lead to a graphical display, and that's what one expects from a _Game of Life_-machine?
