#!/usr/bin/env python3
"""Tests for the JLCPCB exporter.

Unit tests are standard-library only: they parse synthetic KiCad text and replace
KiCad's CLI with a fake that writes the files a real ``kicad-cli`` would write, so
they run without KiCad installed.

The opt-in integration test runs the real tool against this repository's board:

    JLC_INTEGRATION=1 python3 -m unittest scripts/jlcpcb/test_export.py -v

Run either form from the repository root.
"""

import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
import zipfile

SCRIPT = Path(__file__).resolve().parent / "export.py"
ROOT = SCRIPT.parents[2]
spec = importlib.util.spec_from_file_location("jlc_export", SCRIPT)
jlc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jlc)

SMD_PAD = '(pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu" "F.Paste" "F.Mask"))'
TH_PAD = '(pad "1" thru_hole circle (at 0 0) (size 2 2) (drill 1) (layers "*.Cu"))'
NPTH_PAD = '(pad "" np_thru_hole circle (at 0 0) (size 2 2) (drill 2) (layers "*.Cu"))'
LAYERS = ('(0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (2 "B.Cu" signal) '
          '(13 "F.Paste" user) (15 "B.Paste" user) (5 "F.SilkS" user) (7 "B.SilkS" user) '
          '(1 "F.Mask" user) (3 "B.Mask" user) (25 "Edge.Cuts" user)')


def footprint(ref, value="10k", lib="Test:R", side="F.Cu", at=(0.0, 0.0, 0.0),
              attr=("smd",), fields=None, pads=None):
    """Render one footprint s-expression."""
    properties = [f'(property "Reference" "{ref}" (at 0 0 0))',
                  f'(property "Value" "{value}" (at 0 0 0))']
    for name, field_value in (fields or {}).items():
        properties.append(f'(property "{name}" "{field_value}" (at 0 0 0))')
    pad_nodes = pads
    if pad_nodes is None:
        pad_nodes = [SMD_PAD]
    return (f'(footprint "{lib}" (layer "{side}") (at {" ".join(str(item) for item in at)}) '
            + " ".join(properties) + f' (attr {" ".join(attr)}) ' + " ".join(pad_nodes) + ")")


def board_text(footprints, aux_origin="(aux_axis_origin 100 135)"):
    return (f'(kicad_pcb (version 20241229) (generator "pcbnew") (general (thickness 1))\n'
            f'  (layers {LAYERS})\n'
            f'  (setup {aux_origin})\n'
            + "\n".join("  " + item for item in footprints) + "\n)\n")


def positions_csv(rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


def position(ref, value="10k", x=0.0, y=0.0, rotation=0.0, side="top"):
    return {"Ref": ref, "Val": value, "Package": "R", "PosX": f"{x:.6f}", "PosY": f"{y:.6f}",
            "Rot": f"{rotation:.6f}", "Side": side}


def netlist_text(components):
    """components: list of (ref, value, footprint, {field: value}, excluded_from_bom)."""
    parts = []
    for ref, value, foot, fields, excluded in components:
        field_nodes = "".join(f'(field (name "{name}") "{item}")' for name, item in fields.items())
        flag = '\n      (property (name "exclude_from_bom"))' if excluded else ""
        parts.append(f'''    (comp (ref "{ref}")
      (value "{value}")
      (footprint "{foot}")
      (fields {field_nodes})
      (property (name "Reference") (value "{ref}")){flag})''')
    return "(export (version \"E\")\n  (components\n" + "\n".join(parts) + "))\n"


def args_for(project, *extra):
    return jlc.argument_parser().parse_args([str(project), *extra])


def write_project(directory, footprints, aux_origin="(aux_axis_origin 100 135)"):
    board = Path(directory) / "board.kicad_pcb"
    board.write_text(board_text(footprints, aux_origin), encoding="utf-8")
    schematic = Path(directory) / "board.kicad_sch"
    schematic.write_text("(kicad_sch)\n", encoding="utf-8")
    return board, schematic


def fake_cli(gerber_names, netlist, positions):
    """Stand-in for kicad-cli: write exactly the files the real tool would write."""
    def run(cli, arguments, cwd):
        if arguments[:3] == ["pcb", "export", "pos"]:
            Path(arguments[arguments.index("-o") + 1]).write_text(positions, encoding="utf-8")
        elif arguments[:2] == ["sch", "export"]:
            Path(arguments[arguments.index("-o") + 1]).write_text(netlist, encoding="utf-8")
        elif arguments[2] == "gerbers":
            target = Path(arguments[arguments.index("-o") + 1])
            for name in gerber_names:
                (target / name).write_text("G04 mock*\n", encoding="utf-8")
        elif arguments[2] == "drill":
            target = Path(arguments[arguments.index("-o") + 1])
            (target / "board-PTH.drl").write_text("M48\n", encoding="utf-8")
            (target / "board-NPTH.drl").write_text("M48\n", encoding="utf-8")
        return ""
    return run


GERBER_NAMES = ["board-F_Cu.gtl", "board-In1_Cu.g1", "board-In2_Cu.g2", "board-B_Cu.gbl",
                "board-F_Mask.gts", "board-B_Mask.gbs", "board-F_Silkscreen.gto",
                "board-B_Silkscreen.gbo", "board-Edge_Cuts.gm1", "board-F_Paste.gtp",
                "board-B_Paste.gbp", "board-job.gbrjob"]


class ParsingTest(unittest.TestCase):
    def test_parse_sexpr_nesting_and_escapes(self):
        node = jlc.parse_sexpr('(a "b(1)" (c 2.5) (d (e "x\\\\y")))')
        self.assertEqual(node[0], "a")
        self.assertEqual(node[1], "b(1)")
        self.assertEqual(jlc.children(node, "c")[0][1], "2.5")
        self.assertEqual(jlc.atom(jlc.child(jlc.child(node, "d"), "e"), 1), "x\\y")

    def test_parse_sexpr_rejects_unbalanced_input(self):
        with self.assertRaises(jlc.ExportError):
            jlc.parse_sexpr("(a (b)")
        with self.assertRaises(jlc.ExportError):
            jlc.parse_sexpr("(a))")

    def test_read_board_reads_layers_origin_and_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            board, _ = write_project(directory, [footprint("R1", fields={"LCSC": "C123", "MPN": "X"})])
            data = jlc.read_board(board)
        self.assertEqual(data["copper_layers"], ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
        self.assertEqual(data["aux_origin"], (100.0, 135.0))
        item = data["footprints"][0]
        self.assertEqual((item["ref"], item["value"], item["footprint"]), ("R1", "10k", "R"))
        self.assertEqual(item["fields"]["LCSC"], "C123")
        self.assertTrue(item["smd"] and item["electrical"] and not item["dnp"])

    def test_read_board_detects_flags_and_through_hole(self):
        with tempfile.TemporaryDirectory() as directory:
            board, _ = write_project(directory, [
                footprint("J2", attr=("through_hole", "exclude_from_pos_files", "exclude_from_bom"),
                          pads=[TH_PAD]),
                footprint("H1", attr=("exclude_from_bom",),
                          pads=[NPTH_PAD]),
            ])
            data = jlc.read_board(board)
        j2, h1 = data["footprints"]
        self.assertTrue(j2["excluded_from_bom"] and j2["excluded_from_pos"] and not j2["smd"])
        self.assertFalse(h1["electrical"], "a non-plated hole is not an electrical pad")


class FieldTest(unittest.TestCase):
    def board_record(self, **fields):
        return [("PCB", {"ref": "R1"}, fields)]

    def test_part_number_aliases_and_normalization(self):
        for name in ("LCSC", "lcsc part number", "JLCPCB Part #", "LCSC_Part_Number"):
            self.assertEqual(jlc.part_number(self.board_record(**{name: "c1525"})), "C1525")

    def test_part_number_rejects_non_catalog_values(self):
        for value in ("1525", "CL05B104KO5NNNC", "https://lcsc.com/C1525", "C"):
            with self.assertRaises(jlc.ExportError):
                jlc.part_number(self.board_record(LCSC=value))

    def test_conflicting_part_numbers_stop_the_export(self):
        records = [("PCB", {}, {"LCSC": "C1525"}), ("schematic", {}, {"LCSC_Part": "C16780"})]
        with self.assertRaises(jlc.ExportError):
            jlc.part_number(records)

    def test_identical_values_across_sources_are_accepted(self):
        records = [("PCB", {}, {"LCSC": "C1525"}), ("schematic", {}, {"LCSC Part #": "C1525"})]
        self.assertEqual(jlc.part_number(records), "C1525")

    def test_empty_and_placeholder_fields_count_as_missing(self):
        self.assertEqual(jlc.part_number(self.board_record(LCSC="~")), "")
        self.assertEqual(jlc.part_number(self.board_record(LCSC="")), "")

    def test_rotation_offset_field(self):
        self.assertEqual(jlc.rotation_offset(self.board_record(**{"JLCPCB Rotation Offset": "-90"})), -90.0)
        with self.assertRaises(jlc.ExportError):
            jlc.rotation_offset(self.board_record(**{"JLCPCB Rotation Offset": "ninety"}))


class AssemblyTest(unittest.TestCase):
    def build(self, footprints, symbols, positions, *extra, aux="(aux_axis_origin 0 0)"):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        board, _ = write_project(directory, footprints, aux)
        data = jlc.read_board(board)
        return jlc.select_assembly(data, symbols, positions, args_for(directory, *extra))

    def test_selects_smd_and_skips_excluded_parts(self):
        footprints = [
            footprint("R1", fields={"LCSC": "C1"}),
            footprint("J2", attr=("through_hole", "exclude_from_bom"), pads=[TH_PAD]),
            footprint("U7", fields={"LCSC": "C7"}, attr=("smd", "dnp")),
            footprint("H1", pads=[NPTH_PAD]),
        ]
        positions = {ref: position(ref) for ref in ("R1", "J2", "U7", "H1")}
        rows, skipped, warnings = self.build(footprints, {}, positions)
        self.assertEqual([row["reference"] for row in rows], ["R1"])
        reasons = {item["reference"]: item["reason"] for item in skipped}
        self.assertIn("Do Not Populate", reasons["U7"])
        self.assertIn("through-hole footprint", reasons["J2"])
        self.assertIn("no electrical pads", reasons["H1"])

    def test_through_hole_can_be_included_explicitly(self):
        footprints = [footprint("J2", value="conn", attr=("through_hole",), fields={"LCSC": "C1"},
                                pads=[TH_PAD])]
        rows, _, _ = self.build(footprints, {}, {"J2": position("J2")}, "--include-through-hole")
        self.assertEqual([row["reference"] for row in rows], ["J2"])

    def test_schematic_exclusion_is_respected(self):
        symbols = {
            "R1": {"value": "10k", "footprint": "R", "fields": {"LCSC": "C1"},
                   "excluded_from_bom": True, "excluded_from_board": False},
            "R2": {"value": "10k", "footprint": "R", "fields": {"LCSC": "C1"},
                   "excluded_from_bom": False, "excluded_from_board": True},
        }
        footprints = [footprint("R1", fields={"LCSC": "C1"}), footprint("R2", fields={"LCSC": "C1"}),
                      footprint("R3", fields={"LCSC": "C1"})]
        positions = {ref: position(ref) for ref in ("R1", "R2", "R3")}
        rows, skipped, _ = self.build(footprints, symbols, positions)
        self.assertEqual([row["reference"] for row in rows], ["R3"])
        reasons = {item["reference"]: item["reason"] for item in skipped}
        self.assertIn("excluded from BOM in the schematic", reasons["R1"])
        self.assertIn("excluded from board in the schematic", reasons["R2"])

    def test_export_refuses_when_nothing_is_selected(self):
        with self.assertRaises(jlc.ExportError):
            self.build([footprint("R1", fields={"LCSC": "C1"})], {}, {"R1": position("R1")},
                       "--side", "bottom")

    def test_schematic_only_part_number_is_used(self):
        symbols = {"R1": {"value": "10k", "footprint": "R", "fields": {"LCSC": "C1525"},
                          "excluded_from_bom": False, "excluded_from_board": False}}
        rows, _, _ = self.build([footprint("R1")], symbols, {"R1": position("R1")})
        self.assertEqual(rows[0]["lcsc"], "C1525")

    def test_missing_part_number_is_blank_with_a_warning(self):
        rows, _, warnings = self.build([footprint("R1")], {}, {"R1": position("R1")}, "--require-part-numbers")
        self.assertEqual(rows[0]["lcsc"], "")

    def test_unannotated_reference_is_rejected(self):
        with self.assertRaises(jlc.ExportError):
            self.build([footprint("R?")], {}, {"R?": position("R?")})

    def test_duplicate_reference_is_rejected(self):
        with self.assertRaises(jlc.ExportError):
            self.build([footprint("R1"), footprint("R1")], {}, {"R1": position("R1")})

    def test_missing_position_is_rejected(self):
        with self.assertRaises(jlc.ExportError):
            self.build([footprint("R1")], {}, {})

    def test_stale_position_is_rejected(self):
        with self.assertRaises(jlc.ExportError):
            self.build([footprint("R1")], {}, {"R1": position("R1", x=1.0)})
        with self.assertRaises(jlc.ExportError):
            self.build([footprint("R1")], {}, {"R1": position("R1", rotation=90.0)})

    def test_position_is_relative_to_the_drill_origin(self):
        rows, _, _ = self.build([footprint("R1", at=(40.0, 65.0, 0.0))], {},
                                {"R1": position("R1", x=-60.0, y=70.0)},
                                aux="(aux_axis_origin 100 135)")
        self.assertEqual((rows[0]["x"], rows[0]["y"]), (-60.0, 70.0))

    def test_rotation_offset_is_applied_and_normalized(self):
        rows, _, _ = self.build(
            [footprint("U1", at=(0.0, 0.0, -90.0), fields={"LCSC": "C1", "JLCPCB Rotation Offset": "90"})],
            {}, {"U1": position("U1", rotation=-90.0)})
        self.assertEqual(rows[0]["rotation"], 0.0)
        self.assertEqual(rows[0]["rotation_offset"], 90.0)

    def test_value_mismatch_between_sources_warns_and_uses_the_board(self):
        symbols = {"R1": {"value": "10k 1%", "footprint": "R", "fields": {},
                          "excluded_from_bom": False, "excluded_from_board": False}}
        rows, _, warnings = self.build([footprint("R1")], symbols, {"R1": position("R1")})
        self.assertEqual(rows[0]["value"], "10k")
        self.assertTrue(any("differs from board value" in warning for warning in warnings))

    def test_reference_present_in_only_one_source_warns(self):
        footprints = [footprint("R1", fields={"LCSC": "C1"}), footprint("R2", fields={"LCSC": "C1"})]
        symbols = {"R1": {"value": "10k", "footprint": "R", "fields": {"LCSC": "C1"},
                          "excluded_from_bom": False, "excluded_from_board": False}}
        positions = {ref: position(ref) for ref in ("R1", "R2")}
        _, _, warnings = self.build(footprints, symbols, positions)
        self.assertTrue(any("no schematic symbol" in warning for warning in warnings))

    def test_side_filter_and_empty_selection(self):
        footprints = [footprint("R1", fields={"LCSC": "C1"}),
                      footprint("R2", side="B.Cu", fields={"LCSC": "C1"})]
        positions = {"R1": position("R1"), "R2": position("R2", side="bottom")}
        rows, skipped, _ = self.build(footprints, {}, positions, "--side", "bottom")
        self.assertEqual([row["reference"] for row in rows], ["R2"])
        with self.assertRaises(jlc.ExportError):
            self.build([footprint("R1", fields={"LCSC": "C1"})], {}, {"R1": position("R1")},
                       "--side", "bottom")


class OutputTest(unittest.TestCase):
    def test_bom_groups_and_counts(self):
        rows = [{"reference": "R10", "value": "10k", "footprint": "R", "lcsc": "C1", "mpn": "",
                 "manufacturer": ""},
                {"reference": "R2", "value": "10k", "footprint": "R", "lcsc": "C1", "mpn": "",
                 "manufacturer": ""},
                {"reference": "R3", "value": "10k", "footprint": "R", "lcsc": "C2", "mpn": "",
                 "manufacturer": ""}]
        bom = jlc.bom_rows(rows)
        self.assertEqual(len(bom), 2, "different purchase codes are never merged")
        self.assertEqual(bom[0][1], "R2, R10")
        self.assertEqual(bom[0][4], 2)

    def test_cpl_rows_are_naturally_sorted_and_formatted(self):
        rows = [{"reference": "R10", "x": 1.0, "y": -2.5, "rotation": 359.999, "side": "top"},
                {"reference": "R2", "x": 0.0, "y": 0.0, "rotation": 90.0, "side": "bottom"}]
        cpl = jlc.cpl_rows(rows)
        self.assertEqual([row[0] for row in cpl], ["R2", "R10"])
        self.assertEqual(cpl[0], ["R2", "0.0000", "0.0000", "Bottom", "90.00"])
        self.assertEqual(cpl[1][4], "360.00")

    def test_csv_quoting_of_commas(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "out.csv"
            jlc.write_csv(path, ("Comment", "Designator"), [["PESD5V0S2BT,215", "U9, U10"]])
            with path.open(newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows, [["Comment", "Designator"], ["PESD5V0S2BT,215", "U9, U10"]])

    def test_gerber_layers_follow_the_board_stack(self):
        with tempfile.TemporaryDirectory() as directory:
            board, _ = write_project(directory, [footprint("R1")])
            layers, copper = jlc.gerber_layers(jlc.read_board(board))
        self.assertEqual(copper, ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
        self.assertEqual(layers[:4], copper)
        self.assertIn("Edge.Cuts", layers)
        self.assertLess(layers.index("Edge.Cuts"), layers.index("F.Paste"))

    def test_protect_requires_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "bom.csv").write_text("old", encoding="utf-8")
            with self.assertRaises(jlc.ExportError):
                jlc.protect(Path(directory), jlc.ARTIFACTS, overwrite=False)
            jlc.protect(Path(directory), jlc.ARTIFACTS, overwrite=True)


class CliArgumentTest(unittest.TestCase):
    def test_position_export_uses_kicad_side_names(self):
        captured = {}

        def fake(cli, arguments, cwd):
            captured["arguments"] = arguments
            Path(arguments[arguments.index("-o") + 1]).write_text(
                positions_csv([position("R1")]), encoding="utf-8")
            return ""

        with mock.patch.object(jlc, "run_cli", side_effect=fake):
            for side, expected in (("top", "front"), ("bottom", "back"), ("both", "both")):
                jlc.read_positions("kicad-cli", Path("board.kicad_pcb"), Path("/tmp"), side)
                self.assertEqual(captured["arguments"][captured["arguments"].index("--side") + 1], expected)
                self.assertIn("--use-drill-file-origin", captured["arguments"])

    def test_gerber_layers_are_listed_explicitly(self):
        captured = {}

        def fake(cli, arguments, cwd):
            target = Path(arguments[arguments.index("-o") + 1])
            if arguments[:3] == ["pcb", "export", "gerbers"]:
                captured["arguments"] = arguments
                for name in GERBER_NAMES:
                    (target / name).write_text("G04 mock*\n", encoding="utf-8")
            else:
                (target / "board-PTH.drl").write_text("M48\n", encoding="utf-8")
            return ""

        with tempfile.TemporaryDirectory() as directory:
            board, _ = write_project(directory, [footprint("R1")])
            data = jlc.read_board(board)
            workdir = Path(directory) / "work"
            workdir.mkdir()
            with mock.patch.object(jlc, "run_cli", side_effect=fake):
                jlc.plot_gerbers("kicad-cli", board, data, workdir)
        layers = captured["arguments"][captured["arguments"].index("--layers") + 1]
        self.assertEqual(layers.split(",")[:4], ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
        self.assertIn("Edge.Cuts", layers)


class EndToEndTest(unittest.TestCase):
    """Full export with a fake kicad-cli: no KiCad installation required."""

    def run_export(self, *extra):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        project = Path(directory) / "project"
        project.mkdir()
        output = Path(directory) / "out"
        footprints = [
            footprint("R1", value="10k", at=(105.0, 132.0, 0.0),
                      fields={"LCSC": "C25744", "MPN": "0402WGF1002TCE"}),
            footprint("C1", value="100n", lib="Test:C", at=(100.0, 135.0 - 1.0, 90.0)),
            footprint("J2", value="pads", pads=[TH_PAD],
                      attr=("through_hole", "exclude_from_bom", "exclude_from_pos_files")),
        ]
        board, _ = write_project(project, footprints)
        netlist = netlist_text([
            ("R1", "10k", "Test:R", {"LCSC": "C25744", "MPN": "0402WGF1002TCE"}, False),
            ("C1", "100n", "Test:C", {"LCSC": "C1525", "MPN": "CL05B104KO5NNNC"}, False),
            ("J2", "pads", "Test:J", {}, True),
        ])
        positions = positions_csv([position("R1", x=5.0, y=3.0),
                                   position("C1", x=0.0, y=1.0, rotation=90.0)])
        fake = fake_cli(GERBER_NAMES, netlist, positions)
        with mock.patch.object(jlc, "run_cli", side_effect=fake), \
                mock.patch.object(jlc, "kicad_version", return_value="mock"):
            code = jlc.main([str(project), "--output", str(output), *extra])
        self.assertEqual(code, 0)
        return output

    def test_export_writes_valid_artifacts(self):
        output = self.run_export()
        self.assertEqual(sorted(path.name for path in output.iterdir()),
                         ["bom.csv", "export-report.json", "gerber.zip", "pick_and_place.csv"])

        with (output / "bom.csv").open(newline="") as handle:
            bom = list(csv.DictReader(handle))
        self.assertEqual([row["LCSC Part #"] for row in bom], ["C1525", "C25744"])
        self.assertEqual(bom[0]["Comment"], "100n")
        self.assertEqual(bom[0]["MPN"], "CL05B104KO5NNNC",
                         "a part number stored only on the schematic must still be exported")

        with (output / "pick_and_place.csv").open(newline="") as handle:
            cpl = list(csv.DictReader(handle))
        self.assertEqual([(row["Designator"], row["Mid X"], row["Mid Y"], row["Rotation"])
                          for row in cpl], [("C1", "0.0000", "1.0000", "90.00"),
                                            ("R1", "5.0000", "3.0000", "0.00")])
        self.assertTrue(all(row["Layer"] == "Top" for row in cpl))

        with zipfile.ZipFile(output / "gerber.zip") as archive:
            names = archive.namelist()
            self.assertIsNone(archive.testzip())
        self.assertEqual(sorted(names), sorted(GERBER_NAMES + ["board-PTH.drl", "board-NPTH.drl"]))
        self.assertTrue(all("/" not in name for name in names))

        report = json.loads((output / "export-report.json").read_text())
        self.assertEqual(report["assembly"]["selected"], 2)
        self.assertEqual(report["assembly"]["skipped"][0]["reference"], "J2")
        self.assertFalse(report["manufacturing_release"])
        self.assertEqual(report["board"]["aux_origin_mm"], [100.0, 135.0])
        self.assertEqual(sorted(report["artifacts"]), ["bom.csv", "gerber.zip", "pick_and_place.csv"])

    def test_second_run_refuses_to_overwrite_without_the_flag(self):
        output = self.run_export()
        with mock.patch.object(jlc, "run_cli", side_effect=AssertionError("kicad-cli ran")), \
                mock.patch.object(jlc, "kicad_version", return_value="mock"):
            code = jlc.main([str(output.parent / "project"), "--output", str(output)])
        self.assertEqual(code, 1, "existing artifacts must not be replaced silently")

    def test_require_part_numbers_fails_when_a_number_is_missing(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        project = Path(directory) / "project"
        project.mkdir()
        write_project(project, [footprint("R1", at=(100.0, 135.0, 0.0))])
        fake = fake_cli(GERBER_NAMES, netlist_text([("R1", "10k", "Test:R", {}, False)]),
                        positions_csv([position("R1", x=0.0, y=0.0)]))
        err = io.StringIO()
        with mock.patch.object(jlc, "run_cli", side_effect=fake), \
                mock.patch.object(jlc, "kicad_version", return_value="mock"), \
                contextlib.redirect_stderr(err):
            code = jlc.main([str(project), "--output", str(Path(directory) / "out"),
                             "--require-part-numbers"])
        self.assertEqual(code, 1)
        self.assertIn("no JLCPCB/LCSC part number for: R1", err.getvalue())
        self.assertFalse((Path(directory) / "out" / "bom.csv").exists(),
                         "nothing is published when the export fails")


@unittest.skipUnless(os.environ.get("JLC_INTEGRATION") == "1", "set JLC_INTEGRATION=1 to run")
class IntegrationTest(unittest.TestCase):
    """Run the real exporter against this repository's board with the installed KiCad."""

    def test_repository_board(self):
        with tempfile.TemporaryDirectory() as directory:
            code = jlc.main([str(ROOT / "PCB" / "main"), "--output", directory])
            self.assertEqual(code, 0)
            report = json.loads((Path(directory) / "export-report.json").read_text())
            self.assertEqual(report["assembly"]["selected"], 46)
            self.assertEqual(report["assembly"]["missing_part_numbers"], [])
            self.assertEqual(report["board"]["copper_layers"], ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
            with (Path(directory) / "bom.csv").open(newline="") as handle:
                bom = list(csv.DictReader(handle))
            self.assertEqual(sum(int(row["Quantity"]) for row in bom), 46)
            with (Path(directory) / "pick_and_place.csv").open(newline="") as handle:
                cpl = list(csv.DictReader(handle))
            self.assertEqual(len(cpl), 46)
            bom_refs = {ref for row in bom for ref in row["Designator"].split(", ")}
            self.assertEqual(bom_refs, {row["Designator"] for row in cpl})
            with zipfile.ZipFile(Path(directory) / "gerber.zip") as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
            self.assertTrue(any(name.endswith(".drl") for name in names))
            self.assertTrue(all("/" not in name for name in names))

    def test_repository_board_single_side(self):
        with tempfile.TemporaryDirectory() as directory:
            code = jlc.main([str(ROOT / "PCB" / "main"), "--output", directory, "--side", "top"])
            self.assertEqual(code, 0)
            with (Path(directory) / "pick_and_place.csv").open(newline="") as handle:
                cpl = list(csv.DictReader(handle))
            self.assertEqual(len(cpl), 46)
            self.assertTrue(all(row["Layer"] == "Top" for row in cpl))


if __name__ == "__main__":
    unittest.main()
