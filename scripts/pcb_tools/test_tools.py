"""CPU-only regression tests using synthetic native KiCad boards (no GUI)."""
import math
import tempfile
import unittest
from pathlib import Path
import pcbnew as p
from .geometry import clean,patterns,best_pattern,octilinear,simplify,length
from .router import Router,Rules,Plan,V,uid
from .manual import waypoint_plan
from .edit import CopperTransaction
from .io import clone_project,digest


def board():
    b=p.BOARD();b.SetCopperLayerCount(4)
    for net in ('/N','/BLOCK'):
        b.Add(p.NETINFO_ITEM(b,net))
    corners=[(0,0),(10,0),(10,10),(0,10)]
    for a,z in zip(corners,corners[1:]+corners[:1]):
        s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(a));s.SetEnd(V(z));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
    return b

class GeometryTests(unittest.TestCase):
    def test_exact_endpoints_all_quadrants(self):
        for a,z in [((1.0125,2.03),(7.1,5.04)),((8,8),(1,2)),((2,8),(7,1)),((8,2),(1,7)),((1,1),(1,1))]:
            for q in patterns(a,z):
                self.assertEqual(q[0],a);self.assertEqual(q[-1],z)
                self.assertTrue(all(octilinear(u,v) for u,v in zip(q,q[1:])))
    def test_straight_preferred(self):
        self.assertEqual(best_pattern((1,1),(8,1),lambda *_:True),[(1,1),(8,1)])
    def test_staircase_removed(self):
        q=simplify([(1,1),(2,1),(2,2),(3,2),(3,3)],lambda *_:True)
        self.assertEqual(q,[(1,1),(3,3)])
    def test_duplicates_collinear_and_reversal(self):
        self.assertEqual(clean([(0,0),(0,0),(1,0),(2,0),(1,0)]),[(0,0),(2,0),(1,0)])
    def test_blocked(self):
        self.assertIsNone(best_pattern((1,1),(3,4),lambda *_:False))
    def test_deterministic(self):
        self.assertEqual(list(patterns((1.1,2.2),(8.8,7.7))),list(patterns((1.1,2.2),(8.8,7.7))))

class NativeTests(unittest.TestCase):
    def setUp(self): self.b=board();self.r=Router(self.b)
    def test_route_no_mutation_until_apply(self):
        plan=self.r.plan('/N',(1,1,p.F_Cu),(8,1,p.F_Cu),.2)
        self.assertEqual(len(list(self.b.GetTracks())),0)
        self.r.apply(plan);self.assertEqual(len(list(self.b.GetTracks())),1)
    def test_router_uses_bottom_and_vias(self):
        self.r.apply(waypoint_plan('/BLOCK',[(5,.4,'F.Cu'),(5,9.6,'F.Cu')],.2))
        plan=self.r.plan('/N',(2,5,p.F_Cu),(8,5,p.F_Cu),.2)
        self.assertEqual(len(plan.vias),2)
        self.assertTrue(any(l==p.B_Cu for l,_ in plan.legs))
        self.r.apply(plan)
    def test_bend_aware_search(self):
        from .router import Obstacles
        self.r.apply(waypoint_plan('/BLOCK',[(5,3,'F.Cu'),(5,7,'F.Cu')],.4))
        r=Router(self.b,Rules(grid=.2,max_nodes=10000))
        plan=r._search(Obstacles(self.b,'/N'),'/N',(2,5,p.F_Cu),(8,5,p.F_Cu),.2,(p.F_Cu,))
        self.assertFalse(plan.vias)
        self.assertLessEqual(plan.summary()['segments'],5)
        r.apply(plan)
    def test_manual_two_layers(self):
        plan=waypoint_plan('/N',[(1,1,'F.Cu'),(2,1,'F.Cu'),(2,1,'B.Cu'),(8,1,'B.Cu'),(8,1,'F.Cu'),(9,1,'F.Cu')])
        self.r.apply(plan)
        self.assertEqual(sum(isinstance(t,p.PCB_VIA) for t in self.b.GetTracks()),2)
        self.assertEqual({t.GetLayer() for t in self.b.GetTracks() if not isinstance(t,p.PCB_VIA)},{p.F_Cu,p.B_Cu})
    def test_no_diagonal_layer_change(self):
        with self.assertRaises(ValueError): waypoint_plan('/N',[(1,1,'F.Cu'),(2,2,'B.Cu')])
    def test_internal_layer_rejected(self):
        with self.assertRaises(ValueError): waypoint_plan('/N',[(1,1,'In1.Cu'),(2,2,'In1.Cu')])
    def test_unknown_net_rejected(self):
        with self.assertRaises(ValueError): self.r.apply(waypoint_plan('/typo',[(1,1,'F.Cu'),(2,1,'F.Cu')]))
    def test_nonfinite_and_negative(self):
        for w in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): waypoint_plan('/N',[(1,1,'F.Cu'),(2,1,'F.Cu')],w)
        with self.assertRaises(ValueError): waypoint_plan('/N',[(1,1,'F.Cu'),(math.inf,1,'F.Cu')])
    def test_edge_clearance(self):
        with self.assertRaises(RuntimeError): self.r.apply(waypoint_plan('/N',[(.1,.1,'F.Cu'),(8,.1,'F.Cu')]))
        self.assertFalse(list(self.b.GetTracks()))
    def test_stale_plan_and_no_partial_insertion(self):
        plan=waypoint_plan('/N',[(1,2,'F.Cu'),(8,2,'F.Cu'),(8,8,'F.Cu')])
        self.r.apply(waypoint_plan('/BLOCK',[(7,5,'F.Cu'),(9,5,'F.Cu')]))
        with self.assertRaises(RuntimeError): self.r.apply(plan)
        self.assertEqual(len(list(self.b.GetTracks())),1)
    def test_width_checked_not_just_centerline(self):
        self.r.apply(waypoint_plan('/BLOCK',[(1,1,'F.Cu'),(8,1,'F.Cu')],.8))
        with self.assertRaises(RuntimeError): self.r.apply(waypoint_plan('/N',[(1,1.5,'F.Cu'),(8,1.5,'F.Cu')],.2))
    def test_transaction_rollback(self):
        t=self.r.apply(waypoint_plan('/N',[(1,1,'F.Cu'),(8,1,'F.Cu')]))[0];original=uid(t)
        with CopperTransaction(self.b) as tx:
            tx.remove([t]);self.r.apply(waypoint_plan('/N',[(1,2,'F.Cu'),(8,2,'F.Cu')]))
        self.assertEqual([uid(t) for t in self.b.GetTracks()],[original])
    def test_locked_ripup_rejected(self):
        t=self.r.apply(waypoint_plan('/N',[(1,1,'F.Cu'),(8,1,'F.Cu')]))[0];t.SetLocked(True)
        with self.assertRaises(ValueError):
            with CopperTransaction(self.b) as tx: tx.remove([t])
    def test_paste_via_rejected(self):
        f=p.FOOTPRINT(self.b);f.SetReference('X1');self.b.Add(f)
        layers=p.LSET()
        for l in (p.F_Cu,p.F_Paste,p.F_Mask): layers.AddLayer(l)
        a=p.PAD(f);a.SetNumber('1');a.SetAttribute(p.PAD_ATTRIB_SMD);a.SetShape(p.PAD_SHAPE_RECT);a.SetLayerSet(layers);a.SetSize(V((1,1)));a.SetPosition(V((3,3)));a.SetNet(self.b.FindNet('/N'));f.Add(a)
        with self.assertRaises(RuntimeError): self.r.apply(waypoint_plan('/N',[(3,3,'F.Cu'),(3,3,'B.Cu'),(5,3,'B.Cu')]))
    def test_output_guard(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d,'test.kicad_pcb');p.SaveBoard(str(f),self.b);before=digest(f)
            with self.assertRaises(ValueError):clone_project(f,d)
            out=clone_project(f,Path(d,'candidate'));self.assertEqual(digest(out),before);self.assertEqual(digest(f),before)
            with self.assertRaises(FileExistsError):clone_project(f,Path(d,'candidate'))

if __name__=='__main__': unittest.main()
