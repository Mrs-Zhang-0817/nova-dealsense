# Phase 1 前后端 API Contract · 2026-11-12
表中 method、path、参数、请求体和成功码从当前 FastAPI app.openapi() 导出。成功响应的业务结构根据 api/business.py、optimizer.py、decisions.py、reports/decision.py 补全。绝大多数业务处理函数没有 response_model，OpenAPI 成功 schema 为 {}，不能直接据此生成可信的客户端类型。以下状态表示新版页面的采用方式，前三种均有 V1 路由；NEW 仅是提案。

## 传输与错误约定
v1 使用 application/json；金额、单价、数量型 Decimal、汇率、贡献率用十进制字符串交换。Pydantic 也接受 JSON number，前端应始终用字符串构造这些字段。优化数量/天数、页码、计数为整数，开关为 boolean，UUID 与 ISO 日期/带时区时间为字符串。target_margin="0.25" 表示 25%，contribution_margin_percent="25.08" 是百分数。原样保留 null，不把缺少金额当 0。无汇率时返回 422。前端可格式化展示，不自行求财务结果。
成功 POST 通常 201，GET/PUT 200，DELETE 204 无正文。错误使用 {detail:string}；校验 422 的实际 detail 是拼接的字符串，与 OpenAPI 默认 HTTPValidationError 数组不一致。查无对象 404，唯一键或引用冲突 409，通用错误 500。无可行解或资料不足属于正常 201 计算结果。PDF 成功是 application/pdf 字节流（带 Content-Disposition），错误仍解析 JSON。V2 后续可新增结构化字段错误，不直接改 v1 客户端预期。

## 响应类型字典（Wire DTO）
- Market、Buyer、Product、Deal、DealItem、CostItem、Constraint、Selection 分别使用数据库映射表所列完整列名。主键、外键为字符串，目录/订单包含时间戳。DealList = {total:int,items:(Deal & {buyer_name:string,estimated_value:DecimalString})[]}。estimated_value 为销售收入。
- DealDetail = Deal & {buyer:Buyer,items:DealItem[],costs:CostItem[],constraints:Constraint[],financials:Finance}；exchange_rates 在 Deal 内。Finance 包含 revenue、manufacturing_cost、additional_costs、total_included_cost、contribution_profit（金额字符串），contribution_margin、contribution_margin_percent（可空），has_estimates（布尔）。
- Candidate = {price,quantity,shipping,production_days,delivery_days,minimum_margin_price,financials,constraint_results,feasibility,score}。constraint_results 按约束键映射到 {actual,limit,passed}。Run = {run_id,objective,algorithm_version,status,diagnostics,truncated,evaluated,data_complete,grid_size?,recommended:Candidate|null,alternatives:Candidate[],example_rejection:Candidate|null}。diagnostics 为失败项计数字典或缺失原因数组。历史详情额外含 input_snapshot。枚举值 FEASIBLE / INFEASIBLE / INSUFFICIENT_DATA。列表只展示已检查候选，截断时须标明。
- Compare = {currency,objective,summary,rows:(Candidate & {id,name,position,utilization,slack,explanation:{facts,assumptions,ranking}})[]}；此处 objective 已翻译。若要保存选择，使用 rows[].id；原始 scenarios 返回的 result 无行 UUID。HistoryRow = {run_id,status,objective,created_at}。
- ReportRef = {id,report_number,created_at}。Report = {id,title,report_number,generated_at,currency,sections:[{title,rows:[string,string][]}],source,algorithm_version,calculation,objective,selected,alternatives,warnings,selection_id,demo_inputs}。报告读取冻结快照，勿用实时 deal 覆盖 source。
- Dashboard = {actual:Stats,demo:Stats,unknown:Stats}；Stats = {active,runs,feasible,infeasible,feasible_runs,decisions,total_value:{[currency]:DecimalString},reports:ReportRef[]}。feasible 为最近一次运行可行的订单数，feasible_runs 为可行运行总数。

## 请求体业务条件
订单 POST/PUT 使用完整 DealIn（非 PATCH）；buyer 与 buyer_id 二选一，行级 product 与 product_id 二选一；PUT 不应漏回成本、约束、汇率或订单行。按例 1 USD = 7.20 CNY，base=USD、quote=CNY、rate="7.20"，另传 date、source。Optimization.deal_id 必须与路径一致。Pick 的 scenario_id 必须属于指定运行且可行；Generate 只需 decision_selection_id，须与路径订单关联。Pick.selected_by 为文本，不能充当身份认证。

## 当前接口逐项索引
基址 /api/v1。EXTEND 的 POST /deals 今天可用于手工建单，未来询盘转换必须有独立授权。

|状态|方法与相对路径|参数|成功响应|页面|主要表|
|---|---|---|---|---|---|
|EXISTING|GET /health|无|200 Health|服务状态|无|
|EXISTING|GET /markets|无|200 Market[]|市场选择|markets|
|EXISTING|GET /markets/{code}|path code:string|200 Market|市场选择|markets|
|EXISTING|GET /buyers|无|200 Buyer[]|公司/产品目录、订单表单|buyers、markets|
|EXISTING|POST /buyers|body BuyerIn|201 Buyer|公司/产品目录、订单表单|buyers、markets|
|EXISTING|GET /buyers/{id}|path id:uuid|200 Buyer|公司/产品目录、订单表单|buyers、markets|
|EXISTING|PUT /buyers/{id}|path id:uuid, body BuyerIn|200 Buyer|公司/产品目录、订单表单|buyers、markets|
|EXISTING|DELETE /buyers/{id}|path id:uuid|204 无正文|公司/产品目录、订单表单|buyers、markets|
|EXISTING|GET /products|无|200 Product[]|公司/产品目录、订单表单|products|
|EXISTING|POST /products|body ProductIn|201 Product|公司/产品目录、订单表单|products|
|EXISTING|GET /products/{id}|path id:uuid|200 Product|公司/产品目录、订单表单|products|
|EXISTING|PUT /products/{id}|path id:uuid, body ProductIn|200 Product|公司/产品目录、订单表单|products|
|EXISTING|DELETE /products/{id}|path id:uuid|204 无正文|公司/产品目录、订单表单|products|
|EXTEND|POST /deals|body DealIn|201 DealDetail|订单列表/分析/编辑|deals、buyers、markets、products、deal_items、cost_items、constraints|
|EXISTING|GET /deals|query page:integer=1 minimum 1, query page_size:integer=20 minimum 1 maximum 100, query q:string=, query destination_country:string=, query status:string=, query ascending:boolean=False|200 DealList|订单列表/分析/编辑|deals、buyers、markets、products、deal_items、cost_items、constraints|
|EXISTING|PUT /deals/{id}|path id:uuid, body DealIn|200 DealDetail|订单列表/分析/编辑|deals、buyers、markets、products、deal_items、cost_items、constraints|
|EXISTING|DELETE /deals/{id}|path id:uuid|204 无正文|订单列表/分析/编辑|deals、buyers、markets、products、deal_items、cost_items、constraints|
|EXISTING|GET /deals/{id}|path id:uuid|200 DealDetail|订单列表/分析/编辑|deals、buyers、markets、products、deal_items、cost_items、constraints|
|EXISTING|POST /deals/{id}/optimize|path id:uuid, body Optimization|201 Run|Optimizer|optimization_runs、scenarios、订单及市场快照|
|EXISTING|GET /optimization/{run_id}|path run_id:uuid|200 Run + input_snapshot|Optimizer|optimization_runs、scenarios|
|REUSE_WITH_ADAPTER|GET /optimization/{run_id}/scenarios|path run_id:uuid, query offset:integer=0 minimum 0, query limit:integer=100 minimum 1 maximum 1000|200 Candidate[]|Optimizer|scenarios、optimization_runs|
|EXISTING|GET /deals/{id}/optimization-history|path id:uuid|200 HistoryRow[]|Optimizer/历史|deals、optimization_runs|
|REUSE_WITH_ADAPTER|GET /optimization/{id}/comparison|path id:uuid|200 Compare|Decision Center|optimization_runs、scenarios|
|EXISTING|POST /deals/{id}/decisions|path id:uuid, body Pick|201 Selection|Decision Center|decision_selections、optimization_runs、scenarios|
|EXISTING|GET /deals/{id}/decisions|path id:uuid|200 Selection[]|Decision Center|decision_selections、optimization_runs、scenarios、deals|
|EXISTING|GET /decisions/{id}|path id:uuid|200 Selection + scenario|Decision Center|decision_selections、optimization_runs、scenarios|
|EXISTING|POST /deals/{id}/reports|path id:uuid, body Generate|201 {id,report_number}|Reports|decision_reports、decision_selections、optimization_runs、scenarios|
|EXISTING|GET /deals/{id}/reports|path id:uuid|200 ReportRef[]|Reports|decision_reports、decision_selections|
|EXISTING|GET /reports/{id}|path id:uuid|200 Report|Reports|decision_reports|
|REUSE_WITH_ADAPTER|GET /reports/{id}/download|path id:uuid|200 PDF binary|Reports|decision_reports|
|EXISTING|GET /dashboard|无|200 Dashboard|Overview|deals、deal_items、optimization_runs、decision_selections、decision_reports|

## 当前请求模型原文
以下取自运行时 components.schemas，required 列表、默认值、枚举、范围与嵌套引用均以此为准。

```json
{
  "BuyerIn": {
    "properties": {
      "company_name": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Company Name"
      },
      "country_code": {
        "type": "string",
        "pattern": "^[A-Z]{2}$",
        "title": "Country Code"
      },
      "contact_name": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Contact Name"
      },
      "email": {
        "anyOf": [
          {
            "type": "string",
            "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
          },
          {
            "type": "null"
          }
        ],
        "title": "Email"
      },
      "notes": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Notes"
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "company_name",
      "country_code"
    ],
    "title": "BuyerIn"
  },
  "Cost": {
    "properties": {
      "cost_type": {
        "type": "string",
        "enum": [
          "packaging",
          "logistics",
          "insurance",
          "other"
        ],
        "title": "Cost Type"
      },
      "description": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Description"
      },
      "amount": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Amount"
      },
      "currency": {
        "type": "string",
        "pattern": "^[A-Z]{3}$",
        "title": "Currency"
      },
      "source_type": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Source Type",
        "default": "manual"
      },
      "source_reference": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Source Reference"
      },
      "confirmed": {
        "type": "boolean",
        "title": "Confirmed"
      },
      "included": {
        "type": "boolean",
        "title": "Included",
        "default": true
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "cost_type",
      "amount",
      "currency",
      "confirmed"
    ],
    "title": "Cost"
  },
  "DealIn": {
    "properties": {
      "data_origin": {
        "type": "string",
        "enum": [
          "unknown",
          "actual",
          "demo"
        ],
        "title": "Data Origin",
        "default": "unknown"
      },
      "name": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Name"
      },
      "buyer_id": {
        "anyOf": [
          {
            "type": "string",
            "format": "uuid"
          },
          {
            "type": "null"
          }
        ],
        "title": "Buyer Id"
      },
      "buyer": {
        "anyOf": [
          {
            "$ref": "#/components/schemas/BuyerIn"
          },
          {
            "type": "null"
          }
        ]
      },
      "origin_country": {
        "type": "string",
        "pattern": "^[A-Z]{2}$",
        "title": "Origin Country"
      },
      "destination_country": {
        "type": "string",
        "pattern": "^[A-Z]{2}$",
        "title": "Destination Country"
      },
      "currency": {
        "type": "string",
        "pattern": "^[A-Z]{3}$",
        "title": "Currency"
      },
      "incoterm": {
        "type": "string",
        "enum": [
          "EXW",
          "FCA",
          "FAS",
          "FOB",
          "CFR",
          "CIF",
          "CPT",
          "CIP",
          "DAP",
          "DPU",
          "DDP"
        ],
        "title": "Incoterm"
      },
      "status": {
        "type": "string",
        "enum": [
          "draft",
          "confirmed",
          "closed"
        ],
        "title": "Status",
        "default": "draft"
      },
      "requested_deadline": {
        "anyOf": [
          {
            "type": "string",
            "format": "date"
          },
          {
            "type": "null"
          }
        ],
        "title": "Requested Deadline"
      },
      "customer_target_price": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Customer Target Price"
      },
      "target_margin": {
        "anyOf": [
          {
            "type": "number",
            "maximum": 1.0,
            "minimum": 0.0
          },
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Target Margin"
      },
      "notes": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Notes"
      },
      "items": {
        "items": {
          "$ref": "#/components/schemas/Item"
        },
        "type": "array",
        "minItems": 1,
        "title": "Items"
      },
      "costs": {
        "items": {
          "$ref": "#/components/schemas/Cost"
        },
        "type": "array",
        "title": "Costs"
      },
      "constraints": {
        "items": {
          "$ref": "#/components/schemas/Limit"
        },
        "type": "array",
        "title": "Constraints"
      },
      "exchange_rates": {
        "items": {
          "$ref": "#/components/schemas/Rate"
        },
        "type": "array",
        "title": "Exchange Rates"
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "name",
      "origin_country",
      "destination_country",
      "currency",
      "incoterm",
      "items"
    ],
    "title": "DealIn"
  },
  "Generate": {
    "properties": {
      "decision_selection_id": {
        "type": "string",
        "format": "uuid",
        "title": "Decision Selection Id"
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "decision_selection_id"
    ],
    "title": "Generate"
  },
  "Health": {
    "properties": {
      "success": {
        "type": "boolean",
        "title": "Success"
      },
      "message": {
        "type": "string",
        "title": "Message"
      }
    },
    "type": "object",
    "required": [
      "success",
      "message"
    ],
    "title": "Health"
  },
  "Item": {
    "properties": {
      "product_id": {
        "anyOf": [
          {
            "type": "string",
            "format": "uuid"
          },
          {
            "type": "null"
          }
        ],
        "title": "Product Id"
      },
      "product": {
        "anyOf": [
          {
            "$ref": "#/components/schemas/ProductIn"
          },
          {
            "type": "null"
          }
        ]
      },
      "quantity": {
        "anyOf": [
          {
            "type": "number",
            "exclusiveMinimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Quantity"
      },
      "unit_price": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Unit Price"
      },
      "unit_price_currency": {
        "type": "string",
        "pattern": "^[A-Z]{3}$",
        "title": "Unit Price Currency"
      },
      "unit_manufacturing_cost": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Unit Manufacturing Cost"
      },
      "cost_currency": {
        "type": "string",
        "pattern": "^[A-Z]{3}$",
        "title": "Cost Currency"
      },
      "manufacturing_confirmed": {
        "type": "boolean",
        "title": "Manufacturing Confirmed",
        "default": true
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "quantity",
      "unit_price",
      "unit_price_currency",
      "unit_manufacturing_cost",
      "cost_currency"
    ],
    "title": "Item"
  },
  "Limit": {
    "properties": {
      "constraint_type": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Constraint Type"
      },
      "operator": {
        "type": "string",
        "enum": [
          "<=",
          ">=",
          "="
        ],
        "title": "Operator"
      },
      "value": {
        "anyOf": [
          {
            "type": "number"
          },
          {
            "type": "string"
          }
        ],
        "title": "Value"
      },
      "unit": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Unit"
      },
      "is_hard": {
        "type": "boolean",
        "title": "Is Hard"
      },
      "description": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Description"
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "constraint_type",
      "operator",
      "value",
      "unit",
      "is_hard"
    ],
    "title": "Limit"
  },
  "Optimization": {
    "properties": {
      "deal_id": {
        "type": "string",
        "format": "uuid",
        "title": "Deal Id"
      },
      "objective": {
        "type": "string",
        "enum": [
          "PROFIT_FIRST",
          "BUYER_FIT",
          "LOW_RISK"
        ],
        "title": "Objective"
      },
      "target_margin": {
        "anyOf": [
          {
            "type": "number",
            "exclusiveMaximum": 1.0,
            "minimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Target Margin"
      },
      "minimum_profit": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Minimum Profit"
      },
      "price_min": {
        "anyOf": [
          {
            "type": "number",
            "exclusiveMinimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Price Min"
      },
      "price_max": {
        "anyOf": [
          {
            "type": "number",
            "exclusiveMinimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Price Max"
      },
      "price_step": {
        "anyOf": [
          {
            "type": "number",
            "exclusiveMinimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Price Step"
      },
      "quantity_min": {
        "type": "integer",
        "maximum": 1000000000.0,
        "exclusiveMinimum": 0.0,
        "title": "Quantity Min"
      },
      "quantity_max": {
        "type": "integer",
        "maximum": 1000000000.0,
        "exclusiveMinimum": 0.0,
        "title": "Quantity Max"
      },
      "quantity_step": {
        "type": "integer",
        "maximum": 1000000000.0,
        "exclusiveMinimum": 0.0,
        "title": "Quantity Step"
      },
      "production_capacity": {
        "type": "integer",
        "maximum": 1000000000.0,
        "exclusiveMinimum": 0.0,
        "title": "Production Capacity"
      },
      "delivery_deadline_days": {
        "type": "integer",
        "maximum": 1000000000.0,
        "exclusiveMinimum": 0.0,
        "title": "Delivery Deadline Days"
      },
      "customer_unit_price_ceiling": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Customer Unit Price Ceiling"
      },
      "customer_total_budget": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Customer Total Budget"
      },
      "minimum_order_quantity": {
        "anyOf": [
          {
            "type": "integer",
            "maximum": 1000000000.0,
            "exclusiveMinimum": 0.0
          },
          {
            "type": "null"
          }
        ],
        "title": "Minimum Order Quantity"
      },
      "setup_days": {
        "anyOf": [
          {
            "type": "integer",
            "maximum": 1000000000.0,
            "minimum": 0.0
          },
          {
            "type": "null"
          }
        ],
        "title": "Setup Days"
      },
      "production_units_per_day": {
        "anyOf": [
          {
            "type": "integer",
            "maximum": 1000000000.0,
            "exclusiveMinimum": 0.0
          },
          {
            "type": "null"
          }
        ],
        "title": "Production Units Per Day"
      },
      "shipping_options": {
        "items": {
          "$ref": "#/components/schemas/Shipping"
        },
        "type": "array",
        "maxItems": 32,
        "title": "Shipping Options"
      },
      "additional_cost_adjustments": {
        "additionalProperties": {
          "type": "string",
          "enum": [
            "fixed",
            "per_unit"
          ]
        },
        "type": "object",
        "title": "Additional Cost Adjustments"
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "deal_id",
      "objective",
      "target_margin",
      "minimum_profit",
      "price_min",
      "price_max",
      "price_step",
      "quantity_min",
      "quantity_max",
      "quantity_step",
      "production_capacity",
      "delivery_deadline_days"
    ],
    "title": "Optimization"
  },
  "Pick": {
    "properties": {
      "optimization_run_id": {
        "type": "string",
        "format": "uuid",
        "title": "Optimization Run Id"
      },
      "scenario_id": {
        "type": "string",
        "format": "uuid",
        "title": "Scenario Id"
      },
      "selected_by": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Selected By"
      },
      "selection_note": {
        "type": "string",
        "maxLength": 1000,
        "title": "Selection Note",
        "default": ""
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "optimization_run_id",
      "scenario_id",
      "selected_by"
    ],
    "title": "Pick"
  },
  "ProductIn": {
    "properties": {
      "name": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Name"
      },
      "sku": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Sku"
      },
      "unit": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Unit"
      },
      "hs_code": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Hs Code"
      },
      "description": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Description"
      },
      "default_cost": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Default Cost"
      },
      "default_cost_currency": {
        "anyOf": [
          {
            "type": "string",
            "pattern": "^[A-Z]{3}$"
          },
          {
            "type": "null"
          }
        ],
        "title": "Default Cost Currency"
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "name",
      "sku",
      "unit"
    ],
    "title": "ProductIn"
  },
  "Rate": {
    "properties": {
      "base": {
        "type": "string",
        "pattern": "^[A-Z]{3}$",
        "title": "Base"
      },
      "quote": {
        "type": "string",
        "pattern": "^[A-Z]{3}$",
        "title": "Quote"
      },
      "rate": {
        "anyOf": [
          {
            "type": "number",
            "exclusiveMinimum": 0.0
          },
          {
            "type": "string"
          }
        ],
        "title": "Rate"
      },
      "date": {
        "type": "string",
        "format": "date",
        "title": "Date"
      },
      "source": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Source"
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "base",
      "quote",
      "rate",
      "date",
      "source"
    ],
    "title": "Rate"
  },
  "Shipping": {
    "properties": {
      "name": {
        "type": "string",
        "maxLength": 240,
        "minLength": 1,
        "title": "Name"
      },
      "days": {
        "type": "integer",
        "maximum": 1000000000.0,
        "minimum": 0.0,
        "title": "Days"
      },
      "replacement_cost": {
        "anyOf": [
          {
            "type": "number",
            "minimum": 0.0
          },
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "title": "Replacement Cost"
      }
    },
    "additionalProperties": false,
    "type": "object",
    "required": [
      "name",
      "days"
    ],
    "title": "Shipping"
  }
}

```

## 待评审的新接口（全部 NEW）
以下路径建议统一在 /api/v2 下。带 id 的资源使用 UUID。所有列表建议使用 {items,next_cursor}，任务返回 {job_id,status}。这些路径尚未注册，前端仅可使用标注的合成 fixture。

|状态|方法与路径|输入 → 成功响应|页面 / 拟新增实体|
|---|---|---|---|
|NEW|POST /mailboxes/{id}/sync|已授权邮箱 ID → 202 Job；Gmail/Graph 由邮箱配置决定|Inbox / mailboxes、sync_cursors、messages、jobs|
|NEW|POST /uploads|multipart file、来源 → 202 {asset_id,inquiry_id,job_id}；独立上传与邮件同级|Inbox / assets、inquiries、inquiry_sources|
|NEW|GET /inquiries|query source、status、cursor → 200 InquirySummary 列表|Inbox / inquiries|
|NEW|GET /inquiries/{id}|path → 200 {sources,attachments,extraction,proposal_revision,missing_fields,status}；字段附原文位置|询盘审核 / messages、assets、extractions、proposals|
|NEW|GET /jobs/{id}|path → 200 {status,attempts,error_code?,result_id?}|任务状态 / jobs|
|NEW|POST /inquiries/{id}/extract|来源版本、幂等键 → 202 Job；输出买家、产品、数量、价格、交期与证据|Inbox / jobs、extractions|
|NEW|PUT /proposals/{id}|expected_revision、更正字段 → 200 {id,revision,content_hash}|询盘审核 / proposals|
|NEW|POST /proposals/{id}/approve|revision、content_hash、幂等键，操作者取登录身份 → 201 {approval_id,deal_id}|Decision Center / approvals、deal_sources、现有订单表|
|NEW|POST /proposals/{id}/reject|revision、reason → 200 {approval_id,status}|Decision Center / approvals|
|NEW|POST /inquiries/{id}/matches|产品行与规格 → 200 {candidates:[{product_id,basis,unit}]}|Product Intelligence / product_matches、products|
|NEW|POST /companies/{id}/research|公司标识、域名、注册国 → 202 Job|Company Intelligence / company_profiles、jobs、evidence|
|NEW|GET /companies/{id}/evidence|cursor、as_of → 200 Evidence 列表|Company Intelligence / evidence|
|NEW|GET /market-rules|origin、destination、hs_code、as_of → 200 {items,coverage,warnings}|Market Intelligence / markets、market_rules、evidence|
|NEW|POST /research-jobs|政策或商品规则查询范围 → 202 Job|Market Intelligence / jobs、market_rules|
|NEW|POST /quotes|selection_id、language、recipient → 201 {id,revision,draft,status}|Reply Studio / quote_versions|
|NEW|PATCH /quotes/{id}|expected_revision、收件人/正文/附件 → 200 新版本，旧批准失效|Reply Studio / quote_versions|
|NEW|POST /quotes/{id}/approve-send|revision、冻结内容哈希、幂等键 → 202 {approval_id,delivery_id,status}|Reply Studio / approvals、outbox、deliveries|
|NEW|GET /deliveries/{id}|path → 200 {status,provider_message_id?,last_checked_at,error_code?}|Reply Studio / deliveries|
|NEW|GET /approvals|action、status、cursor → 200 待审/已审列表|Decision Center / approvals|
|NEW|GET /reports|cursor、deal_id 可选 → 200 有权访问的报告列表|Reports / decision_reports、资源归属|
|NEW|GET /overview|授权工作区、时间窗 → 200 {deal_metrics,inbox_counts,pending_approvals,delivery_counts}|Overview / 新旧业务表|

Evidence 建议含 source_url、publisher、retrieved_at、effective_from/to、applicable_market、hs_code、excerpt、confidence_basis、review_status。可信度记录依据与限制。拟议错误包括未登录 401、无权限 403、版本冲突 409、文件过大 413、格式不支持 415、字段不完整 422、供应商限流 429。V2 建议使用 {error:{code,message,field_errors?,request_id}}，与现行 v1 的 detail 分开处理。
