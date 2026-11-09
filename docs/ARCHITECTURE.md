# 系统架构
Next.js App Router 通过公开的 API 基址访问 FastAPI /api/v1。浏览器只读取 NEXT_PUBLIC_API_BASE_URL。开发环境允许 localhost:3000 跨域访问，其他来源通过 FRONTEND_ORIGIN 配置。界面按同名键读取中英字典，默认 zh-CN。
FastAPI 路由负责输入输出，业务服务通过独立 SQLAlchemy Session 读写 PostgreSQL。事务由业务服务提交。Alembic 管理版本。健康接口仅检查 API 进程。
优化服务按冻结的订单、日期和汇率快照进行 Decimal 折算。确定性枚举已批准的报价、数量和物流网格，保存每个已评估候选及约束检查。方案对比读取保存值；决策报告冻结选择及 PDF 字节。看板按订单来源统计，订单总额按币种分组。应用通过回环地址运行。
