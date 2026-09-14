"""Apply explicit manual edits from JSON, in an isolated project, without pathfinding.
Usage: python -m pcb_tools.recipe INPUT.kicad_pcb RECIPE.json OUTPUT_DIRECTORY
"""
import sys,json
from dataclasses import replace
from pathlib import Path
import pcbnew as p
from .router import Router,Rules,uid
from .manual import waypoint_plan
from .edit import CopperTransaction
from .io import clone_project,save,drc,counts

def main():
    source,recipe,outdir=sys.argv[1:]
    data=json.loads(Path(recipe).read_text());out=clone_project(source,outdir);b=p.LoadBoard(str(out))
    with CopperTransaction(b) as tx:
        ids=set(data.get('remove_ids',[]));nets=set(data.get('remove_nets',[]))
        known={uid(t) for t in b.GetTracks()}
        if ids-known: raise ValueError(('Unknown copper UUIDs',ids-known))
        tx.remove([t for t in b.GetTracks() if uid(t) in ids or t.GetNetname() in nets])
        for move in data.get('move_footprints',[]):
            f=next(f for f in b.GetFootprints() if f.GetReference()==move['reference'])
            if f.IsLocked(): raise ValueError('Cannot move locked footprint')
            if not ids and not nets: raise ValueError('Moving a footprint requires an explicit copper invalidation list')
            if 'expected_rotation' in move and abs(f.GetOrientationDegrees()-move['expected_rotation'])>1e-6: raise ValueError('Stale footprint orientation')
            f.SetOrientationDegrees(move['rotation'])
            if 'position' in move:
                x,y=move['position'];f.SetPosition(p.VECTOR2I(round(x*1e6),round(y*1e6)))
        for zone in data.get('zones',[]):
            z=p.ZONE(b);z.SetLayer(b.GetLayerID(zone['layer']));z.SetNet(b.FindNet(zone['net']))
            z.SetZoneName(zone['name']);z.SetAssignedPriority(zone.get('priority',2));z.SetLocalClearance(p.FromMM(.15));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(0)
            z.Outline().NewOutline()
            for x,y in zone['points']: z.Outline().Append(round(x*1e6),round(y*1e6))
            b.Add(z)
        summaries=[]
        for route in data['routes']:
            r=Router(b,replace(Rules(),**route.get('rules',{})))
            plan=waypoint_plan(route['net'],route['points'],route.get('width',.2))
            r.apply(plan);summaries.append(plan.summary())
        save(b,out);checks=counts(drc(out,parity=True))
        result={'drc':checks,'removed_uuids':[uid(t) for t in tx.removed],'routes':summaries}
        (out.parent/'recipe-result.json').write_text(json.dumps(result,indent=2)+'\n')
        tx.commit();print(json.dumps(result,indent=2))

if __name__=='__main__':main()
