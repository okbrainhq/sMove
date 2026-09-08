"""R2-only dispatch compatible with the unchanged pinned scripts/freecad/run.py."""
import runpy
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
script=sys.argv[1] if len(sys.argv)>1 else 'generate'
assert script in ('generate','verify')
sys.path.insert(0,str(root/'scripts/r2/enclosure'))
runpy.run_path(str(root/'scripts/r2/enclosure'/f'{script}.py'),run_name='__main__')
