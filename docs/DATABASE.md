# 数据库设计
已迁移 markets，以 ISO 3166-1 alpha-2 country_code 为主键，记录 country_name_zh、country_name_en、ISO 4217 default_currency、is_enabled、rules_status。CN、US 初始状态 unconfigured。新增市场需要录入其主数据，启用与规则是否齐备分别管理。
## 后续实体
|表|关系与用途|
|---|---|
|users|订单与报告的负责人|
|buyers|买方资料和注册市场|
|products|制造商产品、计量单位、基础成本|
|deals|关联 buyer 和 owner，origin_country、destination_country 分别引用 markets，currency 为成交币种，incoterm 为贸易术语，pricing_date 决定取价日期|
|deal_items|关联订单和产品，保存数量及单价快照|
|cost_items|关联订单或明细，记录成本种类、金额、币种和承担方|
|constraints|订单级上下限、单位及约束对象|
|trade_rule_sets|起运地、目的地、适用产品及术语、生效区间、版本、来源及审核状态，供服务按定价日选择|
|exchange_rate_snapshots|基准币、报价币、正值汇率、采集时间与来源，明确一单位基准币的兑换值|
|optimization_runs|订单、输入快照、规则与汇率版本、目标、求解状态|
|scenarios|运行产生的各组可行条件、利润和约束余量|
|decision_reports|引用运行与所选方案，冻结报告内容和生成时间|
金额及汇率采用 NUMERIC，禁止用实时数据覆盖历史快照。国家代码和币种应在写入时校验。首演市场不构成引擎分支。

## 第二阶段已实施
迁移 0002 新增 buyers、products、deals、deal_items、cost_items、constraints。业务表使用 UUID；金额、数量和约束数值使用 NUMERIC；时间戳包含时区。目录记录被订单引用时限制删除，删除订单级联清理明细。订单号和 SKU 唯一。商品行冻结名称、SKU、单位、数量与原币价格。订单 exchange_rates JSON 保存每个币种对的汇率、定价日期和来源；行内冗余保存折算后的扩展金额用于审计与列表查询。新增买家、商品、订单和相关行在一次事务中提交。当前订单定价资料以汇率条目的日期为准。

## 交付版本 0005
已实现市场、买家、商品、订单、订单行、成本、约束、优化运行、候选、选择及报告共 11 张业务表。上文后续实体中 users、trade_rule_sets 和独立 exchange_rate_snapshots 为规划项。选择保存人工填写的姓名；汇率和定价日期在订单快照内。备份恢复见 WINDOWS_RELEASE.md。
