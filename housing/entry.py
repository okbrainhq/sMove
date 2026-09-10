"""Current screwless dispatcher. Legacy two-part generator remains historical only."""
import runpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
mode=sys.argv[1] if len(sys.argv)>1 else 'generate'
assert mode in ('generate','verify')
sys.path.insert(0,str(root/'scripts/r2/enclosure'))
# Both modes regenerate and run all geometric checks, with optional isolated wall sweep.
runpy.run_path(str(root/'scripts/r2/enclosure/screwless.py'),run_name='__main__')
