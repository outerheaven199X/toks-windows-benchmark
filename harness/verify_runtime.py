import hashlib
import os
from pathlib import Path
import sys

if os.name != 'nt' or sys.version_info[:2] != (3, 12):
    raise SystemExit('Native Windows CPython 3.12 is required.')
if '--python-only' not in sys.argv:
    import toks
    import tokenizers
    actual = hashlib.sha256(Path(toks._toks.__file__).read_bytes()).hexdigest()
    if actual != '234f0c2c48a5a3a8dfab6edbb861348ed4f640ec6e2668ee104a6f061d76f522' or toks.__version__ != '0.3.2' or tokenizers.__version__ != '0.23.2':
        raise SystemExit('Audited native wheel / tokenizers==0.23.2 required.')
    print('Audited native toks extension and HF version verified.')
