# Sube un modelo del proyecto a Hugging Face.
# Antes, UNA vez:  .venv\Scripts\hf.exe auth login   (token "Write" de https://huggingface.co/settings/tokens)
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\subir_hf.ps1 -Repo "usuario/robertuito-toxicidad-sv" -Version v3.6.0 [-EtiquetaAnterior v3.4.0] [-Publico]
#  -Version            carpeta de hf_export/ con README e inference_contract; los pesos salen de models/<Version>/manifest.json (o models/<Version>/semilla_*)
#  -EtiquetaAnterior   antes de subir, marca lo que hoy está en el repo con esa etiqueta (para no perder la versión anterior)
param([Parameter(Mandatory = $true)][string]$Repo, [string]$Version = "v3.6.0", [string]$EtiquetaAnterior = "", [switch]$Publico)
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"
$privado = if ($Publico) { "False" } else { "True" }
& .venv\Scripts\python.exe -c @"
import sys, json, pathlib
from huggingface_hub import HfApi
repo, ver, anterior, privado = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == 'True'
m = pathlib.Path('models') / ver; man = m / 'manifest.json'
comp = json.loads(man.read_text(encoding='utf-8'))['componentes'] if man.exists() else [ver]
dirs = sorted(d for c in comp for d in (pathlib.Path('models') / c).glob('semilla_*/modelo') if d.is_dir())
assert len(dirs) == 1, f'se esperaba un solo modelo y hay {len(dirs)}: {dirs}'
api = HfApi(); print('Usuario:', api.whoami()['name'], '| pesos:', dirs[0])
api.create_repo(repo, private=privado, exist_ok=True)
etiquetas = [r.name for r in api.list_repo_refs(repo).tags]
if anterior and anterior not in etiquetas:
    api.create_tag(repo, tag=anterior, tag_message=f'Versión {anterior}'); print('Etiquetado lo anterior como', anterior)
api.upload_folder(repo_id=repo, folder_path=str(dirs[0]), ignore_patterns=['training_args.bin'], commit_message=f'Modelo {ver}')
readme = pathlib.Path(f'hf_export/{ver}/README.md').read_text(encoding='utf-8').replace('USUARIO/robertuito-toxicidad-sv', repo)
api.upload_file(repo_id=repo, path_or_fileobj=readme.encode('utf-8'), path_in_repo='README.md', commit_message=f'Ficha del modelo {ver}')
api.upload_file(repo_id=repo, path_or_fileobj=f'hf_export/{ver}/inference_contract.json', path_in_repo='inference_contract.json', commit_message=f'Contrato de inferencia {ver}')
api.upload_file(repo_id=repo, path_or_fileobj='src/features/normalization.py', path_in_repo='normalization.py', commit_message='Normalizador v1.2')
if ver not in [r.name for r in api.list_repo_refs(repo).tags]: api.create_tag(repo, tag=ver, tag_message=f'Versión {ver}')
print('Listo:', f'https://huggingface.co/{repo}', '(privado)' if privado else '(público)')
"@ $Repo $Version $EtiquetaAnterior $privado
