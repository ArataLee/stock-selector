# Stock Selector

A股（沪深京）成长价值选股助手，面向投资新手。基于大语言模型的多维度综合评分，通过自然语言描述即可发现具备成长潜力的股票。

## 功能

- **智能发现**：输入"推荐3只消费股"，自动筛选并评分推荐
- **代码筛选**：指定股票代码，多维度（财务/行业/估值）LLM评分
- **AI对话**：流式对话，解答选股和财务分析问题
- **多源数据**：免费数据源（新浪→东财降级）+ 付费账号（Tushare）可配置
- **定时监控**：Cron定时扫描 + 企微/飞书/钉钉推送报告
- **CLI + Web**：命令行工具 + React Web界面

## 快速开始

### 后端

```bash
cd backend
pip install -e ".[dev]"
cp config/user.yaml.example config/user.yaml   # 填入LLM API Key
stock-selector server start --reload            # http://127.0.0.1:8000
```

### 前端

```bash
cd frontend
npm install
npm run dev                                     # http://127.0.0.1:5173
```

### 命令行

```bash
stock-selector market quote 600519              # 查询行情
stock-selector screening screen 600519 000858   # 批量评分
stock-selector screening analyze 600519         # 深度分析
```

## 配置

编辑 `backend/config/default.yaml`，填入你的LLM API信息：

```yaml
llm:
  providers:
    - id: deepseek
      api_base: https://api.deepseek.com/v1
      api_key: sk-your-key
      model: deepseek-chat
      default: true
```

支持所有 OpenAI 兼容接口（DeepSeek / 通义千问 / GLM / Ollama 等）。

## 架构

DDD分层架构，Python FastAPI后端 + React/TypeScript前端。

```
用户请求 → CLI / FastAPI → Application层（用例编排）
  → Market Context（多源行情/财务）
  → LLM Context（评分/对话/报告）
  → Screening Context（筛选引擎 + 智能发现）
  → Notification Context（定时扫描 + IM推送）
```

## 开发

```bash
cd backend && pytest          # 运行所有测试（44个）
cd frontend && npx tsc --noEmit  # TypeScript类型检查
```

## 免责声明

所有评分和分析由AI生成，**建议仅供参考，不构成任何投资建议**。投资有风险，入市需谨慎。
