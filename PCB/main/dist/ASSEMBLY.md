# R2 main assembly pin-reference / rotation guide

Engineering prototype; manufacturing_release=false. JLC fits ALL 35 parts, including the board headers, using BOM.csv + CPL.csv and the unchanged JLC-prototype.zip. No local SMT option. External electrical items: PHR-2/PHR-4 cable assemblies and qualified protected battery only. Local-fitted connectors require a genuine THT footprint ECO before manufacturing; these SMT boards do not accept THT substitutes.

All positions are mm, viewed from TOP/component face, X right/Y up at the native auxiliary/drill origin. Rotation is KiCad CCW footprint angle, not an unverified vendor-library correction. Verify actual pad reference coordinates/nets against JLC preview before any assembly approval. USB uses A1, all others pad 1. Nonfitted debug/locators excluded.

|Ref|MPN|X|Y|CCW deg|Reference pad|Pad X|Pad Y|
|---|---|---:|---:|---:|---|---:|---:|
|C1|CL10A475KO8NNNC|7.8|16.6|0.0|1|7.025|16.6|
|C2|CL21A476MQYNNNE|12.8|16.0|90.0|1|12.8|15.05|
|C3|CL21A226MPQNNNE|2.8|32.0|90.0|1|2.8|31.05|
|C4|CL05B104KO5NNNC|5.0|31.8|90.0|1|5.0|31.32|
|C10|CL05A105KA5NQNC|3.8|20.0|90.0|1|3.8|19.52|
|C11|CL05B104KO5NNNC|6.2|22.6|0.0|1|5.72|22.6|
|C13|CL21A476MQYNNNE|3.2|24.0|0.0|1|2.25|24.0|
|D1|LTST-C19HE1WT|19.15|12.3|0.0|1|18.725|13.025|
|J1|TYPE-C-31-M-12|19.88|3.0|0.0|A1|16.63|7.045|
|J2|S2B-PH-SM4-TB(LF)(SN)|20.1|18.5|90.0|1|17.25|17.5|
|J4|S4B-PH-SM4-TB(LF)(SN)|4.9|9.0|270.0|1|7.75|12.0|
|R1|0402WGF5101TCE|15.4|9.2|0.0|1|14.89|9.2|
|R2|0402WGF5101TCE|18.2|9.2|0.0|1|17.69|9.2|
|R3|0402WGF220JTCE|20.4|26.0|0.0|1|19.89|26.0|
|R4|0402WGF220JTCE|20.4|27.2|0.0|1|19.89|27.2|
|R5|0402WGF1003TCE|12.8|22.6|0.0|1|12.29|22.6|
|R7|0402WGF1002TCE|2.0|20.0|90.0|1|2.0|19.49|
|R8|0402WGF1002TCE|14.4|22.4|90.0|1|14.4|21.89|
|R9|0402WGF1002TCE|1.2|32.0|90.0|1|1.2|31.49|
|R10|0402WGF1002TCE|14.0|20.8|0.0|1|13.49|20.8|
|R11|0402WGF1001TCE|19.8|9.4|90.0|1|19.8|8.89|
|R12|0402WGF1001TCE|13.4|1.6|0.0|1|12.89|1.6|
|R13|0402WGF1001TCE|11.2|1.6|0.0|1|10.69|1.6|
|R14|0402WGF1003TCE|8.2|22.6|0.0|1|7.69|22.6|
|R15|0402WGF1003TCE|10.4|22.6|0.0|1|9.89|22.6|
|R21|0402WGF8201TCE|11.0|20.6|90.0|1|11.0|20.09|
|R22|0402WGF4701TCE|11.0|18.0|270.0|1|11.0|18.51|
|R23|0402WGF1002TCE|4.8|17.6|0.0|1|4.29|17.6|
|SW2|TS-1088-AR02016|12.3|11.3|90.0|1|12.3|9.075|
|SW3|TS-1088-AR02016|12.3|5.0|90.0|1|12.3|2.775|
|U1|ESP32-C3-MINI-1-N4|12.5|32.1|0.0|1|6.6|33.4|
|U4|AP2112K-3.3TRG1|2.8|27.3|0.0|1|1.6625|28.25|
|U6|BQ24074RGTR|8.0|19.9|0.0|1|6.6|20.65|
|U8|USBLC6-2SC6|22.5|10.4|0.0|1|21.3625|11.35|
|U9|PESD5V0S2BT,215|16.2|12.0|90.0|1|15.25|11.0625|
