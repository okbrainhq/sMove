"""Readable obstacle diagnostics for rejected hand-placed segments."""
import pcbnew as p
from .router import V,xy,uid

def conflicts(board,net,a,b,width,layer,clearance=.16):
    shape=p.SHAPE_SEGMENT(V(a),V(b),p.FromMM(width));result=[]
    for f in board.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetname()!=net and pad.IsOnLayer(layer) and p.SHAPE.Collide(shape,pad.GetEffectiveShape(layer),p.FromMM(clearance)):
                result.append({'pad':f.GetReference()+':'+pad.GetNumber(),'net':pad.GetNetname(),'position':xy(pad.GetPosition())})
    for t in board.GetTracks():
        if t.GetNetname()!=net and t.IsOnLayer(layer) and p.SHAPE.Collide(shape,t.GetEffectiveShape(),p.FromMM(clearance)):
            result.append({'uuid':uid(t),'net':t.GetNetname(),'start':xy(t.GetStart()),'end':xy(t.GetEnd())})
    return result
