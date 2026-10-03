"""Historical curve discovery runs at startup/background, never in a list GET."""
import json
from src.workbench.queries.data_index import connection
from src.workbench.storage import digest
from src.common import inside

def rebuild(root):
    folders={p.parent for pattern in ('results.csv','results.png') for p in (root/'runs').rglob(pattern) if 'workbench' not in p.relative_to(root/'runs').parts}
    value={'legacy_'+digest(p.relative_to(root).as_posix())[:20]:p.relative_to(root).as_posix() for p in sorted(folders)}
    with connection(root) as con:con.execute("INSERT OR REPLACE INTO query_meta(name,value) VALUES('legacy_curves',?)",(json.dumps(value),))

def sources(root):
    with connection(root) as con:row=con.execute("SELECT value FROM query_meta WHERE name='legacy_curves'").fetchone()
    return {key:inside(value,root) for key,value in json.loads(row[0]).items()} if row else {}
