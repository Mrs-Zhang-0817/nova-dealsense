# NOVA DealSense
面向制造出口商的多市场交易决策平台。首演路线为中国至美国，以反向交易优化寻找符合利润和经营约束的交易条件。第一阶段包含中文应用外壳、API 和市场数据基础。
## 产品与目录
规划模块包括交易总览、订单管理、订单智能分析、反向交易优化、交易方案对比、决策报告。
- frontend/ 包含 Next.js App Router、TypeScript、Tailwind、shadcn/ui 组件、ECharts 和中英字典。
- backend/ 包含 FastAPI、SQLAlchemy、Pydantic 及 Alembic 迁移。
- docs/ 存放需求、架构、数据设计和开发计划。sample_data/ 预留给演示样例。
## Windows 本地开发
安装 Node.js 22 LTS（含 npm）、Python 3.12（含 py 启动器）和 PostgreSQL 16 或以上版本，确保 psql 在 PATH 中。以下 PowerShell 命令从项目根目录开始，仅首次需要复制环境示例。
```powershell
Copy-Item .env.example .env
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm.cmd ci --prefix frontend
psql -U postgres -d postgres
```
在 psql 中执行以下 SQL，将开发角色密码与 .env 对齐。
```sql
CREATE USER "user" WITH PASSWORD 'password';
CREATE DATABASE nova_dealsense OWNER "user";
\q
```
后端读取根目录 .env。非本机环境应替换示例密码与 SECRET_KEY。DeepSeek 凭据可留空。修改浏览器 API 地址时，将 NEXT_PUBLIC_API_BASE_URL 单独写入 frontend/.env.local 并重启前端。
```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```
另开 PowerShell，从项目根目录启动前端。
```powershell
npm.cmd run dev --prefix frontend
```
打开 http://localhost:3000 查看连接状态。可切换 English。在第三个终端验证 API。
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
```
预期 success 为 true，message 为 NOVA DealSense API is running。
## Docker Desktop
启用 Linux 容器，在根目录创建 .env 后执行 `docker compose up --build -d`。数据库健康后后端执行迁移。前端仍按上述 npm 命令运行。
## 排错
- 连接被拒绝时先确认数据库服务及 5432 端口。认证失败时核对角色、密码和 DATABASE_URL，URL 中的特殊字符须编码。
- 页面显示连接失败时检查 8000 端口和 API 基址，用 localhost:3000 访问；更改端口须相应设置 FRONTEND_ORIGIN。
- PowerShell 禁止执行 npm.ps1 时使用 npm.cmd。找不到 alembic 时检查虚拟环境路径及当前目录是否为 backend。
- 容器初始用户及密码仅在首次初始化数据卷时应用。已有卷请在数据库内更新角色密码。

## 第二阶段 · 持久数据库与订单管理

本机 PostgreSQL 18 数据目录为 `%LOCALAPPDATA%\NOVA-DealSense\data`，相同主版本的运行时位于同级 runtime。原临时实例已停止并保留为第一阶段冷副本。不要同时在 5432 端口启动两个实例。新机器仍可按上文安装标准 PostgreSQL，或使用 Compose 中的具名卷。

在 PowerShell 查看状态和启动本机持久实例：
```powershell
$pgRoot = Join-Path $env:LOCALAPPDATA 'NOVA-DealSense'
$pgCtl = Join-Path $pgRoot 'runtime/bin/pg_ctl.exe'
& $pgCtl status -D "$pgRoot/data"
# 仅在未运行时执行
& $pgCtl start -D "$pgRoot/data" -l "$pgRoot/postgresql.log" -w
```
从项目目录启动：
```powershell
cd backend
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000 --no-access-log
```
另开终端在项目根目录运行 `npm.cmd run dev --prefix frontend`。打开 http://localhost:3000/deals 创建订单。已有商品请从列表中选择，新增 SKU 必须唯一。当前报告币种由订单指定。跨币种行必须填写日期、来源和方向明确的汇率。接口清单和输入格式见 http://localhost:8000/docs 。

### 备份和恢复
在后端停写后停止数据库，复制整个 data 目录到独立备份位置，再启动服务。仅使用相同 PostgreSQL 主版本恢复冷备份。以下命令在上面定义 pgRoot、pgCtl 的终端中运行：
```powershell
& $pgCtl stop -D "$pgRoot/data" -m fast -w
if ($LASTEXITCODE) { throw '停止失败，请勿复制' }
$backup = Join-Path $pgRoot ('backup-' + (Get-Date -Format yyyyMMdd-HHmmss))
Copy-Item -LiteralPath "$pgRoot/data" -Destination $backup -Recurse -ErrorAction Stop
& $pgCtl start -D "$pgRoot/data" -l "$pgRoot/postgresql.log" -w
```
恢复时先停库，保留当前 data，将备份复制到新的空目录，使用 pg_ctl start -D 指向该目录。验证 alembic current、市场列表和已知订单后再切换日常启动路径。启动失败时查看 postgresql.log，并检查端口占用和目录权限。

### 财务口径与验收
订单行的原币扩展金额为数量乘单价，制造成本同理。逐行按订单汇率换算，四舍五入保留 8 位小数；销售收入汇总所有销售行。计入总成本由已确认制造成本及已确认且纳入的附加费用组成。包装、物流、保险和其他费用独立分类。估算行保留原值和折算值，界面提示有待确认费用。贡献率为贡献利润除以收入，零收入返回 null。汇率以每一单位 base 对应的 quote 数量记录，订单保存历史汇率、日期和来源。

样例输入见 sample_data/bottle.json。可在空的演示目录数据集上 POST 至 /api/v1/deals；相同 SKU 已存在时应使用 product_id。执行后端验证：
```powershell
cd backend
../.venv/Scripts/python.exe -m unittest discover -s tests -v
```
浏览器验收脚本 frontend/tests/orders.cjs 使用 Playwright 和本机 Edge，要求 3000/8000 服务已启动。执行后保留一笔样例供查看。接口测试会清理其成功流程中创建的数据。


## 第三阶段 · 反向交易优化
先从 backend 执行 `../.venv/Scripts/python.exe -m alembic upgrade head`，按上文启动 API 和前端，打开 http://localhost:3000/optimizer 。选择单商品订单；价格及预算均用订单报告币种。原订单保持不变，每次运行都会追加独立历史记录。
水瓶样例可设置数量 5000 至 5000、数量步长 1、报价 3.00 至 3.07、报价步长 0.01、目标贡献率 0.25、最低利润 0。为演示交付约束，可手工输入总产能 5000、准备 1 天、日产 1000 件、运输 4 天和交期 10 天，运费沿用订单。这些是演示条件，实际业务需填写经确认的数据。将客户单价上限设为 3.00 可复现不可行结果。
搜索顺序、成本行为与排序规则详见 [优化模型](docs/OPTIMIZATION.md)。接口详情可在本机 /docs 查看。运行记录包含冻结的输入；scenarios 接口支持 offset 和 limit 分页，可回查未通过约束的候选。

## 第四阶段 · 方案对比与决策报告
后端新增 ReportLab 依赖。更新虚拟环境后执行 alembic upgrade head。Windows 默认使用本机宋体生成中文 PDF。订单详情可进入方案对比、决策记录和报告。详见 [演示步骤与报告口径](docs/DECISIONS.md)。


## V1.1 提交演练
首次部署优先阅读 [Windows 安装、备份与隔离恢复](docs/WINDOWS_RELEASE.md)，使用 scripts/start.ps1、verify.ps1 和 seed_demo.py。演示顺序见 [六分钟脚本](docs/DEMO_SCRIPT.md)，实现范围见 [技术亮点](docs/TECHNICAL_HIGHLIGHTS.md)。
