"""Build a new submission directory, archive and independent source backup without overwriting."""
import hashlib,shutil,sys,re
from pathlib import Path
from zipfile import ZIP_DEFLATED,ZipFile
from datetime import datetime

root=Path(__file__).resolve().parents[1]
assets=Path(sys.argv[1]).resolve()
dest=root/"submission"
dest.mkdir(exist_ok=False)
source=dest/"source"
def copy(src,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,target)
blocked={".local",".env",".venv",".next",".git","__pycache__","node_modules"}
def include(rel):
    p=root/rel
    if p.is_file():copy(p,source/rel);return
    for f in p.rglob("*"):
        if f.is_file() and not blocked.intersection(f.relative_to(root).parts) and (f.suffix in {".py",".md",".json",".tsx",".ts",".css",".cjs",".js",".ps1",".mako"} or f.name==".gitkeep"):
            copy(f,source/f.relative_to(root))
for rel in ["README.md",".gitignore",".env.example","docker-compose.yml","backend/app","backend/tests","backend/migrations","backend/alembic.ini","backend/Dockerfile","backend/requirements.txt","backend/requirements-test.txt","backend/requirements-windows.lock","backend/maintenance.py","backend/rehearse.py","frontend/app","frontend/components","frontend/hooks","frontend/lib","frontend/messages","frontend/services","frontend/styles","frontend/tests","frontend/types","frontend/next-env.d.ts","frontend/components.json","frontend/package.json","frontend/package-lock.json","frontend/postcss.config.js","frontend/tailwind.config.js","frontend/tsconfig.json","docs","sample_data","scripts"]:
    include(rel)
for name,src in [("README.md","docs/SUBMISSION.md"),("PRODUCT_OVERVIEW.md","docs/PRD.md"),("DEMO_SCRIPT.md","docs/DEMO_SCRIPT.md"),("TECHNICAL_HIGHLIGHTS.md","docs/TECHNICAL_HIGHLIGHTS.md"),("deployment/WINDOWS.md","docs/WINDOWS_RELEASE.md"),("deployment/SECURITY.md","docs/SECURITY_REVIEW.md"),("demo_data/bottle.json","sample_data/bottle.json"),("demo_data/cases.json","sample_data/cases.json")]:
    copy(root/src,dest/name)
for name in ("dashboard","analysis","deals","optimizer","scenarios","report"):
    copy(assets/(name+".png"),dest/"screenshots"/(name+".png"))
copy(assets/"bottle-report.pdf",dest/"demo_data/bottle-report.pdf")
def archive(folder,path):
    with ZipFile(path,"x",ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file():z.write(f,f.relative_to(folder))
    with ZipFile(path) as z:
        if z.testzip():raise ValueError("归档校验失败")
for f in dest.rglob("*"):
    if not f.is_file():continue
    if blocked.intersection(f.relative_to(dest).parts) or (f.name.startswith(".env") and f.name!=".env.example") or f.suffix in {".log",".zip",".db",".pyc"}:
        raise ValueError("禁止发布："+f.name)
    if f.suffix not in {".pdf",".png"} and re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:sk-|ghp_)[A-Za-z0-9]{25,}",f.read_bytes()):
        raise ValueError("可能含凭据："+f.name)
files=[f for f in sorted(dest.rglob("*")) if f.is_file()]
(dest/"SHA256SUMS.txt").write_text("".join(hashlib.sha256(f.read_bytes()).hexdigest()+"  "+f.relative_to(dest).as_posix()+"\n" for f in files),encoding="utf8")
backups=root/"release-backups";backups.mkdir(exist_ok=True)
stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
archive(source,backups/("working-source-"+stamp+".zip"))
bundle=root/"submission-NOVA-DealSense-V1.1.zip"
archive(dest,bundle)
print(len(files),"files checked;",bundle.stat().st_size,"bytes;",hashlib.sha256(bundle.read_bytes()).hexdigest())
