#!/usr/bin/python3
"""Read-only board audit against 43ee2ea; requires pcbnew and Shapely 2.x.
Run from repository root. JSON goes to stdout; no PCB/project file is written.
KiCad copper curves are polygonized outwards with <= 0.001 mm error.
Saved zone contours are used verbatim; drill holes are subtracted explicitly.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
import tempfile

import pcbnew as p
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

BOARD = Path('PCB/main/smove-r2-main.kicad_pcb')
BASE = '43ee2ea'
LAYERS = (p.F_Cu, p.In1_Cu, p.In2_Cu, p.B_Cu)
SEED = Point(110.25, 118.4)
OUTLINE = [(104.5, 117), (113.2, 117), (113.2, 123.2), (104.5, 123.2)]
VIA_POINTS = sorted([(111.7,119.5),(108.6,119.7),(110.2,120.6),(112.1,120.3),
                     (112.9,121.6),(112.1,121.2),(108.5,121.4),(111.4,121.9)])


def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()


def children(s):
    depth = 0
    quoted = escape = False
    start = None
    result = []
    for i, c in enumerate(s):
        if quoted:
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == '"':
                quoted = False
            continue
        if c == '"':
            quoted = True
        elif c == '(':
            depth += 1
            if depth == 2:
                start = i
        elif c == ')':
            if depth == 2:
                result.append(s[start:i+1])
            depth -= 1
    assert depth == 0 and not quoted
    return result


def ident(s):
    match = re.search(r'\(uuid "([^"]+)"\)', s)
    return match.group(1) if match else None


def xy(v):
    return (p.ToMM(v.x), p.ToMM(v.y))


def polygons(ps):
    def ring(r):
        return [xy(r.CPoint(k)) for k in range(r.PointCount())]
    # Saved KiCad hole contours may be fractured into a self-touching outline.
    return [Polygon(ring(ps.COutline(i)),
                    [ring(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]).buffer(0)
            for i in range(ps.OutlineCount())]


def poly(ps):
    return unary_union(polygons(ps))


def shape(it, layer):
    if isinstance(it, p.PCB_VIA):
        return Point(xy(it.GetPosition())).buffer(p.ToMM(it.GetWidth(layer))/2,
                                                quad_segs=256)
    ps = p.SHAPE_POLY_SET()
    it.TransformShapeToPolygon(ps, layer, 0, p.FromMM(.001), p.ERROR_OUTSIDE)
    return poly(ps)


def items(b, layer):
    return ([(t,shape(t,layer)) for t in b.GetTracks() if t.IsOnLayer(layer)] +
            [(a,shape(a,layer)) for f in b.GetFootprints() for a in f.Pads()
             if a.IsOnLayer(layer)])


def drill_shapes(b):
    holes = [Point(xy(t.GetPosition())).buffer(p.ToMM(t.GetDrill())/2, quad_segs=256)
             for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
    for f in b.GetFootprints():
        for a in f.Pads():
            dx, dy = xy(a.GetDrillSize())
            if not dx or not dy:
                continue
            x, y = xy(a.GetPosition())
            angle = math.radians(a.GetOrientationDegrees())
            # Local pad x points clockwise-negative in PCB y-down coordinates.
            vx, vy = (1,0) if dx >= dy else (0,1)
            ex = (vx*math.cos(angle) + vy*math.sin(angle))*abs(dx-dy)/2
            ey = (-vx*math.sin(angle) + vy*math.cos(angle))*abs(dx-dy)/2
            holes.append(LineString([(x-ex,y-ey),(x+ex,y+ey)]).buffer(min(dx,dy)/2,
                                                                                    quad_segs=256))
    return unary_union(holes)


def components(geometry):
    return list(geometry.geoms) if hasattr(geometry, 'geoms') else [geometry]


def counts(b):
    vias = sum(isinstance(t,p.PCB_VIA) for t in b.GetTracks())
    return dict(tracks=len(list(b.GetTracks()))-vias, vias=vias,
                zones=len(list(b.Zones())), footprints=len(list(b.GetFootprints())))


def connected_front(b, layer=p.F_Cu, seed=SEED):
    filled = [poly(z.GetFilledPolysList(layer)) for z in b.Zones()
              if not z.GetIsRuleArea() and z.IsOnLayer(layer)]
    ground = [s for it,s in items(b,layer) if it.GetNetname() == 'GND']
    component = next(c for c in components(unary_union(ground+filled)) if c.covers(seed))
    vias = [dict(uuid=t.m_Uuid.AsString(), xy_mm=xy(t.GetPosition()),
                 diameter_mm=p.ToMM(t.GetWidth(layer)), drill_mm=p.ToMM(t.GetDrill()))
            for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND'
            and component.intersects(shape(t,layer))]
    area = component.difference(drill_shapes(b)).area
    return dict(area_mm2=area, area_before_drill_subtraction_mm2=component.area,
                bounds_mm=list(component.bounds), attached_vias=vias)


def audit(before_text, after_text, before, after):
    old, new = children(before_text), children(after_text)
    oldmap = {ident(s):s for s in old if ident(s)}
    newmap = {ident(s):s for s in new if ident(s)}
    assert oldmap.keys() <= newmap.keys()
    # Stronger than a geometry equality check: every existing object is verbatim.
    for uid, text in oldmap.items():
        assert text == newmap[uid], ('Existing object changed',uid)
    old_non_objects = [s for s in old if not ident(s)]
    new_non_objects = [s for s in new if not ident(s)]
    assert old_non_objects == new_non_objects, 'Board settings/net table changed'
    added = [s for s in new if ident(s) not in oldmap and ident(s)]
    assert Counter(s.split()[0] for s in added) == {'(via':8,'(zone':2}
    assert counts(before) == dict(tracks=426,vias=77,zones=4,footprints=53)
    assert counts(after) == dict(tracks=426,vias=85,zones=6,footprints=53)
    added_ids = {ident(s) for s in added}
    new_vias = sorted([t for t in after.GetTracks() if t.m_Uuid.AsString() in added_ids],
                     key=lambda t:xy(t.GetPosition()))
    assert [xy(t.GetPosition()) for t in new_vias] == VIA_POINTS
    obstacles = [(t,s) for la in LAYERS for t,s in items(before,la)]
    records = []
    for via in new_vias:
        q = Point(xy(via.GetPosition()))
        radius = p.ToMM(via.GetWidth(p.F_Cu))/2
        gap, obj = min(((q.distance(s)-radius,t) for t,s in obstacles), key=lambda x:x[0])
        assert via.GetNetname()=='GND' and via.GetNetCode()==18
        assert p.ToMM(via.GetDrill())==.3 and radius==.3
        assert set(LAYERS) <= set(via.GetLayerSet().Seq())
        assert gap >= .2, ('Via copper clearance',xy(via.GetPosition()),gap)
        records.append(dict(uuid=via.m_Uuid.AsString(), xy_mm=xy(via.GetPosition()),
                            net='GND', net_code=18, diameter_mm=.6, drill_mm=.3,
                            min_existing_copper_gap_mm=gap,
                            nearest_existing_uuid=obj.m_Uuid.AsString()))
    new_pair_gap = min(Point(xy(a.GetPosition())).distance(Point(xy(b.GetPosition())))-.6
                       for i,a in enumerate(new_vias) for b in new_vias[i+1:])
    assert new_pair_gap >= .2
    zones = []
    holes = drill_shapes(after)
    footprint = next(f for f in after.GetFootprints() if f.GetReference()=='U4')
    pad = next(a for a in footprint.Pads() if a.GetNumber()=='2')
    assert pad.GetLocalZoneConnection()==-1  # Inherit solid zone setting.
    ground_pad = shape(pad,p.F_Cu)
    keepout = next(z for z in after.Zones() if z.GetZoneName()=='ANTENNA_ALL_LAYERS')
    keepout_geometry = poly(keepout.Outline())
    before_ground_by_layer = {}
    for la in [p.F_Cu,p.B_Cu]:
        before_copper = unary_union([s for it,s in items(before,la) if it.GetNetname()=='GND'])
        before_ground_by_layer[before.GetLayerName(la)] = before_copper.difference(drill_shapes(before)).intersection(Polygon(OUTLINE)).area
    for z in after.Zones():
        if z.m_Uuid.AsString() not in added_ids:
            continue
        layer = z.GetLayer()
        outline = poly(z.Outline())
        assert outline.equals(Polygon(OUTLINE))
        assert z.GetNetname()=='GND' and z.GetPadConnection()==p.ZONE_CONNECTION_FULL
        assert p.ToMM(z.GetLocalClearance())==.21
        raw = poly(z.GetFilledPolysList(layer))
        pcs = components(raw)
        attached = next(c for c in pcs if c.covers(SEED))
        foreign = unary_union([s for it,s in items(after,layer) if it.GetNetname()!='GND'])
        gap = raw.distance(foreign)
        assert gap >= .2, ('Zone foreign copper clearance',layer,gap)
        assert outline.distance(keepout_geometry)>=17
        if layer==p.F_Cu:
            assert attached.intersection(ground_pad).area>.5
            assert attached.difference(holes).area>=25
        # Each new via is on the directly attached top component and bottom fill.
        for v in new_vias:
            assert attached.covers(Point(xy(v.GetPosition())))
        zones.append(dict(uuid=z.m_Uuid.AsString(), name=z.GetZoneName(),
                          layer=after.GetLayerName(layer),outline_mm=OUTLINE,
                          gross_polygon_area_mm2=outline.area,
                          all_filled_area_mm2=raw.area,
                          clearance_and_unfilled_cutouts_mm2=outline.area-raw.area,
                          excluded_other_components_mm2=raw.area-attached.area,
                          directly_attached_fill_before_drills_mm2=attached.area,
                          drill_cutouts_attached_mm2=attached.intersection(holes).area,
                          directly_attached_fill_net_mm2=attached.difference(holes).area,
                          all_fill_net_mm2=raw.difference(holes).area,
                          min_foreign_copper_gap_mm=gap,
                          antenna_keepout_distance_mm=outline.distance(keepout_geometry),
                          solid_connection=True))
    # Locate and hash the C11 direct route and its via, not just its endpoints.
    c11_ids=['d8e59a01-d4bc-4fee-9aa6-d1b957c9a084','772e4247-d55b-4c14-9ccd-2492ecce88d9']
    c11_via = next(t for t in before.GetTracks() if isinstance(t,p.PCB_VIA)
                   and Point(xy(t.GetPosition())).distance(Point(113.987486,115.94))<.001)
    c11_ids.append(c11_via.m_Uuid.AsString())
    c11_route = [dict(uuid=u,sha256_before=digest(oldmap[u]),sha256_after=digest(newmap[u]),
                      sexpr=oldmap[u]) for u in c11_ids]
    plane = next(z for z in before.Zones() if not z.GetIsRuleArea())
    plane_geom = poly(plane.GetFilledPolysList(p.In1_Cu))
    return dict(baseline=BASE,board=str(BOARD),board_sha256_before=digest(before_text),
                board_sha256_after=digest(after_text),kicad_version=p.GetBuildVersion(),
                counts_before=counts(before),counts_after=counts(after),
                existing_uuid_objects_byte_identical=len(oldmap),
                existing_objects_sha256_before=digest('\n'.join(oldmap[u] for u in sorted(oldmap))),
                existing_objects_sha256_after=digest('\n'.join(newmap[u] for u in sorted(oldmap))),
                all_existing_zones_including_fills_byte_identical=True,
                all_other_net_geometry_byte_identical=True,
                all_footprints_byte_identical=True,settings_net_table_unchanged=True,
                added_vias=records,min_new_via_pair_gap_mm=new_pair_gap,zones=zones,
                front_pin2_component_before=connected_front(before),
                front_pin2_component_after=connected_front(after),
                bottom_original_via_component_before=connected_front(before,p.B_Cu,Point(110.3,119.7)),
                bottom_original_via_component_after=connected_front(after,p.B_Cu,Point(110.3,119.7)),
                baseline_local_rectangle_ground_net_area_mm2=before_ground_by_layer,
                unchanged_inner_ground_plane_filled_area_mm2=plane_geom.area,
                c11_direct_ground_route=c11_route,
                curve_polygonization_max_error_mm=.001,
                note='Areas are geometric, not thermally effective areas. Drills: 1024-gon circles; reported areas rounded in README. Full before/after F.Cu components are same-layer unions; other F.Cu zone components are not counted towards the directly attached >=25 mm2 requirement.')


def main():
    text = subprocess.check_output(['git','show',f'{BASE}:{BOARD}'],text=True)
    with tempfile.TemporaryDirectory(prefix='smove-u4-verify-') as directory:
        baseline = Path(directory)/BOARD.name
        baseline.write_text(text)
        before = p.LoadBoard(str(baseline))
        after = p.LoadBoard(str(BOARD))
        print(json.dumps(audit(text,BOARD.read_text(),before,after),indent=2))


if __name__=='__main__':
    main()
