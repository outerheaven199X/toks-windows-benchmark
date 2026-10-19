"""Download the exact public evidence ZIP, verify it, and extract safely."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import tempfile
import urllib.request
import zipfile

URL = 'https://huggingface.co/spaces/b4ph/toks-windows-benchmark/resolve/main/downloads/TOKS_VS_HF_WINDOWS_V2_PUBLIC_2026-10-18.zip'
SHA256 = '716833fe83e11ed15d831c3f4d11bfed971be50c1553bae479cb55687fd956f1'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('evidence/run'))
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists():
        parser.error('output already exists; choose a new directory')
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / 'evidence.zip'
        urllib.request.urlretrieve(URL, archive)
        with archive.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != SHA256:
            raise SystemExit('SHA-256 mismatch; nothing extracted')
        with zipfile.ZipFile(archive) as zipped:
            for entry in zipped.infolist():
                name = PurePosixPath(entry.filename)
                if name.is_absolute() or '..' in name.parts or '\\' in entry.filename or ':' in entry.filename:
                    raise SystemExit('unsafe archive path; nothing extracted')
                if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    raise SystemExit('symlink in archive; nothing extracted')
                if not (target / entry.filename).resolve().is_relative_to(target):
                    raise SystemExit('path escapes destination; nothing extracted')
            if zipped.testzip() is not None:
                raise SystemExit('ZIP CRC failure; nothing extracted')
            zipped.extractall(target)
    print('Verified SHA-256 and ZIP CRC; extracted to', target)

if __name__ == '__main__':
    main()
