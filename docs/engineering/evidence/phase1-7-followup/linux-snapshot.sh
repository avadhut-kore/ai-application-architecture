set -eu
python -m pip install --quiet uv==0.13.9
python - <<'COPY'
from pathlib import Path
import shutil,hashlib,json,os
source=Path('/repo');target=Path(os.environ['VALIDATION_SOURCE'])
records=[]
for name in json.loads((source/'.venv/linux-snapshot-files.json').read_text(encoding='utf-8')):
 path=source/name
 if not path.is_file():continue
 destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
 data=path.read_bytes();destination.write_bytes(data)
 digest=hashlib.sha256(data).hexdigest();assert digest==hashlib.sha256(path.read_bytes()).hexdigest(),name
 records.append({'path':name,'sha256':digest})
(source/'.quality/followup-linux-source-copy.json').write_text(json.dumps(records,indent=2))
print('Verified Git-visible native source snapshot:',len(records),'files',flush=True)
COPY
cd "$VALIDATION_SOURCE"
export UV_PROJECT_ENVIRONMENT=/validation/venv
export UV_CACHE_DIR=/validation/cache
export QUALITY_OUTPUT=/repo/.quality-followup-linux
python --version
uv sync --frozen
uv run --frozen python scripts/validate.py
uv run --frozen python scripts/quality.py
