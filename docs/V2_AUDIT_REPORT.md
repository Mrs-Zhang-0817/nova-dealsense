# V2.0 基线审计 · 2026-11-09
**结论：保留 V1.1 的交易计算与历史记录，新增独立的询盘和授权生命周期。** 自动抽取可以生成草稿，只有人工批准的固定版本才能进入正式交易或发送流程。

## 证据范围
本轮核对源码、测试实现、已执行的发布验收、数据库目录和本机 GET 接口。冻结包 SHA-256 为 `5cc372e1a47598ba97cc854237c77bee5267b8836b819d1c03b3ca9f35a672e7`；包内 101 个 source 文件与工作目录逐字节一致。原目录无 Git，在本地建立基线 v1.1-baseline（cb04591）及 audit/v2-phase-0 分支。未纳入 .env、数据库备份或生成的 PDF。
本轮只读数据库事务确认 0005、11 张业务表及 alembic_version；GET health、markets、dashboard、deals?page_size=1 实测均为 200。其余“已验证”依据同一源码版本以前的实际运行：14 个后端测试、Edge 三条业务流程和发布包洁净安装。最终验收报告见 [FINAL_RELEASE_REPORT.md](FINAL_RELEASE_REPORT.md)。本轮未重跑写入型测试或调用外部业务服务。

## 工程目录与职责
|位置|实际内容及边界|
|---|---|
|frontend/app|根 layout/page，deals 的 layout、列表、new、[id] 详情、edit、scenarios；optimizer 和 reports/[id]。订单分析在详情锚点，无独立分析路由。|
|frontend/components、services|workspace、decision-dashboard、deal-form、ui/button；api.ts 检查健康，deals.ts 封装 fetch、状态和金额显示。缺少统一领域类型和页面权限边界。|
|frontend/messages、styles、lib|中英字典、global.css、deals/orders.css、类名工具；hooks/types 为占位。业务页面大部分中文直接写在组件。|
|前端构建|package.json、package-lock、tsconfig、Tailwind/PostCSS 配置、components.json；App Router、React、TypeScript。依赖清单有 ECharts，当前对比页图示使用 meter。|
|backend/app|main 注册路由、错误处理及 CORS；core 配置和数据库会话；api 有 health/business/optimizer/decisions；schemas 有 deals/optimization；models 有 market/business/optimization/decision；services/finance.py、optimization/engine.py、reports/decision.py 与 pdf.py 分别计算、求解、冻结报告和排版。parsers 为占位。|
|数据库与运行时|alembic.ini、migrations/env.py、生成模板与 0001–0005；requirements、测试依赖、Windows 锁文件；maintenance.py 备份恢复，rehearse.py 隔离环境演练。|
|测试|backend/tests 中 test_api、finance、optimizer、optimizer_api、decisions、dashboard 六个模块。frontend/tests 中 orders、optimizer、decisions、release-review 四个 Edge 脚本。|
|环境和部署|.env.example 提供数据库、AI、上传、前端基址等示例；实际 Settings 读取 app_name、database_url、frontend_origin。仅 NEXT_PUBLIC_API_BASE_URL 供浏览器用。scripts/start、verify、backup、restore 为 PowerShell；seed_demo.py 与 package_release.py 准备数据与发布包。Compose 配 PostgreSQL 16 和后端，实际发布演练用 Windows PostgreSQL 18.6。|
|资料与产物|README、docs 中需求/架构/数据库/优化/决策/排期、演示脚本、亮点、安全、Windows、提交及最终验收说明；sample_data 两份 JSON；submission、提交 ZIP、release-backups、output 为交付物；.local、.venv 及 node_modules 是本地环境。|

## 能力与验证矩阵
接口均相对 /api/v1；“目录 CRUD”指集合 GET/POST 和单项 GET/PUT/DELETE。
|能力及状态|前端 / 后端|数据及接口|验证与限制|
|---|---|---|---|
|看板：已实现且验证|decision-dashboard / decisions.dashboard|deals、deal_items、runs、selections、reports；GET /dashboard|test_dashboard、release-review；按来源和币种汇总；来源标签不构成权限。|
|市场：已实现且验证|deal-form / business|markets；GET /markets、/markets/{code}|test_api、orders；CN、US 主数据可用，rules_status 不代表法规覆盖。|
|买家与商品：接口已验证，管理 UI 部分实现|表单内联新增或选择 / business.catalog|buyers、products；/buyers、/products 目录 CRUD|test_api；缺少独立情报、批量目录和匹配审核页面。|
|订单管理：已实现且验证|deals 系列页面 / business.persist、detail、listing|deals、buyers、markets、items、costs、constraints；/deals CRUD|test_api、orders；按目的地/状态筛选、分页、快照和事务有效；列表与编辑无用户级隔离。|
|财务：已实现且验证|详情分析 / finance.calculate|行成本、confirmed、included、订单汇率；GET /deals/{id} 返回 financials|test_finance；缺汇率报错、零收入贡献率为空；贡献利润不涵盖企业全部费用。|
|反向优化：已实现且验证|optimizer / optimizer.py、engine.py|runs、scenarios；POST /deals/{id}/optimize，GET /optimization/{id}、/scenarios（运行子资源）、/deals/{id}/optimization-history|test_optimizer、test_optimizer_api、optimizer.cjs；三个策略、三态、复算和截断均有覆盖。单商品、1000 候选，未映射硬约束阻止推荐。|
|对比与人工选择：已实现且验证|deals/[id]/scenarios / decisions|scenarios、selections；GET /optimization/{id}/comparison，POST/GET /deals/{id}/decisions，GET /decisions/{id}|test_decisions、decisions.cjs；拒绝跨单或不可行选择，改选追加。selected_by 不能证明身份。|
|报告：已实现且验证|reports/[id] / reports、decisions|decision_reports；POST/GET /deals/{id}/reports，GET /reports/{id}、/reports/{id}/download|test_decisions、Edge；改价和重启后报告不变。含买家信息，下载接口需补授权。|
|Windows 发布恢复：本机已验证，跨机未充分验证|生产 Next.js、Uvicorn、PostgreSQL、脚本|Alembic；GET /health 仅代表 API 存活|同机新依赖环境、隔离库恢复 11 表、启动及 PDF 已验收；第二台实机、Docker 部署未实测。|
|国际化：部分实现|workspace 字典及语言切换|业务标识为英文|首页中英曾经 Edge 验证；表单、报告、错误及邮件文本没有完整双语链路。|
|V2 接入与审批：未实现|无 Inbox、邮件回调、上传解析、后台 worker、抽取、外部情报、审批、Reply Studio|无配套表/API/集成测试|配置示例和空目录不能证明能力；演示数据是人工输入。|

## 按优先级处理的风险
1. **阻断真实数据接入**：无认证、租户和对象授权，知道 UUID 可访问报告。先建立角色和订单/附件/历史授权；用双租户负向测试验证。单机 CORS 不能承担认证。
2. **阻断自动发送**：既有 POST /deals 可直接建单，人工选择记录可自由填名。必须把建单命令与发件命令分别绑定操作者、版本及审批，封住旧路由绕行；发送结果不明时先对账。
3. **数据迁移与隐私**：JSON 与 PDF 可能固化买家个人信息；旧库缺少历史所属租户。隔离旧记录后核权。备份工具只接受 0005 和同 PostgreSQL 主版本，迁移前先做双版本恢复演练。
4. **同步计算与查询**：优化请求同步枚举并写入全部结果；对比接口读取整次运行，目录列表无分页，优化页可拉取全部订单；PDF bytes 存库增大备份。先测 SQL 执行计划、响应大小、候选上限和恢复时长，再决定索引、分页和后台化。
5. **工程与运维**：大页面直接 fetch、局部无严格响应类型；来源标注、财务事实与 AI 建议应有不同的 UI 表达。Windows 中文路径和字体有已知环境依赖。前端 PostCSS 有兼容覆盖；锁版本审计在 V1.1 发布时完成，新增解析/AI SDK 时需重新审计。
6. **外部信息**：邮箱授权、供应商配额、可信来源和授权范围未取得；公司同名、政策失效和 AI 注入可导致错配。每项证据记录来源、时间、适用范围、冲突/过期状态，缺失允许流程进入待人工补充。
