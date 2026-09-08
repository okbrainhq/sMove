"""Safe FreeCAD GUI inspection controls; only native display groups are moved.
No file writes, source placement edits, constraints, downloads or automatic macros.
"""
import FreeCAD as A
import FreeCADGui as G
from PySide import QtCore, QtWidgets
GROUPS=('ViewBase','ViewLid','ViewMain','ViewCarrier','ViewBattery','ViewCables','ViewHardware')
COLORS={'print':(.32,.55,.82),'main_pcb':(.08,.52,.29),'carrier_pcb':(.13,.62,.44),
        'main_component':(.24,.26,.29),'carrier_component':(.24,.26,.29),'tail':(.7,.7,.7),
        'battery':(.94,.68,.20),'harness':(.86,.20,.12),'hardware':(.72,.72,.76)}

def prepare(doc):
    assert doc.getObject('InspectionAssembly') and all(doc.getObject(n) for n in GROUPS), 'Open the generated R2 enclosure first.'
    for obj in doc.Objects:
        if obj.ViewObject:obj.ViewObject.Visibility=False
    for name in GROUPS:
        group=doc.getObject(name); group.Visibility=True
        for link in group.Group:
            src=link.LinkedObject
            color=COLORS.get(src.Role,(.7,.7,.7))
            if src.Name=='Main_D1':color=(.96,.24,.64)
            if src.Name=='Carrier_U2':color=(.98,.42,.1)
            src.ViewObject.ShapeColor=color
            src.ViewObject.LineColor=(.15,.16,.19)
            src.ViewObject.DisplayMode='Flat Lines'
            src.ViewObject.Visibility=False
            link.Visibility=True
    doc.InspectionAssembly.Visibility=True
    restore(doc)


def restore(doc):
    for name in GROUPS:
        group=doc.getObject(name); group.Placement=A.Placement(); group.Visibility=True
        for link in group.Group:
            # Also undo individual link moves, never modify engineering source transforms.
            link.LinkPlacement=link.LinkedObject.Placement
            link.Visibility=True
    group=doc.getObject('FrameAnnotations')
    if group:
        group.Visibility=True
        for obj in group.Group:obj.Visibility=obj.Name in ('BodyFaceLabel','MainPlaneLabel','CarrierPlaneLabel','OutwardAxisLabel','OutwardAxis')
    doc.recompute()


def explode(doc,amount):
    if doc.getObject('FrameAnnotations'):doc.FrameAnnotations.Visibility=(amount==0)
    for name in GROUPS:
        group=doc.getObject(name); group.Placement=A.Placement(group.ExplodedOffset*(amount/100.),A.Rotation())
    doc.recompute()


def transparency(doc,value):
    # Link shares the fixed source's visual attributes only. Shape/placement is never changed.
    for name in ('Base','Lid'):doc.getObject(name).ViewObject.Transparency=value
    G.activeDocument().activeView().redraw()


class Panel(QtWidgets.QDockWidget):
    def __init__(self,doc):
        super().__init__('sMove | Inspect assembly',G.getMainWindow())
        self.doc=doc; self.setObjectName('sMoveInspectionDock')
        body=QtWidgets.QWidget(); layout=QtWidgets.QVBoxLayout(body); self.setWidget(body)
        note=QtWidgets.QLabel('DISPLAY ONLY: moving parts does not revise CAD fit.\nBase underside = BODY. Sensor +Z = OUTWARD.\nRestore ASSEMBLED before saving an inspection copy.')
        note.setWordWrap(True); layout.addWidget(note)
        self.state=QtWidgets.QLabel('ASSEMBLED | true placements'); layout.addWidget(self.state)
        self.reset_button=QtWidgets.QPushButton('Restore ASSEMBLED'); self.reset_button.clicked.connect(self.reset); layout.addWidget(self.reset_button)
        self.lid_button=QtWidgets.QPushButton('Lift lid only'); self.lid_button.clicked.connect(self.open_lid); layout.addWidget(self.lid_button)
        self.explode_button=QtWidgets.QPushButton('Explode all parts'); self.explode_button.clicked.connect(lambda:self.slider.setValue(100)); layout.addWidget(self.explode_button)
        self.slider=QtWidgets.QSlider(QtCore.Qt.Horizontal); self.slider.setRange(0,100); self.slider.valueChanged.connect(self.on_explode); layout.addWidget(self.slider)
        self.ghost=QtWidgets.QCheckBox('Transparent case'); self.ghost.setChecked(True)
        self.ghost.toggled.connect(lambda checked:transparency(self.doc,80 if checked else 0)); layout.addWidget(self.ghost)
        layout.addWidget(QtWidgets.QLabel('Move one group (mm, relative to assembled):'))
        self.selector=QtWidgets.QComboBox()
        for name in GROUPS:self.selector.addItem(name[4:],name)
        self.selector.currentIndexChanged.connect(self.load_position); layout.addWidget(self.selector)
        form=QtWidgets.QFormLayout(); self.axes=[]
        for axis in 'XYZ':
            spin=QtWidgets.QDoubleSpinBox(); spin.setRange(-150,150); spin.setDecimals(1); spin.setSingleStep(5)
            self.axes.append(spin); form.addRow(axis,spin)
        layout.addLayout(form)
        self.move_button=QtWidgets.QPushButton('Apply group offset'); self.move_button.clicked.connect(self.move); layout.addWidget(self.move_button)
        for text,func in [('Isometric / fit',self.iso),('TOP / outward',self.top),('BODY underside',self.bottom)]:
            button=QtWidgets.QPushButton(text); button.clicked.connect(func); layout.addWidget(button)
        layout.addStretch(); self.setMinimumWidth(310)
        self.reset()
    def redraw(self,fit=False):
        self.doc.recompute(); view=G.activeDocument().activeView()
        if fit:view.fitAll()
        view.redraw(); G.updateGui()
    def load_position(self,*args):
        p=self.doc.getObject(self.selector.currentData()).Placement.Base
        for spin,value in zip(self.axes,tuple(p)):spin.setValue(value)
    def reset(self):
        self.slider.blockSignals(True); self.slider.setValue(0); self.slider.blockSignals(False)
        restore(self.doc); transparency(self.doc,80 if self.ghost.isChecked() else 0)
        self.state.setText('ASSEMBLED | true placements'); self.load_position(); self.redraw(True)
    def on_explode(self,value):
        explode(self.doc,value); self.state.setText('ASSEMBLED | true placements' if value==0 else 'EXPLODED DISPLAY | NOT fit/alignment geometry')
        self.load_position(); self.redraw(True)
    def open_lid(self):
        self.reset();
        if self.doc.getObject('FrameAnnotations'):self.doc.FrameAnnotations.Visibility=False
        self.doc.ViewLid.Placement.Base=A.Vector(0,0,32); self.doc.ViewHardware.Placement.Base=A.Vector(0,0,40)
        self.state.setText('LID LIFTED | boards remain at true placements'); self.load_position(); self.redraw(True)
    def move(self):
        if self.doc.getObject('FrameAnnotations'):self.doc.FrameAnnotations.Visibility=False
        name=self.selector.currentData(); self.doc.getObject(name).Placement=A.Placement(A.Vector(*(s.value() for s in self.axes)),A.Rotation())
        self.state.setText('CUSTOM DISPLAY OFFSET | NOT fit/alignment geometry'); self.redraw(True)
    def iso(self):G.activeDocument().activeView().viewAxonometric(); self.redraw(True)
    def top(self):G.activeDocument().activeView().viewTop(); self.redraw(True)
    def bottom(self):G.activeDocument().activeView().viewBottom(); self.redraw(True)


def show(doc=None):
    doc=doc or A.ActiveDocument
    assert doc is not None, 'Open housing/smove-r2-enclosure.FCStd first.'
    old=G.getMainWindow().findChild(QtWidgets.QDockWidget,'sMoveInspectionDock')
    if old:old.close(); old.deleteLater()
    G.activateWorkbench('PartWorkbench')
    prepare(doc)
    panel=Panel(doc); G.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea,panel)
    panel.show(); panel.iso(); return panel
