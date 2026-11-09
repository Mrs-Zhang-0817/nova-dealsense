# Windows 离线演示准备与恢复
从发布包解压后进入 source（从项目开发目录运行时即 nova-dealsense）。需要 Windows x64、Python 3.12、Node.js 22 LTS 或兼容新版、npm、PostgreSQL 18 及中文字体。首次联网安装依赖；现场使用已构建的本机服务。下列命令按 PowerShell 书写。
1. 安装并启动 PostgreSQL，选择持久数据目录。用管理员账户连接 psql，执行 `CREATE ROLE nova_app LOGIN PASSWORD '在此设置本机密码';` 与 `CREATE DATABASE nova_dealsense OWNER nova_app;`。不要重复创建已有数据库。记录备份与数据库主版本。
2. 复制环境示例，仅在本机 .env 设置实际 DATABASE_URL。URL 中用户名与密码的特殊字符须百分号编码。SECRET_KEY 替换示例值，AI 密钥留空即可。不要把根目录 .env 复制到 frontend。跨域仅允许 FRONTEND_ORIGIN，默认 http://localhost:3000。浏览器只需要 NEXT_PUBLIC_API_BASE_URL，改 API 端口必须重新构建。上传、AI 和 SECRET_KEY 是预留配置；应用当前无上传入口和账号认证。
3. 在源码根目录执行：
```powershell
Copy-Item .env.example .env   # 仅首次，已有配置请保留
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-windows.lock
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
```
4. 分别在两个终端从源码根目录执行 `./scripts/start.ps1 api` 和 `./scripts/start.ps1 web`。API 启动前执行 alembic upgrade head。停止时在各自终端按 Ctrl+C；数据库由 Windows 服务管理器或原 pg_ctl 管理。执行 `./scripts/verify.ps1`。打开 http://localhost:3000 并选择演示数据。
5. 对专用演示库运行 `.\.venv\Scripts\python.exe scripts/seed_demo.py`。脚本仅访问本机 API，根据固定演示名称和来源复用已有订单。新环境生成的 UUID 不同，应从订单列表进入。PDF 字节保存在 PostgreSQL，可从报告页下载至任意用户选择的位置。Windows 使用系统宋体，可用 REPORT_CJK_FONT 指向有嵌入许可的本机中文 TrueType 字体。
## 备份与隔离恢复
从源码根目录执行以下命令，备份目录需存在且可写。归档包含买家及报告数据，限本机保存或按业务要求加密保管。
```powershell
./scripts/backup.ps1 -Archive D:/backups/nova-20261109.zip
./scripts/restore.ps1 -Archive D:/backups/nova-20261109.zip -Database nova_restore_review01
```
备份在一致性只读事务内读取 0005 版全部业务表，按主键排序，使用 PostgreSQL 二进制 COPY 保存 JSON、NUMERIC、UUID 和 PDF。已有备份同名即失败。恢复要求同一 PostgreSQL 主版本、创建数据库权限和全新 nova_restore_ 名称。在新库运行迁移后仅移除刚生成的种子市场，按外键顺序导入并逐表核对摘要；校验失败回滚本次导入，保留原数据库。日常运行账户无需 CREATEDB；可在单独的管理员终端用 DATABASE_URL 临时指定有权限的维护角色。归档范围为应用数据，不含数据库用户、权限及服务器配置。需要集群级备份可采用 README 的停库冷备方案。
## 提交机检查
确认磁盘可写、端口空闲；构建退出码为 0；迁移为 0005；CN、US 可见；来源筛选正确；运行水瓶样例；下载后打开 PDF 核对中文；重启 API 后复查同一报告。不要在真实业务库运行写入型验收。无第二台 Windows 实机时，将跨机器安装列为待验证。
