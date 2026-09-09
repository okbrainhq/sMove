"""PCB-only review release policy; does not change native geometry or routing."""
def apply(j):
    j['status'] = 'PCB REVIEW ONLY; HOUSING INCOMPATIBLE / UNVALIDATED; NOT RELEASED'
    j['manufacturing_release'] = False
    j['housing_compatibility'] = {
        'status': 'INCOMPATIBLE_UNVALIDATED',
        'reason': 'H1 and BAT wire geometry changed from main 554e4fe. No casing changes imported or validated.',
        'legacy_assumptions': 'Any retained enclosure coordinates, strain-relief paths or retention descriptions are historical, not current assembly instructions.'
    }
    j['mounting']['scheme'] = 'One 3.2mm NPTH M3 local support below IMU; mating hardware, insulation, preload and antirotation NOT RELEASED.'
    j['mounting']['release_blocker'] = 'Prior radius-3.4mm bearing has only 0.042612mm nominal margin to filled copper. This is NOT robust insulation or a tolerance-qualified mounting design. Do not assemble using the old bearing/case.'
    j['mounting']['component_clearance_policy'] = 'Native H1 courtyard and all-layer copper keepout retained; no pressure/contact on U2. Hardware envelope and tolerance stack require separate approval.'
    j['retention_policy'] = {'status': 'UNVALIDATED', 'contacts': 'No approved casing or load-bearing contact scheme in this PCB-only revision.'}
    j['battery_wire']['strain_relief'] = 'REQUIRED BUT UNVALIDATED: design and pull/flex qualify insulated lead strain relief outside RF exclusion. No casing routing imported.'
    j['bottom_envelope']['J2'] = 'PTH leads emerge from body-facing underside; insulation/trim/strain relief and final wire path require assembly validation.'
    return j
