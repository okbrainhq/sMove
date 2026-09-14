#!/usr/bin/python3
"""Render native copper geometry as a review diagram, not fabrication artwork."""
import math
from .router import p, xy
import cairo

def render(b,path,layer=p.F_Cu,box=None,fill=True):
    if box is None:
        bb=b.GetBoardEdgesBoundingBox();box=(bb.GetX()/1e6-.5,bb.GetY()/1e6-.5,bb.GetRight()/1e6+.5,bb.GetBottom()/1e6+.5)
    x0,y0,x1,y1=box;sc=50;w,h=int((x1-x0)*sc),int((y1-y0)*sc)
    su=cairo.ImageSurface(cairo.FORMAT_ARGB32,w,h);c=cairo.Context(su);c.set_source_rgb(.04,.055,.075);c.paint()
    def at(q):return (q[0]-x0)*sc,(q[1]-y0)*sc
    def poly(ps):
        for i in range(ps.OutlineCount()):
            for pp in [ps.COutline(i)]+[ps.CHole(i,j) for j in range(ps.HoleCount(i))]:
                for j in range(pp.PointCount()):(c.move_to if j==0 else c.line_to)(*at(xy(pp.CPoint(j))))
                c.close_path()
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD);c.fill()
    colors={'GND':(.15,.27,.24),'/3V3_MAIN':(.48,.25,.08),'/USB_DP':(1,.2,.55),'/USB_DM':(.2,.85,1),'/Compute/USB_DP_MCU':(1,.4,.65),'/Compute/USB_DM_MCU':(.4,1,1),'/VBUS':(1,.5,.15),'/Power/PACK_P':(.9,.4,.1),'/Power/SYS':(.85,.85,.15)}
    if fill:
        for z in b.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(layer):continue
            c.set_source_rgb(*colors.get(z.GetNetname(),(.3,.3,.4)));poly(z.GetFilledPolysList(layer))
    for t in b.GetTracks():
        if not t.IsOnLayer(layer):continue
        c.set_source_rgb(*colors.get(t.GetNetname(),(.85,.65,.3)))
        if isinstance(t,p.PCB_VIA):
            c.arc(*at(xy(t.GetPosition())),p.ToMM(t.GetWidth(layer))/2*sc,0,2*math.pi);c.fill();c.set_source_rgb(.025,.025,.025);c.arc(*at(xy(t.GetPosition())),p.ToMM(t.GetDrill())/2*sc,0,2*math.pi);c.fill()
        else:c.set_line_width(p.ToMM(t.GetWidth())*sc);c.set_line_cap(cairo.LINE_CAP_ROUND);c.move_to(*at(xy(t.GetStart())));c.line_to(*at(xy(t.GetEnd())));c.stroke()
    for f in b.GetFootprints():
        for a in f.Pads():
            if not a.IsOnLayer(layer):continue
            s=p.SHAPE_POLY_SET();a.TransformShapeToPolygon(s,layer,0,p.FromMM(.005),p.ERROR_INSIDE)
            c.set_source_rgb(*colors.get(a.GetNetname(),(.6,.6,.6)));poly(s)
            if a.GetNumber() and (layer==p.F_Cu):
                c.set_source_rgb(.95,.95,.95);c.set_font_size(8);c.move_to(*at(xy(a.GetPosition())));c.show_text(a.GetNumber())
        c.set_font_size(14);c.set_source_rgb(1,1,1);c.move_to(*at(xy(f.GetPosition())));c.show_text(f.GetReference())
    for d in b.GetDrawings():
        if d.GetLayer()==p.Edge_Cuts:
            c.set_source_rgb(.7,.7,.7);c.set_line_width(1);c.move_to(*at(xy(d.GetStart())));c.line_to(*at(xy(d.GetEnd())));c.stroke()
    for x in range(math.ceil(x0),math.floor(x1)+1):
        c.set_font_size(10);c.set_source_rgb(.6,.65,.7);c.move_to(*at((x,y0+.25)));c.show_text(str(x))
    for y in range(math.ceil(y0),math.floor(y1)+1):
        c.move_to(*at((x0+.05,y)));c.show_text(str(y))
    su.write_to_png(str(path))
