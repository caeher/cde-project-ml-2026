# Sube un modelo del proyecto a Hugging Face.
# Antes, UNA vez:  .venv\Scripts\huggingface-cli.exe login   (pega tu token de https://huggingface.co/settings/tokens, con permiso "Write")
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\subir_hf.ps1 -Repo "tu_usuario/robertuito-toxicidad-sv" [-Version v3.4.0] [-Publico]
param([Parameter(Mandatory = $true)][string]$Repo, [string]$Version = "v3.4.0", [switch]$Publico)
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"
$modelo = (Get-ChildItem "models/$Version" -Directory -Filter "semilla_*" | Select-Object -First 1).FullName + "\modelo"
$privado = if ($Publico) { "False" } else { "True" }
& .venv\Scripts\python.exe -c @"
import sys, pathlib
from huggingface_hub import HfApi
repo, modelo, ver, privado = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == 'True'
api = HfApi(); print('Usuario:', api.whoami()['name'])
api.create_repo(repo, private=privado, exist_ok=True)
api.upload_folder(repo_id=repo, folder_path=modelo, ignore_patterns=['training_args.bin'], commit_message=f'Modelo {ver}')
readme = pathlib.Path(f'hf_export/{ver}/README.md').read_text(encoding='utf-8').replace('USUARIO/robertuito-toxicidad-sv', repo)
api.upload_file(repo_id=repo, path_or_fileobj=readme.encode('utf-8'), path_in_repo='README.md', commit_message='Ficha del modelo')
api.upload_file(repo_id=repo, path_or_fileobj=f'hf_export/{ver}/inference_contract.json', path_in_repo='inference_contract.json')
api.upload_file(repo_id=repo, path_or_fileobj='src/features/normalization.py', path_in_repo='normalization.py', commit_message='Normalizador v1.2')
print('Listo:', f'https://huggingface.co/{repo}', '(privado)' if privado else '(público)')
"@ $Repo $modelo $Version $privado
