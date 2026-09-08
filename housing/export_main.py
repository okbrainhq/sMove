"""Refresh the conservative populated-board STEP from current fixed engineering sources.
Frame: same main-local XY as housing, PCB bottom Z=0. Not a vendor-accurate assembly.
"""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
R=Path(__file__).resolve().parents[1]
def export(doc):
 sources=[o for o in doc.Objects if getattr(o,'Role','') in ('main_pcb','main_component','tail')]
 tmp=A.newDocument('MainEnvelopeExport');objs=[]
 for src in sources:
  o=tmp.addObject('Part::Feature',src.Name);o.Shape=src.Shape.copy();o.Shape.translate(A.Vector(0,0,-10.8)) if False else None
  shape=src.Shape.copy();shape.translate(A.Vector(0,0,-10.8));o.Shape=shape;objs.append(o)
 path=R/'PCB/main/dist/main-populated-with-conservative-envelopes.step';Part.export(objs,str(path));path.write_text('\n'.join(v.rstrip() for v in path.read_text().splitlines())+'\n')
 report=dict(status='CONSERVATIVE_ENVELOPES_NOT_VENDOR_ASSEMBLY',frame='X=nativeX-100; Y=139-nativeY; Z=board_bottom_origin; module antenna overhang included',objects=[o.Name for o in objs],sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 (R/'PCB/main/dist/conservative-step-frame.json').write_text(json.dumps(report,indent=2)+'\n');A.closeDocument(tmp.Name);A.setActiveDocument(doc.Name)
if __name__=='__main__':
 d=A.openDocument(str(R/'housing/smove-r2-enclosure.FCStd'));export(d)
