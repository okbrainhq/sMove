#!/usr/bin/python3
"""Current main-board acceptance evidence, using original project rules unchanged."""
from pathlib import Path
import sys,json,subprocess,math,collections,argparse
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import pcbnew as p
from pcb_tools.router import xy,uid,V
from pcb_tools.io import drc,counts,digest
from pcb_tools.render import render

USB={'/USB_DM','/USB_DP','/Compute/USB_DM_MCU','/Compute/USB_DP_MCU'}

def metadata(path):
    b=p.LoadBoard(str(path));footprints={}
    for f in b.GetFootprints():
        footprints[f.GetReference()]={'value':f.GetValue(),'position':xy(f.GetPosition()),'angle':f.GetOrientationDegrees(),'layer':b.GetLayerName(f.GetLayer()),
          'pads':sorted([(a.GetNumber(),a.GetNetname(),xy(a.GetPosition()),xy(a.GetSize())) for a in f.Pads()])}
    usb=sorted([(t.GetNetname(),b.GetLayerName(t.GetLayer()),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth()/1e6) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname() in USB])
    rules=[]
    for z in list(b.Zones())+[z for f in b.GetFootprints() for z in f.Zones()]:
        if not z.GetIsRuleArea():continue
        ps=z.Outline();polys=[]
        for i in range(ps.OutlineCount()):polys.append([xy(ps.COutline(i).CPoint(j)) for j in range(ps.COutline(i).PointCount())])
        rules.append([z.GetZoneName(),[b.GetLayerName(l) for l in z.GetLayerSet().Seq()],z.GetDoNotAllowTracks(),z.GetDoNotAllowVias(),z.GetDoNotAllowCopperPour(),polys])
    edges=sorted([(str(d.GetShape()),xy(d.GetStart()),xy(d.GetEnd())) for d in b.GetDrawings() if d.GetLayer()==p.Edge_Cuts])
    return b,{'footprints':footprints,'usb':usb,'keepouts':rules,'edges':edges}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',default=str(ROOT/'PCB/main/smove-r2-main.kicad_pcb'));ap.add_argument('--baseline');ap.add_argument('--output',default=str(ROOT/'docs/revision-r2/main-routing'));ap.add_argument('--metadata-only',action='store_true');args=ap.parse_args()
    board=Path(args.board);b,meta=metadata(board)
    if args.metadata_only: print(json.dumps(meta));return
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    result={'sha256':digest(board),'drc':counts(drc(board,out/'drc.json',True))}
    assert result['drc']['errors']==0 and result['drc']['unconnected']==0 and result['drc']['parity']==0,result
    if args.baseline:
        # Separate worker: do not load a second PCB into the native SWIG registry.
        raw=subprocess.check_output([sys.executable,__file__,'--board',args.baseline,'--metadata-only'],text=True)
        before=json.loads(raw);after=json.loads(json.dumps(meta))
        changed=[r for r in before['footprints'] if before['footprints'][r]!=after['footprints'][r]]
        assert set(changed)<= {'C7'},changed
        assert before['keepouts']==after['keepouts'] and before['edges']==after['edges']
        assert before['footprints'].keys()==after['footprints'].keys()
        # Verify pin/net identity even for the intentionally rotated C7.
        for ref in before['footprints']:
            assert [(a[0],a[1],a[3]) for a in before['footprints'][ref]['pads']]==[(a[0],a[1],a[3]) for a in after['footprints'][ref]['pads']]
        final_usb={json.dumps(t) for t in after['usb']}
        assert all(json.dumps(t) in final_usb for t in before['usb']), 'A user USB segment was removed or changed'
        result['preservation']={'changed_footprints':changed,'pad_nets_sizes':True,'outline_keepouts':True,'all_user_usb_segments':True,'baseline_sha256':digest(args.baseline)}
    tracks=list(b.GetTracks());segments=[t for t in tracks if not isinstance(t,p.PCB_VIA)]
    assert all(t.GetLayer() in (p.F_Cu,p.B_Cu) for t in segments)
    result['segments_by_layer']=dict(collections.Counter(b.GetLayerName(t.GetLayer()) for t in segments));result['vias']=len(tracks)-len(segments);result['footprints']=len(list(b.GetFootprints()))
    result['planes']=[]
    for z in b.Zones():
        if not z.GetIsRuleArea():result['planes'].append({'name':z.GetZoneName(),'net':z.GetNetname(),'layer':b.GetLayerName(z.GetLayer()),'filled_regions':z.GetFilledPolysList(z.GetLayer()).OutlineCount()})
    gnd=next(z for z in b.Zones() if z.GetLayer()==p.In1_Cu and z.GetNetname()=='GND')
    assert gnd.GetFilledPolysList(p.In1_Cu).OutlineCount()==1,'GND reference split'
    for net in ('/3V3_MAIN','/Power/PACK_P'):
        assert any(z.GetNetname()==net and z.GetLayer()==p.In2_Cu and z.GetFilledPolysList(p.In2_Cu).OutlineCount()==1 for z in b.Zones())
    samples=missing=0
    for t in segments:
        if t.GetNetname() not in USB:continue
        assert t.GetLayer()==p.F_Cu,'USB data must remain top'
        a,z=xy(t.GetStart()),xy(t.GetEnd());n=max(1,math.ceil(math.dist(a,z)/.05))
        for i in range(n+1):
            q=(a[0]+(z[0]-a[0])*i/n,a[1]+(z[1]-a[1])*i/n);samples+=1
            if not gnd.GetFilledPolysList(p.In1_Cu).Contains(V(q)):missing+=1
    result['usb_reference_sampling']={'spacing_mm':.05,'samples':samples,'uncovered':missing,'note':'Centerline coverage, not an impedance/return-current certification'}
    assert missing==0,result['usb_reference_sampling']
    result['length_by_net_mm']={net:round(sum(t.GetLength()/1e6 for t in segments if t.GetNetname()==net),3) for net in sorted({t.GetNetname() for t in segments})}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    for l in b.GetEnabledLayers().CuStack():render(b,out/(b.GetLayerName(l)+'.png'),l)
    render(b,out/'top-tracks.png',fill=False);render(b,out/'bottom-tracks.png',p.B_Cu,fill=False)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
