"""Isolated KiCad project copies, read-only source handling and authoritative checks."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import pcbnew as p


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def clone_project(source, directory):
    source=Path(source).resolve(); directory=Path(directory).resolve()
    if directory==source.parent: raise ValueError('Output must be an isolated directory')
    directory.mkdir(parents=True,exist_ok=True)
    output=directory/source.name
    if output.exists(): raise FileExistsError(output)
    for f in source.parent.iterdir():
        if f.suffix in ('.kicad_pro','.kicad_dru','.kicad_sch','.kicad_sym') or f.name in ('fp-lib-table','sym-lib-table'):
            shutil.copy2(f,directory/f.name)
        elif f.is_dir() and f.suffix=='.pretty':
            shutil.copytree(f,directory/f.name,dirs_exist_ok=True)
    shutil.copy2(source,output)
    (directory/'source.json').write_text(json.dumps({'source':str(source),'sha256':digest(source)},indent=2)+'\n')
    return output

def save(board, output, fill=True):
    output=Path(output)
    # pcbnew may rewrite the project's defaults when saving. Never keep that change.
    pro=output.with_suffix('.kicad_pro'); raw=pro.read_bytes() if pro.exists() else None
    try:
        if fill: board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones())
        p.SaveBoard(str(output),board)
    finally:
        if raw is not None: pro.write_bytes(raw)

def drc(board_path, report=None, parity=False):
    board_path=Path(board_path)
    report=Path(report) if report else board_path.parent/'drc.json'
    cmd=['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(report)]
    if parity: cmd+=['--schematic-parity']
    subprocess.run(cmd+[str(board_path)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return json.loads(report.read_text())

def counts(report):
    return {'errors':sum(v['severity']=='error' for v in report['violations']),
            'warnings':sum(v['severity']=='warning' for v in report['violations']),
            'unconnected':len(report['unconnected_items']),
            'parity':len(report.get('schematic_parity',[]))}
