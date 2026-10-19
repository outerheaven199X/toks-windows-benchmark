param([Parameter(Mandatory=$true)][string]$Python)
$ErrorActionPreference = 'Stop'
$wheel = Join-Path $PSScriptRoot 'wheels\toks-0.3.2-cp312-cp312-win_amd64.whl'
if ((Get-FileHash -LiteralPath $wheel -Algorithm SHA256).Hash.ToLower() -ne 'c15cc2b01b861d26c00d1366e44db0b900df1e9eb65574a4a8330dd4ff7c0c76') { throw 'Wheel SHA-256 mismatch' }
& $Python (Join-Path $PSScriptRoot 'verify_runtime.py') --python-only
if ($LASTEXITCODE) { throw 'Unsupported Python' }
$environment = Join-Path $PSScriptRoot '.venv'
if (Test-Path -LiteralPath $environment) { throw 'Environment already exists; refusing to overwrite it.' }
& $Python -m venv $environment
if ($LASTEXITCODE) { throw 'Environment creation failed' }
$venvPython = Join-Path $environment 'Scripts\python.exe'
& $venvPython -m pip install --no-deps $wheel
if ($LASTEXITCODE) { throw 'Local wheel installation failed' }
& $venvPython -m pip install 'tokenizers==0.23.2'
if ($LASTEXITCODE) { throw 'Hugging Face tokenizer installation failed' }
& $venvPython (Join-Path $PSScriptRoot 'verify_runtime.py')
if ($LASTEXITCODE) { throw 'Installed extension hash mismatch' }
