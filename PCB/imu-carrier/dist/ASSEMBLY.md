# R2 imu-carrier assembly pin-reference / rotation guide

Engineering prototype; manufacturing_release=false. JLC fits ALL 14 parts, including the board headers, using BOM.csv + CPL.csv and the unchanged JLC-prototype.zip. No local SMT option. External electrical items: PHR-2/PHR-4 cable assemblies and qualified protected battery only. Local-fitted connectors require a genuine THT footprint ECO before manufacturing; these SMT boards do not accept THT substitutes.

All positions are mm, viewed from TOP/component face, X right/Y up at the native auxiliary/drill origin. Rotation is KiCad CCW footprint angle, not an unverified vendor-library correction. Verify actual pad reference coordinates/nets against JLC preview before any assembly approval. USB uses A1, all others pad 1. Nonfitted debug/locators excluded.

|Ref|MPN|X|Y|CCW deg|Reference pad|Pad X|Pad Y|
|---|---|---:|---:|---:|---|---:|---:|
|C5|CL10A475KO8NNNC|0.95|11.9|90.0|1|0.95|11.125|
|C6|CL10A475KO8NNNC|5.0|14.3|0.0|1|4.225|14.3|
|C7|CL05B104KO5NNNC|12.6|15.0|0.0|1|12.12|15.0|
|C8|CL05B104KO5NNNC|7.6|13.4|0.0|1|7.12|13.4|
|C9|CL05B104KO5NNNC|9.7|13.05|0.0|1|9.22|13.05|
|J5|S4B-PH-SM4-TB(LF)(SN)|9.0|4.9|0.0|1|6.0|7.75|
|R16|0402WGF4701TCE|14.7|13.9|0.0|1|14.19|13.9|
|R17|0402WGF4701TCE|14.7|15.2|0.0|1|14.19|15.2|
|R18|0402WGF4701TCE|8.8|10.6|0.0|1|8.29|10.6|
|R19|0402WGF4701TCE|8.15|11.8|0.0|1|7.64|11.8|
|R20|0402WGF2003TCE|16.4|11.7|90.0|1|16.4|11.19|
|U2|ICM-20948|9.5|16.2|0.0|1|8.0|17.2|
|U3|PCA9306DCUR|12.9|11.7|0.0|1|11.35|12.45|
|U5|AP2112K-1.8TRG1|3.8|11.7|0.0|1|2.6625|12.65|
