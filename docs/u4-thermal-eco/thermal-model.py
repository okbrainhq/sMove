#!/usr/bin/python3
"""Conditional lumped thermal estimate, NOT simulation or measured thetaJA.
Run from repository root with pcbnew and Shapely available. JSON to stdout.
"""
import json
import math
import tempfile
import subprocess
from pathlib import Path
import pcbnew as p
from verify import BOARD, BASE, shape, xy, unary_union, LineString

with tempfile.TemporaryDirectory(prefix='smove-u4-model-') as directory:
    path = Path(directory)/BOARD.name
    path.write_bytes(subprocess.check_output(['git','show',f'{BASE}:{BOARD}']))
    board = p.LoadBoard(str(path))
    pad = next(a for f in board.GetFootprints() if f.GetReference()=='U4'
               for a in f.Pads() if a.GetNumber()=='2')
    via = next(t for t in board.GetTracks()
               if t.m_Uuid.AsString()=='84533de4-9e53-4210-9cdf-38a20bf1c6b0')
    track = next(t for t in board.GetTracks()
                 if t.m_Uuid.AsString()=='0bb245a2-c7f7-4480-8fc2-911e0e53d223')
    neck = LineString([xy(track.GetStart()),xy(track.GetEnd())]).difference(
        unary_union([shape(pad,0),shape(via,0)])).length
    width = p.ToMM(track.GetWidth())

# Geometry in the saved board: 35um F.Cu, 0.28mm first dielectric,
# 35um In1.Cu => center-to-center distance 0.315mm to the existing GND plane.
# Material/plating values below are assumptions, not fabricated-board measurements.
k_copper = 390.0
foil_mm = .035
plating_mm = .025
finished_hole_mm = .3
inner_depth_mm = .315
barrel_section_m2 = math.pi*((finished_hole_mm/2+plating_mm)**2-(finished_hole_mm/2)**2)*1e-6
r_neck = neck*1e-3/(k_copper*width*1e-3*foil_mm*1e-3)
r_barrel_inner = inner_depth_mm*1e-3/(k_copper*barrel_section_m2)
r_barrel_bottom = 1e-3/(k_copper*barrel_section_m2)
# Bare-device Pd reference 250mW at Ta25/Tj125 => 400K/W. Treat as an
# unchanged parallel bypass only for this heuristic; it is not thetaJC.
r_bypass = (125-25)/.250
# Retain the review's upper thetaJA as a conditional calibration, NOT a measurement.
r_before = 250.0
r_ground_before = 1/(1/r_before-1/r_bypass)
r_shared = r_ground_before-r_neck-r_barrel_inner
# Eight new vias plus original one. Credit only half their ideal effectiveness;
# ignore two other existing GND vias newly reached by the F.Cu pour.
effective_vias = 4.5
# Broad but obstructed F.Cu spreader: nominal 60K/W access estimate.
# This is about 0.82 squares of 35um copper at k=390, NOT an extracted FEM value.
r_access_after = 60.0

def after_theta(access, n):
    return 1/(1/r_bypass+1/(r_shared+access+r_barrel_inner/n))

r_after = after_theta(r_access_after,effective_vias)
reference = 166.67
geometry = json.loads(Path('docs/u4-thermal-eco/geometry.json').read_text())
result = {
    'status':'Conditional engineering estimate; not measured, not validated FEM, not safety qualification',
    'datasheet_url':'https://media.digikey.com/pdf/Data%20Sheets/Torex/XC6220.pdf',
    'datasheet_page':26,
    'datasheet_reference_thetaJA_C_per_W':reference,
    'reference_board':'40x40mm FR4, 50% copper each face (~800mm2/face), 1.6mm thick, four 0.8mm holes, natural convection',
    'geometry_inputs':{'before_F_Cu_component_mm2':geometry['front_pin2_component_before']['area_mm2'],
                       'after_F_Cu_component_mm2':geometry['front_pin2_component_after']['area_mm2'],
                       'after_attached_bottom_zone_mm2':next(z for z in geometry['zones'] if z['layer']=='B.Cu')['directly_attached_fill_net_mm2'],
                       'neck_centerline_length_outside_pad_and_via_mm':neck,
                       'neck_width_mm':width,'specified_outer_copper_mm':foil_mm,
                       'specified_F_to_In1_center_distance_mm':inner_depth_mm},
    'assumptions':{'copper_conductivity_W_per_m_K':k_copper,'via_wall_plating_mm':plating_mm,
                   'unchanged_parallel_bypass_C_per_W':r_bypass,'baseline_review_calibration_C_per_W':r_before,
                   'after_access_C_per_W':r_access_after,'after_effective_parallel_vias':effective_vias,
                   'bottom_spreader_extra_board_to_air_credit':'zero; conservative omission, shared board/package resistance held fixed'},
    'network_C_per_W':{'old_neck':r_neck,'one_barrel_to_inner_plane':r_barrel_inner,
                       'one_barrel_full_board':r_barrel_bottom,'fitted_shared_ground_path':r_shared,
                       'old_ground_path':r_ground_before,'new_ground_path':r_shared+r_access_after+r_barrel_inner/effective_vias},
    'thetaJA_C_per_W':{'before':r_before,'after':r_after,'delta':r_after-r_before,
                       'before_penalty_above_datasheet_reference':r_before-reference,
                       'after_penalty_above_datasheet_reference':r_after-reference},
    'sensitivity_not_confidence_interval':{'fixed_baseline_250_access_40_to_120_and_effective_vias_2_to_9':
                                         [after_theta(40,9),after_theta(120,2)]},
    'steady_peak_power_projections_before_thermal_protection':[]}
for watts,current in [(.470,.235),(.700,.350)]:
    ambient=40.0
    result['steady_peak_power_projections_before_thermal_protection'].append(
        dict(power_W=watts,Vin_V=5.3,Vout_V=3.3,Iout_A=current,ambient_C=ambient,
             rise_before_C=watts*r_before,rise_after_C=watts*r_after,
             junction_before_C=ambient+watts*r_before,junction_after_C=ambient+watts*r_after,
             delta_junction_C=watts*(r_after-r_before)))
result['warning']='Both stated sustained loads exceed the Tj125 power-rating basis; projections at/above typical TSD150 are not realizable regulated operating points. Actual RF peaks require transient/duty-cycle and enclosure measurements. Ground-pin die thermal coupling is not specified in this datasheet.'
print(json.dumps(result,indent=2))
