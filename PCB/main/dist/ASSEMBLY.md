# R2 main assembly pin-reference / rotation guide

Engineering prototype; manufacturing_release=false. Default BOM/CPL fits ALL 47 parts at JLC. JLC fits all board headers; no local SMT option. Gerbers/BOM/pick-and-place are PROTOTYPE ONLY; assembly rotation preview and supplier qualification remain mandatory. External electrical items: PHR-2 cable assembly and qualified protected battery only. No carrier/PH4 is assembled. Local-fitted connectors require a genuine THT footprint ECO before manufacturing; current SMT boards do not accept THT substitutes.

All positions are mm, viewed from TOP/component face, X right/Y up at the native auxiliary/drill origin. Rotation is KiCad CCW footprint angle, not an unverified vendor-library correction. Verify actual pad reference coordinates/nets against JLC preview before any assembly approval. USB uses A1, all others pad 1. No external UART or testpoints. Two board-only M3 NPTH mounting holes excluded from BOM/CPL.

|Ref|MPN|X|Y|CCW deg|Reference pad|Pad X|Pad Y|
|---|---|---:|---:|---:|---|---:|---:|
|C1|CL10A475KO8NNNC|2.75|5.0|0.0|1|1.975|5.0|
|C2|CL21A476MQYNNNE|6.75|8.0|90.0|1|6.75|7.05|
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
|D1|LTST-C19HE1WT|20.0|5.0|0.0|1|19.575|5.725|
|J1|TYPE-C-31-M-12|21.1|18.2|90.0|A1|17.055|14.95|
|J2|S2B-PH-SM4-TB(LF)(SN)|12.5|7.2|0.0|1|11.5|10.05|
|R1|0402WGF5101TCE|15.0|13.5|90.0|1|15.0|12.99|
|R2|0402WGF5101TCE|18.25|12.0|0.0|1|17.74|12.0|
|R3|0402WGF220JTCE|22.25|24.5|0.0|1|21.74|24.5|
|R4|0402WGF220JTCE|23.0|26.25|90.0|1|23.0|25.74|
|R5|0402WGF1003TCE|13.0|13.5|0.0|1|12.49|13.5|
|R7|0402WGF1002TCE|2.75|13.75|90.0|1|2.75|13.24|
|R8|0402WGF1002TCE|21.75|26.25|90.0|1|21.75|25.74|
|R9|0402WGF1002TCE|23.0|28.5|90.0|1|23.0|27.99|
|R10|0402WGF1002TCE|8.5|20.5|90.0|1|8.5|19.99|
|R11|0402WGF1001TCE|18.75|7.5|90.0|1|18.75|6.99|
|R12|0402WGF1001TCE|18.25|4.25|90.0|1|18.25|3.74|
|R13|0402WGF1001TCE|17.75|10.0|90.0|1|17.75|9.49|
|R14|0402WGF1003TCE|8.5|22.25|0.0|1|7.99|22.25|
|R15|0402WGF1003TCE|10.75|22.25|90.0|1|10.75|21.74|
|R16|0402WGF4701TCE|4.75|10.5|0.0|1|4.24|10.5|
|R17|0402WGF4701TCE|7.25|11.0|90.0|1|7.25|10.49|
|R18|0402WGF4701TCE|8.0|18.5|0.0|1|7.49|18.5|
|R19|0402WGF4701TCE|13.25|14.75|0.0|1|12.74|14.75|
|R20|0402WGF2003TCE|1.5|13.0|90.0|1|1.5|12.49|
|R21|0402WGF8201TCE|3.0|11.0|90.0|1|3.0|10.49|
|R22|0402WGF4701TCE|5.75|5.5|180.0|1|6.26|5.5|
|R23|0402WGF1002TCE|1.25|10.5|0.0|1|0.74|10.5|
|SW2|TS-1088-AR02016|21.5|9.8|90.0|1|21.5|7.575|
|SW3|TS-1088-AR02016|3.6|-0.3|90.0|1|3.6|-2.525|
|U1|ESP32-C3-MINI-1-N4|14.2|32.1|0.0|1|8.3|33.4|
|U2|ICM-20948|12.5|17.5|270.0|1|13.5|19.0|
|U3|PCA9306DCUR|5.25|13.5|270.0|1|6.0|15.05|
|U4|AP2112K-3.3TRG1|3.0|23.75|0.0|1|1.8625|24.7|
|U5|AP2112K-1.8TRG1|3.0|18.75|270.0|1|3.95|19.8875|
|U6|BQ24074RGTR|2.75|8.0|0.0|1|1.35|8.75|
|U8|USBLC6-2SC6|13.5|21.5|0.0|1|12.3625|22.45|
|U9|PESD5V0S2BT,215|8.5|14.5|90.0|1|7.55|13.5625|
