# 页面映射与交互边界
表中“新”均为提案。沿用深色主题、表单控件及订单报告币种；可复用元素在对应行列明。所有 API 路径省略版本前缀，既有为 v1，建议新增为 v2。默认简中，集中维护中英词条；用户语言、原文语言、回复语言独立设置。

|目标页（建议路径）|复用现状|要改的交互|新组件|接口与实体|
|---|---|---|---|---|
|Overview /|workspace、decision-dashboard、GET /dashboard|导航按工作阶段；演示来源与真实租户隔离|待处理询盘、审批、失败任务入口|新 GET /overview；旧 deals/runs/selections/reports，新 inquiries/jobs/approvals|
|Deal Inbox /inbox|列表筛选样式、api 客户端|将正式订单与未批准询盘明确区分|并列邮箱/文件入口、原文与字段证据、任务状态|新 GET /inquiries、POST /uploads、POST /mailboxes/{id}/sync；inquiries/messages/assets/extractions|
|Company Intelligence /companies/[id]|buyer 的公司名、国家和联系人|买家选择须先确认同名主体|企业档案、域名匹配、证据与复查日期|旧 /buyers；新 GET /companies/{id}/evidence、POST /companies/{id}/research；buyers/company_profiles/evidence|
|Product Intelligence /products|商品目录 API、订单行快照|将内联选择扩展为规格单位对照|别名、成本报价、候选匹配确认|旧 /products；新 POST /inquiries/{id}/matches、PUT /matches/{id}；products/product_aliases/supplier_quotes/product_matches|
|Market Intelligence /markets/[code]|市场中英文名、启用状态|国家概览与具体贸易路径分开|政策与产品规定、HS/生效日过滤、覆盖缺口|旧 /markets；新 GET /market-rules、POST /research-jobs；markets/market_rules/evidence|
|Deal Analysis /deals/[id]、询盘提案预览|deal-form、订单明细、finance.calculate|正式建单按钮改为提案审核；历史订单保持可读|原文与更正差异、缺失项、审批回执|旧 /deals/{id}；新 GET /proposals/{id}、POST /proposals/{id}/approve；deals/deal_items/cost_items/proposals/approvals|
|Deal Optimizer /optimizer|约束表单、三策略、历史与截断状态|从选定订单版本进入；区分原始条件与情报建议|证据采用记录、缺失输入引导|旧 POST /deals/{id}/optimize、GET /optimization/{id}；optimization_runs/scenarios/evidence|
|Decision Center /decisions|方案对比、解释与选择历史|区分偏好选择、建单批准和发送批准|待审队列、版本差异、退回理由、审批者身份|旧 /optimization/{id}/comparison、/deals/{id}/decisions；新 GET /approvals、POST /proposals/{id}/reject；decision_selections/approvals|
|Reply Studio /replies/[id]|已选方案、报告链接和金额展示|收件人、币种与附件须在批准前可核对|中英草稿编辑、版本、预览、批准、发件状态|新 POST /quotes、PATCH /quotes/{id}、POST /quotes/{id}/approve-send、GET /deliveries/{id}；quote_versions/approvals/outbox/deliveries|
|Reports /reports、/reports/[id]|已实现详情、八节快照、PDF 下载|新增权限过滤、保留原编号及不可变下载|列表、关联询盘、证据版本与可见性提示|旧 /deals/{id}/reports、/reports/{id}、/download；新 GET /reports 索引；decision_reports/decision_selections/deal_sources|

**原型走查**：分别从邮箱和上传进入同一询盘详情；展示一条缺失币种、一条同名公司、一条无产品规则覆盖；修正后审批建单。选中保存的可行方案，生成英文草稿，修改收件人后展示原发送批准失效。空状态、失败重试、被拒、资料过期、只读历史和无权限均要有页面状态。Phase 1 原型使用明确标注的合成输入，不发送邮件。
