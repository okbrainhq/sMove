# Radio/wake architecture and battery PROTOTYPE GATE

## Owner's clarified duty cycle (supersedes earlier ambiguity)

One use/session lasts **at most one hour**: **TEN 30-second ESP-NOW active bursts = 300 seconds**, and up to **3300 seconds (55 minutes) BLE-ready standby**. Between sessions the device may deep-sleep or be disconnected OFF. Number of sessions between charges, time between sessions, command latency, sample rate, TX power and traffic/retry rate are unspecified. This is a hardware architecture/budget document, **not a firmware implementation or a runtime promise**.

## Exact installed MCU and feasible states

Native U1 remains **ESP32-C3-MINI-1-N4**, not a generic ESP32, C6 or S3. The module supports Wi-Fi and BLE with one shared antenna/radio; the current manufacturer table marks N4 NRND. Do not silently substitute N4X: verify stock, chip revision, module assembly and selected ESP-IDF compatibility before procurement. [source](https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf)

| State | Required behavior / transition | Radio availability |
|---|---|---|
| Between sessions: true deep sleep | Stop/deinitialize Wi-Fi and Bluetooth; request ICM/magnetometer low power first; LED off and I2C lines released. Native U4/U5 are always enabled, not load switches. | **No BLE command reception and no BLE deep-sleep wake.** |
| Start session | Existing **SW2 RESET → U1 EN/pin8** restarts the powered module when released. Or configure RTC timer wake beforehand. Current J2 is permanently soldered wire pads, not an unplug connector; any pack isolation/reconnection is a qualified service procedure with USB absent. | Boot into bounded BLE-ready session. |
| Session standby, up to 55min | Proposed connectable advertising + authenticated GATT command, or a maintained low-duty BLE connection. Wi-Fi stopped. Use BLE modem power saving and driver-managed automatic light sleep **only when verified for the actual C3 revision/SDK/clock configuration**. Not continuous scanning by default. | BLE-ready; consumes more than true sleep. Latency depends on advertising/connection intervals and phone behavior. |
| Authorized start-burst command | Acknowledge command, fix ESP-NOW channel/peer policy, start Wi-Fi STA + ESP-NOW. Either suspend BLE for the burst and reconnect afterward, or enable/test software coexistence. | ESP-NOW active for 30s. Don't promise simultaneous lossless BLE/Wi-Fi reception. |
| End of each burst | Flush/ack bounded data, stop ESP-NOW/Wi-Fi, return to BLE-ready state while session remains open. | BLE-ready until next command. |
| Session timeout/end | No more than ten bursts/one-hour window; stop radios and deep-sleep. | Physical RESET/timer required to start again. |
| True OFF | With both USB and J2 pack disconnected, board has no external energy source. Existing board has **no latching master power switch**. Holding RESET only disables MCU; it does not disconnect charger/regulators/IMU. | No remote wake; pack disconnection is a service procedure, not a new external OFF switch. |

C3 manual explicitly distinguishes radios-off deep/manual light sleep from modem sleep plus **automatic** light sleep for maintained BLE. Timer wake and restart by external reset are supported; a generic Bluetooth wake API is not evidence of deep-sleep reception. SW3 BOOT is **GPIO9**, a boot strap/digital GPIO, not one of the C3 RTC GPIO0–5 deep-sleep inputs. Don't repurpose it as a promised deep-sleep wake button. Keep BOOT released on RESET unless downloading; hold BOOT then pulse RESET for the existing ROM service workflow. [source](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/system/sleep_modes.html) [source](https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf)

The C3 coexistence table lists ESP-NOW TX with BLE as supported, and RX with BLE as supported **in STA mode**. The radio is time-shared; enable the matching SDK coexistence option and bench-test retries/latency rather than assuming two simultaneous radios. Sequential BLE-trigger → ESP-NOW burst → BLE standby is the simpler proposed policy. [source](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-guides/coexist.html)

Native IMU bus is U1 GPIO4/SCL (module18), GPIO5/SDA (module19), through the original PCA9306 and pull-ups. ICM INT1 is **NC**, with no testpad, ESP connection or motion wake. FIFO polling is retained. No interrupt translator or substitute sensor was guessed.

## Explicit one-hour WHAT-IF energy screen

Reproduce with `python3 scripts/r2/integrated/budget.py`; [machine-readable assumptions/results](validation/battery-budget.json).

Manufacturer module table lists 350mA for 802.11b TX at 20.5dBm/100% TX duty, 82–84mA RX, and 5uA typical chip deep sleep. These are **not measured board averages, guaranteed system peak limits, or BLE-ready standby current**. The recommended external supply current is at least 0.5A; size/qualify the source, protection and wiring for actual load-step peaks, not just average mAh. [source](https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf)

Conservative planning exercise: hold the 3.3V rail at an **assumed 360mA** for all 300 active seconds (350 + an engineering 10mA peripheral allowance). Three **assumed**, not measured, BLE-ready rail currents show standby sensitivity. Add **1mAh board overhead** (regulator quiescent, charger leakage, divider, IMU/translator state), **1mAh extra transition reserve**, and **30% margin**. These allocations must be replaced by measurements; 360mA is not a guaranteed peak ceiling.

| Assumed BLE-ready rail average | Active charge | Standby charge | Battery charge incl overhead/transition/30% | At 3.7V nominal |
|---:|---:|---:|---:|---:|
| 5mA, optimized low-duty BLE target | 30.00mAh | 4.58mAh | **47.56mAh** | 175.97mWh |
| 20mA, moderate standby | 30.00mAh | 18.33mAh | **65.43mAh** | 242.10mWh |
| 100mA, poorly optimized radio-ready screen | 30.00mAh | 91.67mAh | **160.77mAh** | 594.84mWh |

The actual power chain is **linear**: BQ24074 power path → AP2112 3.3V → AP2112 1.8V branch. Battery current is approximately rail current plus quiescent/parasitic current, **not** a fictional efficient buck conversion. Computing battery energy at its voltage includes linear conversion loss (ideal 3.3/3.7 ≈89% for the 3.3V branch, before quiescent/path loss); do not double-divide the current budget by an efficiency. Near discharge, dropout/path/wire/PCM voltage sag may make much of the labeled capacity unusable. Load-step/rundown/thermal tests determine usable capacity, not this table.

Even assuming **120mAh usable** (an explicitly hypothetical 80% of 150mAh), the first two energy examples fit and the 100mA standby example does not. **This does not qualify the candidate cell.** Ten one-hour sessions were never promised. Use:

```text
Q_total_mAh = N * Q_one_session_mAh + I_board_deep_sleep_mA * hours_between_sessions
E_battery_mWh = integral(V_pack * I_pack * dt_hours)
```

For scale only: 0.2mA measured idle would cost 4.8mAh/day; 1mA would cost 24mAh/day. Neither is a claim about this board. Regulators remain enabled, the ADC divider remains present, and the IMU's actual sleep configuration matters. True disconnection removes board drain, but not cell/PCM self-discharge. N and storage interval remain unspecified.

## Candidate and non-negotiable qualification

Duino.lk **302030 150mAh** listing gives **30×20×3mm**, 3.7V nominal and 4.2V charge; “Available with PCM Protection” is ambiguous/version-dependent. There is **no qualified max discharge, pulse duration, continuous rating, permitted charge current, protection threshold/tolerance or full lead/tab/PCM envelope** in the evidence obtained. No price/stock assurance or generic cutoff is adopted. [source](https://www.duino.lk/product/3-7v-150mah-302030-lipo-battery/)

**Do not connect/charge the candidate on this PCB just because it fits.** Obtain the exact supplier cell/PCM datasheet and protected sample, verify continuous/pulse current at temperature/low SOC, ESR/sag, capacity, polarity, wire/solder-joint current rating and strain relief, overcharge/overdischarge/overcurrent/short protection, and approved charge voltage/current/tolerance. Confirm pouch growth, tabs, PCM and wires inside the uncompressed acceptance envelope. No resistor/charge-current changes were made: **R21=8.2k ISET, R22=4.7k ILIM, R23=10k TS bias remain**. The inherited engineering charge screen was up to **121mA / 4.23V including tolerance**; that is a demand on a qualified pack, NOT permission to charge this 4.2V-listed cell at those limits. **No cell-temperature sensing** exists. Review exact charger limits and real programmed behavior with the supplier before charging.

Safe prototype choices: use a current-limited bench source with USB/charging isolated appropriately and no candidate cell; or use a separately qualified protected pack with approved charge path, accepting a larger external holder/case. A lower charge current or different protection/power topology is a deliberate future ECO only after evidence. Supervised off-body charging only after qualification; never unattended/on-body charging. Thermal, RF/on-body detuning, magnetic current bias, SI/ESD and brownout tests remain open.
