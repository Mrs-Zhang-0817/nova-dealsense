# Phase 1 后端准备审计
2026-11-12 基于 audit/v2-phase-0 的 FastAPI 实例、路由处理器、SQLAlchemy 模型和测试实现。frontend/v2-design 是独立 worktree。本轮交付只涉及文档。下表的“历验”表示 V1.1 发布时真实 Edge、隔离库和 PDF 验收，本轮实际检查见末节。

|能力|完成度与代码证据|V2 接入判断|
|---|---|---|
|Deal Management|已实现。business.catalog、persist、detail、listing 支持事务内新增及全量替换、查询筛选、分页。test_api 历验重启与修改。|旧手工订单流程可用；询盘转订单必须经服务端版本审批，不能直接把 AI 输出 POST 到原路由。|
|Product & Cost|已实现商品 CRUD 和订单内成本维护。models/business 的 Product、DealItem、CostItem 保存目录及成交快照。|可复用 SKU 与单位；企业目录批量管理、供应商报价、匹配候选未实现。成本没有独立 CRUD。|
|Financial Analysis|已实现。finance.calculate 统一处理销售、制造、已确认且纳入的附加成本和贡献利润。|直接读 financials，无独立 calculate API。已有水瓶用例和零收入边界。|
|Exchange Rate Snapshots|已实现每单汇率数组，汇率、方向、日期和来源随运行冻结；test_finance 覆盖双向折算及缺失汇率。|不是汇率供应商服务或独立历史表；UI 可展示与人工录入。|
|Reverse Optimization|已实现。engine.evaluate 有 3 种目标、约束检查和截断标志。|单商品和 1000 候选边界保留；资料不足应展示原因。|
|Optimization Scenarios|已实现，Scenario.result 按 position 存储，可分页读取；test_optimizer_api 覆盖复算。|原始结果和具 ID 的对比行需区分。|
|Scenario Comparison|已实现，decisions.comparison 与 reports.decision.present 补充解释、产能占用和可选 UUID。|同步返回整次运行；候选很多时需分页/摘要适配。|
|Decision Selection|已实现追加选择，核对 deal/run/scenario 归属和可行性；test_decisions 有拒绝案例。|偏好选择可复用；当前无审批者认证、租户和发送授权。|
|Decision Reports|已实现中文八节快照、持久 PDF 字节、按订单列表与下载；历史验收验证编辑重启后一致。|可直接预览与下载；缺少全局索引、授权和多语言报价。|
|Overview Dashboard|已实现，decisions.dashboard 统计数据库值，按来源/币种分组。test_dashboard 测创建、改价和重启。|沿用统计定义，未提供待审询盘、证据时效或发送状态。|

**缺口与风险**：没有邮箱连接器、上传端点、文件解析、任务 worker、结构化抽取、企业背景/政策/产品监管证据、报价草稿及发件服务。parsers 只有占位文件。AI 密钥和上传目录仅是环境样例。v1 多数响应无正式模型；前端误用浮点、误读 422 或使用错方案 ID 容易造成联调错误。真实邮件接入前必须补资源级授权、原件访问和凭据隔离；发送需处理超时结果不明和重复提交。业务逻辑已验证部分继续复用。

**本轮测试**：从当前应用成功生成 OpenAPI。用 unittest discover 分别执行 test_finance.py 与 test_optimizer.py，5+5 全部通过。覆盖金额精度、零收入、缺失成本/汇率、反推报价、舍入后贡献率、客户上限、交期、三个目标、重复计费和截断。未对当前主库运行带写入/删除的 test_api、test_dashboard、test_decisions、test_optimizer_api。此前 14 项完整回归及 Edge 结果是历史证据，详见 FINAL_RELEASE_REPORT.md；本轮没有重新验收外部邮箱或 PDF。

运行环境探测：本轮连接已配置的 localhost:5432 超时，127.0.0.1:8000 的 /openapi.json、/api/v1/health、markets、dashboard 和订单列表未取得 HTTP 响应。因此本轮数据库清单来自 ORM 与迁移源码，契约来自本地导入的 app.openapi()；当前在线数据及端口联通性未通过验证。历史验收的 0005 和 HTTP 200 不作为本日结果。
