"""Start/check only a dedicated rehearsal database. Credentials stay in child environment."""
import sys,os,re,subprocess
from maintenance import URL,connect
from psycopg import sql
from pathlib import Path

name,action=sys.argv[1:]
if not re.fullmatch(r"nova_(restore|demo)_[a-z0-9_]+",name) or name==URL.database:
    raise SystemExit("需要独立演练库")
env=dict(os.environ,DATABASE_URL=URL.set(database=name).render_as_string(hide_password=False),FRONTEND_ORIGIN="http://localhost:3011")
def run(*args):
    subprocess.run([sys.executable,*args],cwd=Path(__file__).parent,env=env,check=True)
if action=="create":
    with connect("postgres",True) as admin:admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    run("-m","alembic","upgrade","head")
elif action=="serve":
    run("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8011","--no-access-log")
elif action=="test":
    run("-m","unittest","discover","-s","tests","-v")
    run("-m","alembic","check")
else:raise SystemExit("使用 create / serve / test")
