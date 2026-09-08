# External debug interface removed

Latest owner revision removes **ALL TP1–TP14 and J3 UART/service header**, including BOOT/EN probe branches. This supersedes the earlier testpoint map. No external testpoints are populated or exposed in the native PCB or schematic. USB programming, BOOT/RESET buttons and their functional circuits remain. U1 pins30/31 and ICM INT1 are deliberately NC. See [current handoff](README.md) and [intentional net migrations](validation/centered/net-migrations.json).
