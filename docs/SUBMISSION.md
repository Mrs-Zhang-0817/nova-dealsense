# NOVA DealSense V1.1
面向制造业出口商的跨境交易决策平台。给定报价范围、产能、交期及利润目标，反推可行交易条件，比较方案并导出带历史快照的中文报告。
- 先看 PRODUCT_OVERVIEW.md 与 TECHNICAL_HIGHLIGHTS.md。
- 安装请读 deployment/WINDOWS.md，所有命令在 source 目录执行。真实密码在本机自行填写。
- 按 DEMO_SCRIPT.md 进行约六分钟演示。demo_data 内有水瓶订单输入、三个场景条件和已生成的演示 PDF。screenshots 为 Windows Edge 生产构建的实际页面。
- 数据来源为人工假设的合成案例。演示目标为美元单价 3.07、预计贡献利润 3850、预计贡献率 25.08%。
- 安全边界见 deployment/SECURITY.md。SHA256SUMS.txt 可核对文件完整性。

## 本次验收记录
Windows 生产构建在独立目录执行 npm ci、npm run build 和 next start 成功；另建 Python 3.12.14 环境按锁文件安装、加载 API 及中文字体成功。14 个后端用例、订单/优化/决策 Edge 流程通过。6 个主要页面在 1280 和 1440 像素宽度均通过导航与溢出检查。另用只读一致性备份在全新数据库恢复 11 张业务表，摘要全部一致。隔离 API 重启前后的看板、订单、优化历史、报告 JSON 和下载 PDF 保持一致。PDF 已渲染检查 5 页。未在第二台物理 Windows 主机或 Docker 上做本轮验收。
