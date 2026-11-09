# 从订单到决策报告
在 Windows 中按 README 启动数据库、执行迁移、启动前后端。运行 backend 测试前安装 requirements-test.txt。PDF 默认读取本机宋体 C:/Windows/Fonts/simsun.ttc，并将所用字形嵌入文件；可用 REPORT_CJK_FONT 指定具有嵌入许可的本机中文 TrueType 字体。项目不分发 Windows 字体文件。
## 演示
打开水瓶订单，核对原报价 USD 3、数量 5000、预计贡献利润 USD 3500。依次运行利润优先、低风险和买家匹配。使用 3.00–3.09 的报价区间、0.01 的报价步长、固定 5000 件、25% 贡献率及 0 最低利润。人工演示条件为准备 1 天、日产 1000 件、总产能 5000 件、运输 4 天、客户交期 10 天。
三个达标价格为 3.07、3.08 和 3.09。利润优先选 3.09；三者的产能占用和交付余量相同，低风险按既有利润规则打破平局，也选 3.09；买家匹配选 3.07。后者比 3.09 少 USD 100 预计贡献利润，更接近原单价。
在订单详情进入方案对比，选取运行并切换对比列。保存决策人和选择理由；可重新选择，旧记录可回查。为任一次选择生成报告后，可预览八个章节并下载 PDF。报告对照所选方案及最多三个其他排名靠前的可行方案；全部已评估候选仍保存在优化运行内。
## 数据来源与审计
decision_selections 关联订单、运行和方案，decision_reports 关联选择并保存报告编号、生成时刻、JSON 快照及 PDF 字节。两者均为追加记录。删除订单时保留已有选择及报告。报告的财务值来自所选结果；成本拆分复用优化器已有的物流替换、变动成本及汇率折算逻辑。数学约束、操作人员输入和算法排名单独展示。演示汇率和未经核验的交期会在风险与假设章节说明。
首页按真实业务、演示及来源未标注分类。活跃订单排除已关闭订单；可行及不可行订单数按每个订单最近一次运行计算。保存选择数包含历史改选。分类统计仅覆盖仍有关联订单的记录。历史报告可用原报告编号对应的链接回读。
## 实现清单
- 后端新增 app/api/decisions.py、app/models/decision.py、app/reports/decision.py、app/reports/pdf.py、tests/test_decisions.py 和 requirements-test.txt。
- 后端更新 app/main.py、app/api/business.py、app/models/business.py、app/schemas/deals.py、app/optimization/engine.py、requirements.txt、Dockerfile 和 migrations/env.py。新增迁移 0004_decisions.py 和 0005_legacy_demo_origin.py。
- 前端新增 app/deals/[id]/scenarios/page.tsx、app/reports/[id]/page.tsx、components/decision-dashboard.tsx 和 tests/decisions.cjs。更新订单详情、优化页、工作台、订单表单及 tests/orders.cjs 的演示来源标记。
- 更新 README.md。本机演示下载保存在 output/pdf/。


现场演示采用 scripts/seed_demo.py 创建的三笔独立演示订单。通过报告页或看板重新打开同一编号，PDF 下载来自数据库冻结的文件内容。
