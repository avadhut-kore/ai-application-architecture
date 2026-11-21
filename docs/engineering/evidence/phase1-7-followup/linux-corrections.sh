set -eu
python - <<'COPY'
from pathlib import Path
import json,hashlib
source=Path('/repo');target=Path('/validation/source-followup-765b37c281')
records=json.loads((source/'.quality/followup-linux-source-copy.json').read_text())
changed=[]
for record in records:
 path=source/record['path']
 if path.is_file():
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  if digest!=record['sha256']:
   (target/record['path']).write_bytes(path.read_bytes())
   record['sha256']=digest;changed.append(record['path'])
(source/'.quality-followup-linux/final-source-patches.json').write_text(json.dumps({'changed_paths':changed,'final_hashes':records},indent=2))
print('Verified final source patches:',changed,flush=True)
COPY
cd /validation/source-followup-765b37c281
export QUALITY_OUTPUT=/repo/.quality-followup-linux-static
/validation/venv/bin/python scripts/quality.py --static-only
/validation/venv/bin/python -m unittest discover -s platform/mcp-adapter/tests -t platform/mcp-adapter
