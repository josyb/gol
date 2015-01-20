create_clock -period 10.000 -name Clk -waveform {0.000 5.000} [get_ports Clk]
derive_clock_uncertainty
set_false_path -from [get_ports {LoadnotRotate Reset SerialIn ShiftInOut ShiftOrRotate Step}] -to *
set_false_path -from * -to [get_ports SerialOut]
