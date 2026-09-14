"""One-board-per-process worker avoids native SWIG registry/lifetime conflicts."""
import sys,json
from pathlib import Path
import pcbnew as p
from .router import xy
from .geometry import patterns,length
from .io import save,drc,counts
from .render import render

def main():
    out=Path(sys.argv[1]);ref=sys.argv[2];angle=float(sys.argv[3]);pos=tuple(map(float,sys.argv[4:6]))
    b=p.LoadBoard(str(out));f=next(f for f in b.GetFootprints() if f.GetReference()==ref)
    if f.IsLocked(): raise ValueError('Footprint locked')
    nets={a.GetNetname() for a in f.Pads() if a.GetNetname() and not a.GetNetname().startswith('unconnected-')}
    removed=[t for t in b.GetTracks() if t.GetNetname() in nets]
    if any(t.IsLocked() for t in removed): raise ValueError('Attached copper locked')
    for t in removed: b.Remove(t)
    f.SetOrientationDegrees(angle);f.SetPosition(p.VECTOR2I(round(pos[0]*1e6),round(pos[1]*1e6)))
    score=0.
    for pad in f.Pads():
        peers=[a for g in b.GetFootprints() if g.GetReference()!=ref for a in g.Pads() if pad.GetNetname() in nets and a.GetNetname()==pad.GetNetname() and a.GetNetname()!='GND']
        if peers: score+=min(min(length(q) for q in patterns(xy(pad.GetPosition()),xy(a.GetPosition()))) for a in peers)
    save(b,out);checks=counts(drc(out,parity=True));render(b,out.parent/'top-preview.png',fill=False)
    result=dict(angle=angle,position=pos,approx_connection_length_mm=round(score,3),removed_tracks=len(removed),drc=checks,board=str(out))
    (out.parent/'rotation.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
