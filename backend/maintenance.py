"""Portable app-data backup and isolated restore for schema 0005 / same PostgreSQL major."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.core.database import Base
from app.models import market,business,optimization,decision

TABLES=[t.name for t in Base.metadata.sorted_tables]
URL=make_url(settings.database_url)
def connect(name=None,autocommit=False):
    url=URL.set(drivername="postgresql",database=name or URL.database)
    return psycopg.connect(url.render_as_string(hide_password=False),autocommit=autocommit)

def dump_table(conn,name,output=None):
    digest=hashlib.sha256()
    with conn.cursor().copy(sql.SQL("COPY (SELECT * FROM {} ORDER BY 1) TO STDOUT WITH (FORMAT binary)").format(sql.Identifier(name))) as stream:
        for chunk in stream:
            digest.update(chunk)
            if output is not None:output.write(chunk)
    return digest.hexdigest()

def backup(path):
    with connect() as c, ZipFile(path,"x",compression=ZIP_DEFLATED) as archive:
        c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        if c.execute("SELECT version_num FROM alembic_version").fetchone()[0]!="0005":
            raise ValueError("备份仅支持 0005 版本")
        manifest={"revision":"0005","server_major":c.info.server_version//10000,"tables":{}}
        for table in TABLES:
            with archive.open(table,"w") as file:
                manifest["tables"][table]=dump_table(c,table,file)
        archive.writestr("manifest.json",json.dumps(manifest))
    print("Backup complete:",len(TABLES),"tables",path)

def restore(path,name):
    if not re.fullmatch(r"nova_restore_[a-z0-9_]{1,42}",name) or name==URL.database:
        raise ValueError("仅可恢复到新的 nova_restore_ 数据库")
    with ZipFile(path) as archive,connect("postgres",True) as admin:
        m=json.loads(archive.read("manifest.json"))
        if set(m["tables"])!=set(TABLES) or m["revision"]!="0005" or m["server_major"]!=admin.info.server_version//10000:
            raise ValueError("备份版本或表清单不兼容")
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        # Run migrations in a child with the isolated connection, before loading any data.
        import os,sys,subprocess
        env=dict(os.environ,DATABASE_URL=URL.set(database=name).render_as_string(hide_password=False))
        subprocess.run([sys.executable,"-m","alembic","upgrade","0005"],env=env,cwd=Path(__file__).parent,check=True)
        with connect(name) as c:
            c.execute("DELETE FROM markets")  # only seeds of the database just created
            for table in TABLES:
                with archive.open(table) as source,c.cursor().copy(sql.SQL("COPY {} FROM STDIN WITH (FORMAT binary)").format(sql.Identifier(table))) as copy:
                    while chunk:=source.read(1024*1024):copy.write(chunk)
                if dump_table(c,table)!=m["tables"][table]:
                    raise ValueError("恢复内容校验失败："+table)
    print("Restore verified:",len(TABLES),"table digests match in",name)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["backup","restore"])
    parser.add_argument("archive",type=Path)
    parser.add_argument("database",nargs="?")
    args=parser.parse_args()
    if args.mode=="backup":backup(args.archive)
    else:restore(args.archive,args.database or "")
