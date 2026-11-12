# 当前表结构与 V2 扩展
以下由当前 SQLAlchemy metadata 导出。另有 Alembic 管理的 alembic_version。问号表示可空，PK 为主键。

## markets

- country_code · VARCHAR(2) PK
- country_name_zh · VARCHAR
- country_name_en · VARCHAR
- default_currency · VARCHAR(3)
- is_enabled · BOOLEAN
- rules_status · VARCHAR

## products

- id · CHAR(32) PK
- name · VARCHAR
- sku · VARCHAR UNIQUE
- hs_code · VARCHAR?
- description · TEXT?
- unit · VARCHAR
- default_cost · NUMERIC?
- default_cost_currency · VARCHAR(3)?
- created_at · DATETIME
- updated_at · DATETIME

## buyers

- id · CHAR(32) PK
- company_name · VARCHAR
- country_code · VARCHAR(2) → markets.country_code（默认引用限制）
- contact_name · VARCHAR?
- email · VARCHAR?
- notes · TEXT?
- created_at · DATETIME
- updated_at · DATETIME

## deals

- data_origin · VARCHAR
- id · CHAR(32) PK
- deal_number · VARCHAR UNIQUE
- name · VARCHAR
- buyer_id · CHAR(32) → buyers.id（默认引用限制）
- origin_country · VARCHAR(2) → markets.country_code（默认引用限制）
- destination_country · VARCHAR(2) → markets.country_code（默认引用限制）
- currency · VARCHAR(3)
- incoterm · VARCHAR
- status · VARCHAR
- requested_deadline · DATE?
- customer_target_price · NUMERIC?
- target_margin · NUMERIC?
- notes · TEXT?
- created_at · DATETIME
- updated_at · DATETIME
- exchange_rates · JSON

## constraints

- id · CHAR(32) PK
- deal_id · CHAR(32) → deals.id（CASCADE）
- constraint_type · VARCHAR
- operator · VARCHAR
- value · NUMERIC
- unit · VARCHAR
- is_hard · BOOLEAN
- description · TEXT?

## cost_items

- id · CHAR(32) PK
- deal_id · CHAR(32) → deals.id（CASCADE）
- cost_type · VARCHAR
- description · TEXT?
- amount · NUMERIC
- currency · VARCHAR(3)
- source_type · VARCHAR
- source_reference · VARCHAR?
- confirmed · BOOLEAN
- included · BOOLEAN
- converted_amount · NUMERIC
- created_at · DATETIME

## deal_items

- id · CHAR(32) PK
- deal_id · CHAR(32) → deals.id（CASCADE）
- product_id · CHAR(32) → products.id（默认引用限制）
- product_name_snapshot · VARCHAR
- sku_snapshot · VARCHAR
- quantity · NUMERIC
- unit_price · NUMERIC
- unit_price_currency · VARCHAR(3)
- unit_manufacturing_cost · NUMERIC
- cost_currency · VARCHAR(3)
- unit · VARCHAR
- converted_revenue · NUMERIC
- converted_manufacturing_cost · NUMERIC
- manufacturing_confirmed · BOOLEAN

## optimization_runs

- id · CHAR(32) PK
- deal_id · CHAR(32)? → deals.id（SET NULL）
- objective · VARCHAR
- status · VARCHAR
- algorithm_version · VARCHAR
- input_snapshot · JSON
- calculation_snapshot · JSON
- completed_at · DATETIME
- created_at · DATETIME

## scenarios

- id · CHAR(32) PK
- optimization_run_id · CHAR(32) → optimization_runs.id（CASCADE）
- position · INTEGER
- result · JSON
- created_at · DATETIME

## decision_selections

- id · CHAR(32) PK
- deal_id · CHAR(32)? → deals.id（SET NULL）
- optimization_run_id · CHAR(32) → optimization_runs.id（默认引用限制）
- scenario_id · CHAR(32) → scenarios.id（默认引用限制）
- selected_by · VARCHAR
- selection_note · VARCHAR
- created_at · DATETIME

## decision_reports

- id · CHAR(32) PK
- decision_selection_id · CHAR(32) → decision_selections.id（默认引用限制）
- report_number · VARCHAR UNIQUE
- report_snapshot · JSON
- pdf · BLOB
- created_at · DATETIME


## 可复用边界与后续迁移
0001 市场，0002 订单目录和明细，0003 优化与候选，0004 选择、报告与来源分类，0005 历史演示来源校正。报价、成本及折算额使用 NUMERIC，序列化为字符串；汇率保存在 deals.exchange_rates 中。删除订单会级联删除明细、成本、约束；优化运行和选择的 deal_id 置空，冻结快照、报告通过自身 ID 保留。不要从当前 catalog 重建历史 PDF。
本次文档、前端原型和对接已有 API 都无需迁移。后续按身份/租户 → 输入与任务 → 证据与目录扩展 → 双审批与发件顺序增加 Alembic 修订。审批保存真实主体、动作、版本、时间和结果。批准版本与正式订单建立唯一来源关联；发送意图对报价版本唯一，外部超时先对账。每条情报都关联证据和适用时段，任何新数据源的状态以实际接入验收为准。先在隔离库回放备份，再验旧报告哈希、历史运行和已删除订单的存档访问。maintenance.py 当前限定 0005，同一阶段需升级恢复工具，不能将未知版本的备份硬套旧清单。详见 V2_DATABASE_MIGRATION_PLAN.md。

核对边界：本日数据库连接超时，以上是模型声明与迁移链映射。ORM 通用类型 CHAR(32) 的 Uuid 在 PostgreSQL 方言下为 UUID，HTTP 使用标准 UUID 字符串。
