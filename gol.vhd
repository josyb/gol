-- gol.vhd


-- 22-10-2012 jb
-- a start



---------------------------------------------------------------
-- first build a package for later use
library ieee;
	use ieee.std_logic_1164.all;
	use ieee.numeric_std.all ;

package gol_package is
	-- a Game-Of-Life cell is either
	type gol_states is (DEAD , ALIVE) ;

	function to_natural(l : gol_states) return  natural ;
	function to_gol_states( l : std_logic ) return gol_states ;
	function to_std_logic( s : gol_states) return std_logic ;

	--	we will building a 2D array of CA
	type gol_2D is array(natural range <> , natural range <>) of gol_states ;

	-- some utility functions
	function ternary( b : boolean ;  er , ner : std_logic) return std_logic ;
	function ternary( b : boolean ; rt , rf : gol_states ) return gol_states ;

end package gol_package;

package body gol_package is

	function to_natural(l : gol_states) return  natural is
		begin
			if (l = ALIVE) then
				return 1 ;
			else
				return 0 ;
			end if ;
		end function ;


		function to_gol_states( l : std_logic ) return gol_states is
			begin
				if (l = '1') then
					return ALIVE ;
				else
					return DEAD ;
				end if ;
			end function ;

		function to_std_logic( s : gol_states) return std_logic is
			begin
				if (s = ALIVE) then
					return '1' ;
				else
					return '0' ;
				end if ;
			end function ;



		function ternary( b : boolean ;  er , ner : std_logic) return std_logic is
			begin
				if ( b ) then
					return er ;
				else
					return ner ;
				end if ;
			end function ternary ;


		function ternary( b : boolean ; rt , rf : gol_states ) return gol_states is
		begin
			if b then
				return rt ;
			else
				return rf ;
			end if ;
		end function ;

end package body gol_package;




-------------------------------------------------------------------------------------
-- this is our basic Game-Of-Life Cellular Automaton

-- quieten some un-avoidable warnings
-- altera message_off 10720
-- altera message_off 13024 21074


library ieee;
	use ieee.std_logic_1164.all;
	use ieee.numeric_std.all ;

	use work.gol_package.all ;

entity CA is
	port (
		Clk 		: in std_logic ;
		Reset 		: in std_logic ;

		SEvolve		: in std_logic ;
		SShift		: in std_logic ;	-- mutually exclusive with SEvolve

		NeighbourN	: in gol_states ;
		NeighbourNE	: in gol_states ;
		NeighbourE	: in gol_states ;
		NeighbourSE	: in gol_states ;
		NeighbourS	: in gol_states ;
		NeighbourSW	: in gol_states ;
		NeighbourW	: in gol_states ;
		NeighbourNW	: in gol_states ;

		State		: out gol_states 	-- to connect to our neighbours

		);
	end entity CA;



architecture a of CA is

	signal	staten , statep	:	gol_states ;


begin


	-- the CA decision process is common for all 'load/monitor' methods
	process( statep , 	NeighbourN , NeighbourNE , NeighbourE ,
						NeighbourSE , NeighbourS ,
						NeighbourSW , NeighbourW , NeighbourNW
			)
			variable	sum	: natural range 0 to 8 ;
		begin

			sum := 		((to_natural(NeighbourN) + to_natural(NeighbourNE)) + (to_natural(NeighbourE) + to_natural(NeighbourSE)))
					+ 	((to_natural(NeighbourS) + to_natural(NeighbourSW)) + (to_natural(NeighbourW) + to_natural(NeighbourNW)))
					;
			State <= statep  ;
			case statep is
				when DEAD =>
					if (sum = 3) then
						staten <= ALIVE ;
					else
						staten <= DEAD ;
					end if ;
					-- ModelSim finds this OK, but Quartus II doesn't
--					staten <= ALIVE when (sum = 3) else DEAD ;

				when ALIVE =>
					if (sum = 2) or (sum = 3) then
						staten <= ALIVE ;
					else
						staten <= DEAD ;
					end if ;
			end case ;

		end process ;


		-- a single clock process for all
		process (Clk, Reset) is
			begin
				if (Reset = '1') then
					statep <= DEAD ;
				elsif rising_edge(Clk) then
					if (SShift = '1') or (SEvolve = '1') then
						if (SShift = '1') then
							statep <= NeighbourS  ;
						else
							statep <= staten ;
						end if ;
					end if;
				end if ;
			end process ;


end architecture a;





----------------------------------------------------------------------------------------
-- now we build the Game-Of-Life system
library ieee;
	use ieee.std_logic_1164.all;
	use ieee.numeric_std.all ;

	use work.gol_package.all ;


entity gol is
	generic(
		HORIZONTAL      : positive := 16*5 ;
		VERTICAL        : positive := 9*5
		);
	port(
		Clk           : in  std_logic;
		Reset         : in  std_logic;

		ShiftInOut    : in  std_logic;		-- this shifts the initial data into the loading register,
											-- and at the same time shifts the monitoring data out
		LoadnotRotate : in  std_logic;		-- decides whether we load a new set of data or whether we rotate the states through
		ShiftOrRotate : in  std_logic;		-- this will move the states to it selected neighbour
		Step          : in  std_logic;		-- performs one step in the Game-Of-Life
		SerialIn      : in  std_logic;		-- serial input to load the 'initial' states
		SerialOut     : out std_logic		-- serial output to monitor the states
		);
	end entity gol;

architecture a of gol is

	signal states     : gol_2D(VERTICAL - 1 downto 0, HORIZONTAL - 1 downto 0);
	signal loadreg    : std_logic_vector(HORIZONTAL - 1 downto 0);
	signal monitorreg : std_logic_vector(HORIZONTAL - 1 downto 0);


begin

	vert: for j in 0 to VERTICAL - 1 generate
		hor: for i in 0 to HORIZONTAL - 1 generate
			cell : entity work.CA
				port map (
					Clk 		=> Clk,
					Reset 		=> Reset,
					SEvolve 	=> Step,
					SShift 		=> ShiftOrRotate ,

					NeighbourNW => states((VERTICAL + j + 1) mod VERTICAL	, (HORIZONTAL + i - 1) mod HORIZONTAL),
					NeighbourN 	=> states((VERTICAL + j + 1) mod VERTICAL	, i),
					NeighbourNE => states((VERTICAL + j + 1) mod VERTICAL	, (HORIZONTAL + i + 1) mod HORIZONTAL),

					NeighbourSW => states((VERTICAL + j - 1) mod VERTICAL	, (HORIZONTAL + i - 1) mod HORIZONTAL),
					NeighbourS 	=> ternary( j = 0,
											ternary( LoadnotRotate = '0' , states(VERTICAL - 1 , i) , to_gol_states( loadreg(i) ) ),
											states((VERTICAL + j - 1) mod VERTICAL , i)
										  ),
					NeighbourSE => states((VERTICAL + j - 1) mod VERTICAL	, (HORIZONTAL + i + 1) mod HORIZONTAL),

					NeighbourE 	=> states(j									, (HORIZONTAL + i + 1) mod HORIZONTAL),
					NeighbourW 	=> states(j									, (HORIZONTAL + i - 1) mod HORIZONTAL),

					State 		=> states(j	, i)

					) ;
		end generate ;
	end generate ;


	process (Clk, Reset) is
		begin
			if (Reset = '1') then
				monitorreg <= (others => '0' ) ;
				loadreg <= (others => '0') ;

			elsif rising_edge(Clk) then
				if (ShiftOrRotate = '1') or (ShiftInOut = '1') then
					if (ShiftOrRotate = '1') then
						for i in 0 to HORIZONTAL - 1 loop
							monitorreg(i) <= to_std_logic( states(VERTICAL - 1 , i) ) ;
						end loop ;
					else
						monitorreg <= "0" & monitorreg(HORIZONTAL -1 downto 1) ;
					end if ;
				end if ;

				if (ShiftInOut = '1') then
					loadreg <= SerialIn & loadreg(HORIZONTAL -1 downto 1) ;
				end if ;

			end if;
		end process ;

	SerialOut <= monitorreg(0) ;
end architecture a;




