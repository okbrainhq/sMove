"""Run inside the real FreeCAD GUI: save styled assembled FCStd, render, test controls.
This is not the offscreen FreeCAD Python runner: a real OpenGL GUI is required.
"""
import hashlib
import json
from pathlib import Path
import FreeCAD as A
import FreeCADGui as G
import Part
from PySide import QtCore, QtWidgets
import inspection
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'housing'; EX=OUT/'dist'; CACHE=ROOT/'.cache/housing'


def annotations(doc):
    group=doc.getObject('FrameAnnotations') or doc.addObject('App::DocumentObjectGroup','FrameAnnotations')
    group.Label='DISPLAY LABELS / body frame (not physical parts)'
    def text(name,words,pos,color=(.10,.15,.22),size=14):
        obj=doc.getObject(name) or doc.addObject('App::Annotation',name)
        obj.LabelText=words; obj.Position=A.Vector(*pos); obj.ViewObject.FontSize=size
        obj.ViewObject.TextColor=color; group.addObject(obj); return obj
    text('BodyFaceLabel',['BODY CONTACT | flat base underside Z=0'],(12,-10,0),size=14)
    text('MainPlaneLabel',['MAIN | TOP OUTWARD'],(1,37,12),size=13)
    text('CarrierPlaneLabel',['ICM-20948 integrated'],(-1,8,12),size=13)
    text('OutwardAxisLabel',['accel/gyro +Z OUT'],(12.5,21.5,28),(.8,.18,.04),14)
    text('TopFaceLabel',['TOP / OUTWARD'],(2,40,19),size=17)
    text('RGBLabel',['RGB'],(15.1,12.7,20),(.65,.03,.32),14)
    text('ResetLabel',['RESET'],(11,14.9,20),size=12)
    text('BootLabel',['BOOT'],(11,11.15,20),size=12)
    text('BodyOnlyLabel',['BODY SIDE','Main PCB BOTTOM faces this base'],(1,20,0),size=17)
    arrow=doc.getObject('OutwardAxis') or doc.addObject('Part::Feature','OutwardAxis')
    arrow.Shape=Part.makeCylinder(.28,14,A.Vector(12.5,21.5,12.0)).fuse(Part.makeCone(.85,0,2,A.Vector(12.5,21.5,26.0)))
    arrow.ViewObject.ShapeColor=(1.,.28,.03); group.addObject(arrow)
    return group


def main():
    G.getMainWindow().resize(1600,1000)
    doc=A.openDocument(str(OUT/'smove-r2-enclosure.FCStd'))
    macro=OUT/'InspectAssembly.FCMacro'
    namespace={'__file__':str(macro)}
    exec(compile(macro.read_text(),str(macro),'exec'),namespace)
    panel=namespace['smove_inspection_panel']
    notes=annotations(doc)
    view=G.activeDocument().activeView()
    # White viewport; set only this isolated application's preferences.
    params=A.ParamGet('User parameter:BaseApp/Preferences/View')
    params.SetBool('Simple',True); params.SetBool('UseNewSelection',True)
    saved_shapes={o.Name:(o.Placement.copy(),o.Shape.Volume) for o in doc.EngineeringSources.Group if hasattr(o,'Shape') and hasattr(o,'Placement') and not o.Shape.isNull()}
    def show_notes(names):
        notes.Visibility=True
        for obj in notes.Group:obj.Visibility=obj.Name in names
    def settle():
        # Let camera animation/MDI startup complete before image capture.
        import time
        for _ in range(8):QtWidgets.QApplication.processEvents();time.sleep(.05)
    def capture(name,mode='iso'):
        for area in G.getMainWindow().findChildren(QtWidgets.QMdiArea):
            for window in area.subWindowList():
                if 'smove' in window.windowTitle().lower():area.setActiveSubWindow(window)
        G.updateGui();settle()
        if mode=='iso':view.viewAxonometric()
        elif mode=='top':view.viewTop()
        elif mode=='bottom':view.viewBottom()
        elif mode=='front':view.viewFront()
        doc.recompute();settle();view.fitAll();G.updateGui();view.redraw();settle();G.updateGui()
        view.saveImage(str(EX/(name+'.png')),2000,1250,'White')
    panel.reset_button.click(); show_notes(('BodyFaceLabel','MainPlaneLabel','CarrierPlaneLabel','OutwardAxisLabel','OutwardAxis'))
    capture('assembled')
    # Real GUI button activation, not just calling the underlying transform helper.
    panel.lid_button.click()
    assert doc.ViewLid.Placement.Base.z==32 and doc.ViewMain.Placement.isIdentity() and doc.ViewDivider.Placement.isIdentity()
    panel.explode_button.click()
    assert panel.slider.value()==100 and doc.ViewDivider.Placement.Base==doc.ViewDivider.ExplodedOffset
    show_notes(())
    capture('exploded')
    settle();G.getMainWindow().grab().save(str(EX/'freecad-inspection.png'))
    panel.selector.setCurrentIndex(panel.selector.findData('ViewBase')); panel.axes[2].setValue(-8); panel.move_button.click()
    assert doc.ViewBase.Placement.Base.z==-8
    panel.reset_button.click()
    for name in inspection.GROUPS:assert doc.getObject(name).Placement.isIdentity()
    for name,(placement,volume) in saved_shapes.items():
        obj=doc.getObject(name)
        assert (obj.Placement.Base-placement.Base).Length<1e-7 and abs(obj.Shape.Volume-volume)<1e-7
    # Closed simple enclosure and explicit opposite body face.
    panel.ghost.setChecked(False); show_notes(('TopFaceLabel','RGBLabel','ResetLabel','BootLabel'))
    capture('top','top')
    dims=json.loads((OUT/'validation/mechanical.json').read_text())['measured_external_mm']
    annotation=doc.addObject('App::Annotation','MeasuredDimensions');annotation.LabelText=[f'MEASURED CAD: {dims[1]:.1f} L x {dims[0]:.1f} W x {dims[2]:.1f} H mm','Nominal CAD <50 x 30 x 20; physical fit/battery gates OPEN'];annotation.Position=A.Vector(-1,-6,20);annotation.ViewObject.FontSize=16
    capture('dimensions','top');doc.removeObject(annotation.Name)
    show_notes(('BodyOnlyLabel',)); capture('body-side','bottom')
    # A genuine native Boolean section through the H1 M3 stack, lower key, battery and single PCB.
    sections=doc.addObject('App::DocumentObjectGroup','TemporarySection')
    keep=Part.makeBox(14,50,24,A.Vector(-4,0,-1))
    for name in ['Base','Lid','BatteryDivider']+json.loads((CACHE/'build.json').read_text())['reference_objects']+json.loads((CACHE/'build.json').read_text())['hardware_objects']:
        src=doc.getObject(name);shape=src.Shape.common(keep)
        if not shape.isNull() and shape.Volume>1e-7:
            obj=doc.addObject('Part::Feature','Section_'+name);obj.Shape=shape;obj.ViewObject.ShapeColor=src.ViewObject.ShapeColor
            obj.ViewObject.DisplayMode='Flat Lines';sections.addObject(obj)
    doc.InspectionAssembly.Visibility=False;show_notes(())
    capture('section','front')
    for obj in list(sections.Group):doc.removeObject(obj.Name)
    doc.removeObject(sections.Name)
    doc.InspectionAssembly.Visibility=True
    panel.ghost.setChecked(True);panel.reset_button.click();show_notes(('BodyFaceLabel','MainPlaneLabel','CarrierPlaneLabel','OutwardAxisLabel','OutwardAxis'))
    view.viewAxonometric();view.fitAll();G.updateGui()
    doc.recompute();doc.save()
    report=dict(status='PASS_REAL_FREECAD_GUI_CONTROLS',freecad_version=A.Version(),
                checks=['Delivered InspectAssembly.FCMacro executed successfully','FCStd opened with real OpenGL viewport','Lift lid preserves main PCB and divider placements','Explode button and slider move native groups',
                        'Selected base offset changes group only','Restore returns ALL group/link transforms to assembled',
                        'Fixed engineering source placements and volumes unchanged','Native saved with assembled default and distinct named parts'],
                method='Programmatic Qt button clicks in the actual FreeCAD GUI; screenshot from QMainWindow.grab, renders from activeView.saveImage.',
                desktop_agent='Desktop observation available this turn; programmatic Qt GUI macro tests, not native GUI PCB routing.',
                exploded_display_is_not_alignment_geometry=True,
                native_sha256=hashlib.sha256((OUT/'smove-r2-enclosure.FCStd').read_bytes()).hexdigest(),
                source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'scripts/r2/enclosure/inspection.py',OUT/'InspectAssembly.FCMacro']})
    (OUT/'validation/gui-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
    print('GUI PRESENTATION AND CONTROLS PASS',flush=True)
    return doc,panel
