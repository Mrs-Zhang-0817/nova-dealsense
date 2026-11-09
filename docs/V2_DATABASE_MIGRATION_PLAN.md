# 数据基线、关系与迁移方案
实库只读目录检查为 Alembic 0005。0001 创建市场，0002 创建买家/产品/订单及成本约束，0003 创建优化运行及候选，0004 创建选择与报告并加入 data_origin，0005 修正旧演示来源标记。alembic_version 是版本表；下列 11 张为业务表。

|表|键、关系与业务语义|
|---|---|
|markets|country_code 主键，含中英文名、default_currency、is_enabled 与 rules_status；保存市场主数据。|
|buyers|UUID 主键；country_code → markets；公司、联系人、电邮、备注及创建/更新时间，是可变目录。|
|products|UUID 主键；唯一 SKU、名称、HS、说明、单位、默认成本与币种、时间戳。|
|deals|UUID 主键、唯一 deal_number；buyer_id → buyers，origin_country 与 destination_country → markets。currency、incoterm、status、期限、目标价、目标贡献率、notes、exchange_rates JSON、data_origin 和时间戳。|
|deal_items|UUID；deal_id → deals（级联），product_id → products；冻结名称、SKU、单位、数量、原币售价与制造成本、已确认标志，以及扩展收入/成本折算值。|
|cost_items|UUID；deal_id → deals（级联）；类别、说明、原币金额、币种、来源类型/引用、确认/纳入标志、折算额、创建时间。|
|constraints|UUID；deal_id → deals（级联）；类型、运算符、数值、单位、硬约束标记和说明。|
|optimization_runs|UUID；deal_id → deals（删除置空）；目标、状态、算法版本、input_snapshot、calculation_snapshot、创建与完成时间。保存订单、市场、汇率、边界和候选规则。|
|scenarios|UUID；optimization_run_id → runs（级联）；position、result JSON、时间。价格、数量、物流、财务、约束、交期、得分存在 result 中。|
|decision_selections|UUID；deal_id 删除置空，另引用 run、scenario；selected_by 自填，含说明及创建时间。选择变更追加一行。|
|decision_reports|UUID；引用 selection；唯一 report_number、report_snapshot JSON、pdf 二进制和创建时间。可从选择追溯运行与方案。|

金额、数量、汇率计算采用 Decimal，表的金额列为 NUMERIC，JSON 快照内保留十进制字符串。finance.calculate 使用 80 位运算上下文，逐行扩展金额折算至 8 位；确认并纳入的附加费用进入贡献利润。零收入贡献率为空。报告直接按 ID 返回原 PDF 字节。V2 必须保留旧 JSON 形状、算法版本和旧下载结果。

## 新实体提案及键约束
- 身份与隔离：tenants、users、memberships（tenant_id + user_id 唯一）、legacy_ownership（旧表名+主键+归属依据）。先制定历史访问映射，再启用真实账户。旧订单已删除的报告仍须明确所有者。
- 输入：mailboxes（租户、提供商、账户、凭据引用）、sync_cursors（邮箱+文件夹）、messages（邮箱+外部 ID 唯一）、assets（租户、内容摘要、字节数、隔离状态、存储键）、inquiries、inquiry_sources。邮箱文本、附件、独立上传可汇入同一 inquiry；摘要相同仅表示内容重复，不等于同一业务询盘。
- 任务与抽取：jobs（幂等键、租约、尝试次数、下次运行时间）、extractions（inquiry_id、输入摘要、模型版本、结构化结果、原文字段定位）、proposals（询盘、revision、金额币种及哈希，唯一询盘+版本）。保留原始抽取，人工更正另存版本。
- 企业与市场：product_aliases、supplier_quotes、product_matches 指向产品/询盘；company_profiles 指向买家；evidence 保存数据提供方、URI、内容摘要、检索时刻、有效日期、覆盖国家/产品、证据片段及授权约束；market_rules 按原产地、目的地、HS、适用日期和贸易条件查询，引用证据版本。企业、政策和产品证据分别关联，不覆盖 markets 的简单状态。
- 授权与回复：approvals 记录动作种类、主体、不可变版本、签批人、实际时间与结果。deal_sources 以已批准 proposal_id 唯一关联正式订单。quote_versions 引用 selection/report，冻结语言、正文、金额、收件人和附件摘要；outbox 对已批准报价版本设置唯一发送意图；deliveries 记录供应商 ID、对账及重试历史。通过同租户联合约束和服务端检查阻止跨租户关联。
- 索引、存储：在 jobs(state,next_attempt_at)、每租户询盘到达时间、证据来源/有效期、run_id+position 和审批待办建立按查询需要的索引，先用 EXPLAIN 验证。附件大文件存受控位置；资产内容和 DB manifest 必须作为同一恢复点验证。

## 实施顺序与退出条件
1. 在隔离库恢复 0005 的只读备份，登记每表行数/摘要、历史运行 ID、PDF 哈希；保留 V1.1 源码基线和原备份。用原版本读取原件作对照。
2. 每阶段独立 Alembic revision，先加新表、可空字段/关联，不把旧审批者字符串回填为真实身份，不自动将未知来源改为真实。旧工作流仍可读。
3. 分批回填经确认的归属，写进度检查点、隔离异常、校验唯一性和所有外键；双租户负向访问通过后再加非空/唯一约束。校验使用旧 API 读取历史订单、报告以及已删除订单的留存报告。
4. 新版本维护工具按 schema 版本识别清单，兼容旧归档恢复到 0005 再升级；校验恢复顺序、PDF 字节、附件摘要和加密凭据引用的可恢复性。现有 maintenance.py 固定 0005，不能直接承担 V2 恢复。
5. 审批创建订单与创建来源关系同事务；同一提案并发批准只创建一单。发送审批与 outbox 同事务，供应商外部调用在事务外。改价、改附件、改收件人使旧批准失效。
6. 切换失败先停 worker/发送、保留任务和待对账记录、关闭 V2 入口；回滚兼容应用。数据库回退在隔离副本演练；已有 V2 写入时不得以覆盖旧备份作为在线回滚。放行条件为历史快照逐字节一致、对账无孤儿、旧 PDF 哈希一致、无重复建单/发件及可恢复性通过。
