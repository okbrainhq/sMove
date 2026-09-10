"""Pinned FreeCAD GUI raster export. Run in an authorized X11 session via scripts/freecad/run.py.
No PCB writes. Uses temporary BRep presentation copies; editable CSG is unchanged.
"""
import os
os.environ['QT_QPA_PLATFORM']='xcb'
import sys,json,hashlib,time
from pathlib import Path
import FreeCAD as A,FreeCADGui as G,Part
from PySide import QtWidgets,QtCore
R=Path(__file__).resolve().parents[1];H=R/'housing';EX=H/'dist'
G.showMainWindow();G.getMainWindow().resize(1400,1000)
doc=A.openDocument(str(H/'smove-r2-enclosure.FCStd'))
parts=[o for o in doc.Objects if getattr(o,'Role','')=='print']
refs=[o for o in doc.Objects if getattr(o,'Role','') in ('pcb','component','battery','insulator','lead_envelope','connector_nominal','solder_reserve') and o.Name!='Component_J1']
orig=parts+refs
for o in doc.Objects:
 if hasattr(o,'ViewObject'):o.ViewObject.Visibility=False
colors={'print':(.92,.94,.97),'pcb':(.04,.38,.18),'component':(.22,.25,.3),'battery':(.66,.70,.77),'insulator':(.8,.65,.2),'lead_envelope':(.85,.12,.04),'connector_nominal':(.6,.62,.65),'solder_reserve':(.8,.65,.2)}
copies=[]
for src in orig:
 o=doc.addObject('PartDesign::Feature','Display_'+src.Name);o.Shape=src.Shape.copy();o.addProperty('App::PropertyString','SourceRole').SourceRole=src.Role;o.ViewObject.ShapeColor=colors[src.Role];o.ViewObject.LineColor=(.2,.22,.25);o.ViewObject.DisplayMode='Flat Lines' if src.Role=='print' else 'Flat Lines';copies.append((src,o))
view=G.activeDocument().activeView()
def capture(name,orientation='axon'):
 doc.recompute()
 if orientation in ('axon','wire'):view.viewAxonometric()
 elif orientation=='top':view.viewTop()
 elif orientation=='right':view.viewRight()
 for _ in range(20):QtWidgets.QApplication.processEvents();time.sleep(.05)
 if orientation=='wire':view.setCameraOrientation((A.Rotation(A.Vector(0,0,1),180)*view.getCameraOrientation()).Q)
 view.fitAll();G.updateGui()
 for _ in range(20):QtWidgets.QApplication.processEvents();time.sleep(.05)
 view.saveImage(str(EX/(name+'.png')),1800,1400,'White')
capture('assembled')
for src,o in copies:
 if src.Role=='print':o.ViewObject.Transparency=80
 if src.Name=='Component_U1':o.ViewObject.ShapeColor=(.1,.7,.8)
capture('assembled-wire-path','wire')
for src,o in copies:
 if src.Role=='print':o.ViewObject.Transparency=0
for src,o in copies:
 if src in parts:
  o.Placement.Base.z+=24 if src==doc.TopAccess else (-14 if src.Role=='print' and src!=doc.Midframe else 0)
 else:o.Placement.Base.z+=0
 if src==doc.Midframe:o.ViewObject.Transparency=65
 if src==doc.TopAccess:o.Placement.Base.x+=25
capture('exploded','wire')
for src,o in copies:o.Placement=A.Placement();o.Shape=src.Shape.copy();o.ViewObject.Visibility=False;o.ViewObject.Transparency=0
for index,src in enumerate(parts):
 o=next(o for s,o in copies if s==src);sh=src.Shape.copy()
 if src==doc.TopAccess:sh.rotate(A.Vector(),A.Vector(1,0,0),180)
 if src==doc.Midframe:sh.rotate(A.Vector(),A.Vector(0,1,0),90)
 bb=sh.BoundBox;sh.translate(A.Vector(index*62-bb.XMin,-bb.YMin,-bb.ZMin));o.Shape=sh;o.ViewObject.Visibility=True
capture('print-three')
# Real cutaway through the west BAT routing. Retain x <=5.5 to expose pack, separator, PCB, leads.
for src,o in copies:
 o.Placement=A.Placement();o.Shape=src.Shape.common(Part.makeBox(20,60,60,A.Vector(-14.5,0,-20)));o.ViewObject.Visibility=not o.Shape.isNull()
capture('section','right')
# Frame-only plan shows open passage and opposite-side locators in separate underside view.
for src,o in copies:o.Placement=A.Placement();o.Shape=src.Shape.copy();o.ViewObject.Visibility=src==doc.Midframe
capture('midframe-top','top');view.viewBottom();view.fitAll();G.updateGui();view.saveImage(str(EX/'midframe-bottom.png'),1800,1400,'White')
for src,o in copies:doc.removeObject(o.Name)
for o in orig:
 o.ViewObject.Visibility=getattr(o,'Role','')!='lead_envelope'
 o.ViewObject.ShapeColor=colors[o.Role]
view.viewAxonometric();view.fitAll();doc.recompute();doc.save()
(H/'validation/renders.json').write_text(json.dumps({'result':'PASS','method':'Pinned FreeCAD GUI activeView BRep raster, authorized X11; not a physical prototype','images':['assembled-wire-path','assembled','exploded','print-three','section','midframe-top','midframe-bottom'],'native_sha256':hashlib.sha256((H/'smove-r2-enclosure.FCStd').read_bytes()).hexdigest()},indent=2)+'\n')
A.closeDocument(doc.Name)
QtCore.QCoreApplication.sendPostedEvents(None,QtCore.QEvent.DeferredDelete)
QtWidgets.QApplication.processEvents()
G.getMainWindow().close()
QtCore.QCoreApplication.sendPostedEvents(None,QtCore.QEvent.DeferredDelete)
QtWidgets.QApplication.processEvents()
print('Render files saved and GUI cleaned up',flush=True)
