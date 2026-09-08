#!/usr/bin/env python3
"""Explicit WHAT-IF budget, not measured currents/cell specifications; no firmware generated."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[3]
active_s=10*30;standby_s=3600-active_s
assert active_s==300 and standby_s==3300
rows=[]
for standby in [5,20,100]:
 active_mah=360*active_s/3600;standby_mah=standby*standby_s/3600
 # Linear regulator: input current approximately output current; no fictitious buck boost efficiency.
 # Other-rail/Q/transient allocations are explicit engineering assumptions, not vendor limits.
 q=(active_mah+standby_mah+1.+1.)*1.30
 rows.append(dict(active_3v3_ma_assumed=360,standby_3v3_ma_assumed=standby,active_mah=active_mah,standby_mah=standby_mah,board_overhead_mah_assumed=1,extra_transition_mah_assumed=1,margin_percent_assumed=30,battery_mah_screen=q,battery_mwh_at_3_7v=q*3.7,passes_hypothetical_120mah_usable=q<=120))
j=dict(status='WHAT_IF_ONLY_NOT_BATTERY_APPROVAL',user_duty=dict(session_max_s=3600,bursts=10,burst_active_s=30,total_espnow_s=300,ble_ready_standby_s=3300,between_sessions='deep sleep or disconnected OFF',session_count_between_charges='unspecified'),candidate=dict(listing_mah=150,listing_body_mm=[30,20,3],protection_and_discharge_and_charge_qualification='UNKNOWN'),rows=rows,idle_formula='Q_between_mAh=measured_board_idle_mA*between_session_hours; add N*Q_session for N sessions',model='Existing linear AP2112 supply; headroom/ESR/capacity at usable voltage unmeasured. 120mAh usable is only 80%-of-listing what-if, not validated. 360mA active is 350mA module TX table +10mA engineering allocation, not guaranteed worst peak.')
(R/'docs/revision-r2/integrated/validation/battery-budget.json').write_text(json.dumps(j,indent=2)+'\n')
print(json.dumps(rows,indent=2))
