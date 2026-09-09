"""Explicit real-GUI review export and movable-group smoke test. No PCB writes.
Run housing/PresentAssembly.FCMacro in the pinned GUI, not the offscreen runner.
"""
import hashlib,json,time
from pathlib import Path
import FreeCAD as A,FreeCADGui as G,Part
from PySide import QtWidgets
import inspection
R=Path(__file__).resolve().parents[3];H=R/'housing';EX=H/'dist'
def main():
    G.getMainWindow().showMaximized()
    doc=A.openDocument(str(H/'smove-r2-enclosure.FCStd'))
    macro=H/'InspectAssembly.FCMacro';ns={'__file__':str(macro)}
    exec(compile(macro.read_text(),str(macro),'exec'),ns)
    panel=ns['smove_inspection_panel'];view=G.activeDocument().activeView()
    fixed={o.Name:(o.Placement.copy(),o.Shape.Volume) for o in doc.EngineeringSources.Group if hasattr(o,'Shape') and hasattr(o,'Placement') and not o.Shape.isNull()}
    def settle():
        for _ in range(6):QtWidgets.QApplication.processEvents();time.sleep(.06)
    def capture(name):
        doc.recompute();view.viewAxonometric();view.fitAll();G.updateGui();settle()
        view.saveImage(str(EX/(name+'.png')),1800,1200,'White')
    panel.reset_button.click();panel.ghost.setChecked(False);capture('assembled')
    panel.lid_button.click()
    assert doc.ViewLid.Placement.Base.z==32 and doc.ViewMain.Placement.isIdentity()
    panel.explode_button.click()
    assert all(doc.getObject(n).Placement.Base==doc.getObject(n).ExplodedOffset for n in inspection.GROUPS)
    capture('exploded')
    panel.selector.setCurrentIndex(panel.selector.findData('ViewBattery'));panel.axes[1].setValue(-20);panel.move_button.click()
    assert doc.ViewBattery.Placement.Base.y==-20
    panel.reset_button.click()
    for n in inspection.GROUPS:assert doc.getObject(n).Placement.isIdentity()
    for name,(p,volume) in fixed.items():
        o=doc.getObject(name);assert (o.Placement.Base-p.Base).Length<1e-7 and abs(o.Shape.Volume-volume)<1e-7
    # A true BRep section at X=12.5 shows battery ceiling, PCB air gap and lid without a third part.
    section=doc.addObject('App::DocumentObjectGroup','TemporarySection');build=json.loads((H/'validation/build.json').read_text())
    keep=Part.makeBox(22.1,55,30,A.Vector(-9.6,0,-1))
    for n in ['Base','Lid']+build['reference_objects']+build['hardware_objects']:
        src=doc.getObject(n);s=src.Shape.common(keep)
        if not s.isNull() and s.Volume>1e-7:
            o=doc.addObject('Part::Feature','Section_'+n);o.Shape=s;o.ViewObject.ShapeColor=src.ViewObject.ShapeColor;section.addObject(o)
    doc.InspectionAssembly.Visibility=False;view.viewRight();view.fitAll();G.updateGui();settle()
    view.saveImage(str(EX/'section.png'),1800,1200,'White')
    for o in list(section.Group):doc.removeObject(o.Name)
    doc.removeObject(section.Name)
    panel.reset_button.click();panel.ghost.setChecked(True);view.viewAxonometric();view.fitAll();G.updateGui();settle();doc.recompute();doc.save()
    report={'status':'PASS_REAL_FREECAD_GUI_CONTROLS','freecad_version':A.Version(),'manufacturing_release':False,
      'checks':['Native FCStd opened in real FreeCAD GUI','Delivered InspectAssembly macro executed','Lift lid leaves PCB fixed','Explode moves all seven display groups','Battery manual Y offset moves group only','Restore resets all group transforms','Engineering source placements/volumes unchanged','Native saved in assembled display state'],
      'method':'Explicit GUI macro, Qt button activation, activeView renders. Native desktop-tool observations are recorded separately in docs/revision-r2/two-part-case/images.md.',
      'native_sha256':hashlib.sha256((H/'smove-r2-enclosure.FCStd').read_bytes()).hexdigest()}
    (H/'validation/gui-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
    print('TWO-PART GUI PRESENTATION AND CONTROLS PASS',flush=True)
    return doc,panel
