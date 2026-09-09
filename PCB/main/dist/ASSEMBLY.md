# R2 main assembly pin-reference / rotation guide

Engineering prototype; manufacturing_release=false. BOM/CPL fits 46 electronic parts. J2 is two PCB-only plated wire holes on 2.54mm centre pitch, NOT a JST/header and excluded from BOM/CPL. No battery connector or mating cable is purchased. Hand-solder qualified battery leads only after verifying polarity and pack charge/discharge suitability; fit the housing lacing restraint before closing.

J2 holes: 1.0mm finished target (accept 0.9–1.1mm), 2.0mm pads. Wire envelope assumption: tinned bundle <=0.7mm, insulated OD <=1.2mm; no exact gauge supplied. Insulation stays below PCB; solder TOP and trim top protrusion <=0.6mm. BAT+ = protected PACK_P, BAT- = GND. Never solder directly on a pouch; keep each battery lead individually insulated until its connection is made; isolate the pack for service whenever the pack permits. No USB connected during assembly.

All positions mm, TOP/component face, X right/Y up at native auxiliary/drill origin; KiCad CCW angles, not vendor rotation offsets. Check assembly preview. No external UART or testpoints. One M3 NPTH hole and two copper-free keyed corners are PCB features, excluded from BOM/CPL.

|Ref|MPN|X|Y|CCW deg|Reference pad|Pad X|Pad Y|
|---|---|---:|---:|---:|---|---:|---:|
|C1|CL10A475KO8NNNC|6.5|9.5|0.0|1|5.725|9.5|
|C2|CL21A476MQYNNNE|6.35|6.4|0.0|1|5.4|6.4|
|C3|CL21A226MPQNNNE|2.75|26.75|180.0|1|3.7|26.75|
|C4|CL05B104KO5NNNC|5.75|27.0|180.0|1|6.23|27.0|
|C5|CL10A475KO8NNNC|2.0|15.75|0.0|1|1.225|15.75|
|C6|CL10A475KO8NNNC|5.75|18.75|270.0|1|5.75|19.525|
|C7|CL05B104KO5NNNC|11.25|14.25|270.0|1|11.25|14.73|
|C8|CL05B104KO5NNNC|9.75|19.5|270.0|1|9.75|19.98|
|C9|CL05B104KO5NNNC|9.25|17.25|180.0|1|9.73|17.25|
|C10|CL05A105KA5NQNC|7.25|20.25|90.0|1|7.25|19.77|
|C11|CL05B104KO5NNNC|6.25|22.0|0.0|1|5.77|22.0|
|C13|CL21A476MQYNNNE|6.25|24.5|90.0|1|6.25|23.55|
|D1|LTST-C19HE1WT|15.1|8.7|0.0|1|14.675|9.425|
|J1|TYPE-C-31-M-12|21.1|18.2|90.0|A1|17.055|14.95|
|R1|0402WGF5101TCE|15.0|13.5|90.0|1|15.0|12.99|
|R2|0402WGF5101TCE|16.8|11.7|90.0|1|16.8|11.19|
|R3|0402WGF220JTCE|22.25|24.5|0.0|1|21.74|24.5|
|R4|0402WGF220JTCE|23.0|26.25|90.0|1|23.0|25.74|
|R5|0402WGF1003TCE|13.0|13.5|0.0|1|12.49|13.5|
|R7|0402WGF1002TCE|2.75|13.75|90.0|1|2.75|13.24|
|R8|0402WGF1002TCE|21.75|26.25|90.0|1|21.75|25.74|
|R9|0402WGF1002TCE|23.0|28.5|90.0|1|23.0|27.99|
|R10|0402WGF1002TCE|8.5|20.5|90.0|1|8.5|19.99|
|R11|0402WGF1001TCE|17.35|9.5|90.0|1|17.35|8.99|
|R12|0402WGF1001TCE|17.35|7.3|90.0|1|17.35|6.79|
|R13|0402WGF1001TCE|18.75|11.75|0.0|1|18.24|11.75|
|R14|0402WGF1003TCE|8.5|22.25|0.0|1|7.99|22.25|
|R15|0402WGF1003TCE|10.75|22.25|90.0|1|10.75|21.74|
|R16|0402WGF4701TCE|15.1|6.35|0.0|1|14.59|6.35|
|R17|0402WGF4701TCE|6.7|8.1|0.0|1|6.19|8.1|
|R18|0402WGF4701TCE|8.0|18.5|0.0|1|7.49|18.5|
|R19|0402WGF4701TCE|13.25|14.75|0.0|1|12.74|14.75|
|R20|0402WGF2003TCE|1.5|13.0|90.0|1|1.5|12.49|
|R21|0402WGF8201TCE|1.5|11.0|90.0|1|1.5|10.49|
|R22|0402WGF4701TCE|2.05|5.75|0.0|1|1.54|5.75|
|R23|0402WGF1002TCE|3.25|10.6|0.0|1|2.74|10.6|
|SW2|TS-1088-AR02016|11.0|10.9|0.0|1|8.775|10.9|
|SW3|TS-1088-AR02016|11.0|7.15|0.0|1|8.775|7.15|
|U1|ESP32-C3-MINI-1-N4|14.2|32.1|0.0|1|8.3|33.4|
|U2|ICM-20948|12.5|17.5|270.0|1|13.5|19.0|
|U3|PCA9306DCUR|5.25|13.5|270.0|1|6.0|15.05|
|U4|AP2112K-3.3TRG1|3.0|23.75|0.0|1|1.8625|24.7|
|U5|AP2112K-1.8TRG1|3.0|18.75|270.0|1|3.95|19.8875|
|U6|BQ24074RGTR|2.75|8.15|0.0|1|1.35|8.9|
|U8|USBLC6-2SC6|13.5|21.5|0.0|1|12.3625|22.45|
|U9|PESD5V0S2BT,215|8.5|14.75|90.0|1|7.55|13.8125|
