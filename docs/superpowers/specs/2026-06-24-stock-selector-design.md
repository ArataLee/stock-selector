# Stock Selector — 设计文档

> A股市场（沪深京）成长价值选股助手，面向投资新手

---

## 1. 项目目标

面向A股（沪深京）市场，基于大语言模型帮助投资新手挑选有成长价值的股票。

**核心功能：**
- 多数据源自适应降级的统一数据接口
- LLM驱动的多维度综合评分（财务/行业赛道/估值等）
- 对话式选股交互 + 批量打分 + 分析报告生成
- CLI + Web双界面
- 定时市场扫描 + IM推送（企微/飞书/钉钉等）
- 用户自定义评估维度 + 关注列表管理

**用户画像：** 投资新手，不擅长在市场上挑选具有成长性的股票

---

## 2. 架构决策

**总体架构：** 分层架构 + DDD（领域驱动设计）

**选择理由：** 对当前规模不过度，对未来扩展不欠账。数据源、LLM、IM渠道均可独立扩展。

**组织方式：** Monorepo（`backend/` + `frontend/`），规模大了再拆。

---

## 3. 领域划分（Bounded Contexts）

```
┌──────────────────────────────────────────────────────┐
│                    Presentation                       │
│             CLI (Typer)  │  FastAPI                   │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────┼─────────────────────────────────┐
│        Application Layer (用例编排)                    │
│           App Services / DTOs / Commands              │
└────────────────────┬─────────────────────────────────┘
                     │
┌──────────┬─────────┼──────────────┬──────────────────┐
│  市场数据  │  选股分析  │   LLM交互   │   监控推送        │
│  Market  │Screening │    LLM      │ Notification     │
│  Context │ Context  │   Context   │    Context       │
├──────────┼──────────┼──────────────┼──────────────────┤
│          │                                        │  │
│  ┌───────┴─────────┐                ┌────────────┴─┐│
│  │   用户管理        │                │   Shared      ││
│  │  User Context    │                │   Kernel      ││
│  └──────────────────┘                └───────────────┘│
└───────────────────────────────────────────────────────┘
```

### Context 职责

| Context | 职责 |
|---------|------|
| **Market** | 统一数据接口，内部多源降级；定义 Stock、FinancialReport、Quote 聚合；数据源配置和发现 |
| **Screening** | 评估维度管理；筛选策略和打分；用户自定义维度 |
| **LLM** | 对话交互、打分排序、报告生成；多模型路由（按场景和成本）；OpenAI兼容协议适配 |
| **Notification** | 监控任务管理（CRUD/开关）；IM渠道适配（企微/飞书/钉钉）；APScheduler集成 |
| **User** | 关注列表、偏好配置、筛选历史 |
| **Shared Kernel** | 跨Context共享的核心值对象和接口 |

---

## 4. Shared Kernel

```
shared/
├── domain/
│   ├── StockCode.py       # 股票代码值对象（600001.SH → 沪市/600001）
│   ├── Market.py           # 市场枚举（沪/深/京）
│   ├── TimeRange.py        # 时间区间值对象
│   ├── PageRequest.py      # 分页值对象
│   └── ScoreTier.py        # 评分档位枚举
├── events/
│   ├── DomainEvent.py      # 领域事件基类
│   └── EventPublisher.py   # 发布接口
└── exceptions/
    └── DomainError.py      # 领域异常基类
```

**判断标准：** 一个类被多个Context使用，且变更需协调各Context → 放Shared Kernel。

**不放：** 数据库连接、LLM客户端、数据源适配器、通用工具函数。

---

## 5. Market Context — 市场数据

### 聚合

| 聚合 | 说明 |
|------|------|
| **Stock** | stock_code, name, market, listing_date |
| **FinancialReport** | stock_code, period, revenue_yoy, profit_yoy, roe, gross_margin... |
| **Quote** | stock_code, price, pe_ttm, pb, volume, market_cap... |

### 数据源策略

- **免费数据源**（AKShare、Baostock等）：开箱即用
- **账号数据源**（Tushare等）：用户配置账号后自动启用，删除配置后自动禁用
- **降级链：** 按 priority 顺序尝试，失败自动降级到下一数据源

### 统一对外接口

每个Repository接口由多个Adapter实现，外部只看到接口：
- `StockRepository` — 股票信息查询
- `FinancialRepository` — 财务数据查询
- `QuoteRepository` — 行情数据查询

Router按 `DataSourceId.priority` 串联adapter，透明降级。

---

## 6. Screening Context — 选股分析

### 聚合

| 聚合 | 说明 |
|------|------|
| **Dimension** | DimensionId("financial"/"industry"/"valuation")、DimensionWeights、CustomDimension（用户描述+LLM prompt模板） |
| **ScreenTask** | dimensions, universe(all/watchlist), status, results |
| **ScreenResult** | stock, dimension_scores, composite_score, tier, reasoning |

### 评分模型

| 分数 | 档位 | 含义 |
|------|------|------|
| 0-60 | 不推荐 | 成长性不足 |
| 60-80 | 推荐 | 有一定成长价值 |
| 80-100 | 力荐 | 成长价值突出 |

**ScreenResult 结构：**
- `dimension_scores` — 各维度独立打分
- `composite_score` — 综合评分（加权/等权/LLM综合判断）
- `tier` — 评分档位
- `reasoning` — LLM生成的推荐理由

### 筛选策略

| 策略 | 说明 |
|------|------|
| **PreScreenStrategy** | 定时全市场初筛，快速过滤 |
| **DeepScreenStrategy** | 按需深度分析，LLM精细化打分 |

### 默认评估维度

1. **财务** — 营收增长率、净利润增长率、ROE、毛利率等
2. **行业赛道** — 行业景气度、政策支持、市场空间等
3. **估值** — PE/PB分位、PEG等

用户可通过LLM自由文本描述自定义维度。

---

## 7. LLM Context — LLM交互

### 聚合

| 聚合 | 说明 |
|------|------|
| **ModelProvider** | ProviderId("deepseek"/"qwen"/"openai"/"ollama"...)、ProviderConfig(api_base, api_key, model)、ProviderRegistry |
| **Scenario** | ScenarioType(CONVERSATION/SCORING/REPORT)、ScenarioConfig（每场景可绑定不同model） |
| **PromptTemplate** | template_id, scenario, content, variables（内置默认 + 用户可覆盖） |
| **StockAnalysis** | stock_code, scenario, ScoreCard(dimension_scores, composite_score, tier, reasoning) |
| **Conversation** | user_id, messages[], context(当前分析股票) |

### 多模型路由

```
ScenarioType → ProviderConfig
   ├ CONVERSATION → 高级模型（如 deepseek-chat / gpt-4）
   ├ SCORING      → 便宜模型（如 deepseek-v3 / gpt-4o-mini）
   └ REPORT       → 高级模型
```

### 评分结构化提取

LLM输出由 `ScoreExtractor` 用JSON Schema约束，解析失败自动重试一次（更严格约束），仍失败则标注"解析异常"。

### 综合评分策略

- **weighted（默认）：** 各维度按配置权重加权平均
- **llm_judge：** 由LLM直接综合判断各维度权重并打分

---

## 8. Notification Context — 监控推送

### 聚合

| 聚合 | 说明 |
|------|------|
| **MonitorTask** | user_id, cron_expr, universe_type(all/watchlist), dimension_config, enabled（默认关闭） |
| **ChannelConfig** | user_id, channel_type(wecom/feishu/dingtalk), webhook_url, enabled |
| **PushMessage** | title, stock_list, summary, template_type → MessageFormatter按模板格式化 |

### 定时扫描流程

```
APScheduler 触发 cron
  → ScreeningAppService 执行筛选
  → 发布 ScreeningCompleted 事件
  → Notification 订阅事件
  → LLM 生成分析报告
  → MessageFormatter 按渠道模板格式化
  → ChannelAdapter 发送到 IM
```

### 领域事件

| 事件 | 发布方 | 订阅方 | 说明 |
|------|--------|--------|------|
| `ScreeningCompleted` | Screening | Notification | 生成报告并推送 |
| `ScoringFailed` | LLM | Notification | 可选：评分异常告警 |
| `DataSourceDegraded` | Market | Notification | 可选：数据源降级通知 |

---

## 9. User Context — 用户管理

| 聚合 | 说明 |
|------|------|
| User | 用户基本信息 |
| Watchlist | 用户关注股票列表 |
| UserPreferences | 偏好配置（默认维度、默认universe等） |

---

## 10. 项目目录结构

```
stock-selector/
├── backend/
│   ├── src/
│   │   ├── shared/                      # Shared Kernel
│   │   │   ├── domain/
│   │   │   │   ├── StockCode.py
│   │   │   │   ├── Market.py
│   │   │   │   ├── TimeRange.py
│   │   │   │   └── ScoreTier.py
│   │   │   ├── events/
│   │   │   │   ├── DomainEvent.py
│   │   │   │   └── EventPublisher.py
│   │   │   └── exceptions/
│   │   │       └── DomainError.py
│   │   │
│   │   ├── market/
│   │   │   ├── domain/
│   │   │   ├── infrastructure/
│   │   │   │   └── adapters/             # Tushare/AKShare/Baostock Adapter
│   │   │   └── application/
│   │   │
│   │   ├── screening/
│   │   │   ├── domain/
│   │   │   ├── infrastructure/
│   │   │   └── application/
│   │   │
│   │   ├── llm/
│   │   │   ├── domain/
│   │   │   ├── infrastructure/
│   │   │   │   ├── adapters/
│   │   │   │   └── clients/
│   │   │   └── application/
│   │   │
│   │   ├── notification/
│   │   │   ├── domain/
│   │   │   ├── infrastructure/
│   │   │   │   ├── adapters/             # WeCom/Feishu/DingTalk Adapter
│   │   │   │   └── scheduler/
│   │   │   └── application/
│   │   │
│   │   ├── user/
│   │   │   ├── domain/
│   │   │   ├── infrastructure/
│   │   │   └── application/
│   │   │
│   │   ├── api/                          # FastAPI Presentation
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   └── schemas.py
│   │   │
│   │   ├── cli/                          # CLI Presentation
│   │   │   ├── main.py                  # Typer 入口
│   │   │   └── commands/
│   │   │
│   │   └── bootstrap.py                 # DI容器 / 应用启动
│   │
│   ├── config/
│   │   ├── default.yaml
│   │   └── user.yaml.example
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   │
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│
└── docs/
    └── superpowers/
        └── specs/
```

**命名约定：** 各Context的顶层文件按聚合命名（`Stock.py`、`FinancialData.py`），不使用 `models.py`、`entities.py` 等大口袋。

---

## 11. Context间协作

| 方式 | 适用场景 | 举例 |
|------|---------|------|
| **领域事件** | 异步通知 | 扫描完成 → 通知推送 |
| **应用服务编排** | 同步流程 | 筛选：取数据→打分→存结果 |
| **Shared Kernel** | 值对象共用 | StockCode、ScoreTier |

**禁止跨Context直接访问Repository。**

---

## 12. 核心数据流

### 用户按需筛选（同步）

```
ScreeningAppService.Execute()
  ├──1→ Market: batch_fetch(universe) → List[Quote]
  │       └── DataSourceRouter → TushareAdapter → AKShareAdapter(降级)
  ├──2→ Market: batch_fetch_financials(universe) → List[FinancialReport]
  ├──3→ LLM: batch_score(quotes + financials + dimensions) → List[ScoreCard]
  │       └── ScenarioRouter → OpenAICompatAdapter(deepseek)
  ├──4→ Screening: ScreenTaskRepository.save(task)
  └──5→ 返回 List[ScreenResult]
```

### 定时扫描推送（异步）

```
APScheduler 触发 cron
  → ExecuteMonitorUseCase.execute(monitor_task)
      → 复用 ScreeningAppService（同上1-4步）
      → 发布 ScreeningCompleted 事件
  → Notification 订阅 ScreeningCompleted
      → GenerateReportUseCase → LLM生成报告
      → MessageFormatter.format(report, channel_type)
      → ChannelAdapter.send(formatted_message)
```

---

## 13. 技术栈

| 层 | 选择 | 说明 |
|-----|------|------|
| 后端框架 | FastAPI 0.115+ | 异步原生、Pydantic v2集成 |
| CLI | Typer | FastAPI同作者 |
| ORM | SQLAlchemy 2.0 async | DDD中仅用于infrastructure层 |
| 财务数据缓存 | DuckDB + pandas | 列式存储、OLAP、嵌入式 |
| 任务调度 | APScheduler 4.x | 进程内cron |
| HTTP客户端 | httpx (async) | LLM API + 数据源网络请求 |
| 配置 | YAML + pydantic-settings | 分层配置 |
| 前端 | React 19 + TypeScript + Vite | — |
| UI组件 | Ant Design 5 | 表格/图表/表单 |
| 图表 | ECharts (echarts-for-react) | K线/财务对比图 |

---

## 14. 数据存储

| 数据 | 存储 | 理由 |
|------|------|------|
| 用户信息、配置、关注列表 | SQLite | 结构化、ORM |
| 筛选历史、分析报告 | SQLite | 结构化、数据量小 |
| 财务数据缓存（季报/年报） | DuckDB | 列式存储、OLAP查询、嵌入式 |
| 实时行情 | 不持久化 | API实时获取 |

---

## 15. API设计

```
/api
├── /market
│   ├── GET  /stocks                    # 股票列表搜索
│   ├── GET  /stocks/{code}            # 股票基本信息
│   ├── GET  /stocks/{code}/quote      # 实时行情
│   └── GET  /stocks/{code}/financials # 财务数据
│
├── /screening
│   ├── POST /tasks                     # 创建筛选任务
│   ├── GET  /tasks/{id}               # 任务状态
│   ├── GET  /tasks/{id}/results       # 筛选结果（含ScoreCard）
│   └── POST /pre-screen               # 手动初筛
│
├── /llm
│   ├── POST /chat                      # 对话（SSE）
│   ├── POST /score/{stock_code}       # 单股打分
│   └── POST /reports/generate         # 生成报告
│
├── /monitor
│   ├── POST   /tasks                  # 创建监控
│   ├── GET    /tasks                  # 监控列表
│   ├── PUT    /tasks/{id}             # 更新（含开关）
│   └── DELETE /tasks/{id}             # 删除
│
├── /notification
│   ├── POST   /channels               # 添加渠道
│   ├── GET    /channels               # 渠道列表
│   ├── PUT    /channels/{id}          # 更新
│   └── DELETE /channels/{id}          # 删除
│
├── /user
│   ├── GET    /profile                # 用户信息
│   ├── PUT    /profile/preferences    # 更新偏好
│   ├── GET    /watchlist              # 关注列表
│   ├── POST   /watchlist              # 添加关注
│   └── DELETE /watchlist/{code}       # 移除关注
│
└── /config
    ├── GET  /llm-providers            # LLM provider列表
    ├── PUT  /llm-providers/{id}       # 配置LLM provider
    ├── GET  /data-sources             # 数据源状态
    ├── PUT  /data-sources/{id}/account # 配置数据源账号
    ├── DELETE /data-sources/{id}/account # 删除数据源账号
    └── GET  /prompts                  # Prompt模板列表
```

---

## 16. 配置设计

### 默认配置（default.yaml — 随代码发布）

```yaml
market:
  data_sources:
    - id: akshare
      name: AKShare
      type: free
      priority: 2
      enabled: true
    - id: baostock
      name: Baostock
      type: free
      priority: 3
      enabled: true
    - id: tushare
      name: Tushare
      type: account
      priority: 1
      enabled: false

llm:
  providers: []
  scenario_routing:
    conversation: ${provider}
    scoring: ${provider}
    report: ${provider}

screening:
  default_dimensions: ["financial", "industry", "valuation"]
  composite_strategy: weighted
  universe_default: all
  batch_size: 20

notification:
  channels: []

scheduler:
  max_concurrent_monitors: 5
  default_cron: "0 18 * * 1-5"
```

### 用户配置（user.yaml / 数据库存储）

```yaml
market:
  accounts:
    tushare:
      token: "your_tushare_token"

llm:
  providers:
    - id: deepseek
      api_base: https://api.deepseek.com/v1
      api_key: sk-xxx
      model: deepseek-chat
      default: true

notification:
  channels:
    - id: wecom_1
      type: wecom
      webhook_url: https://qyapi.weixin.qq.com/...
      enabled: true
```

**配置优先级：** 数据库 > 用户YAML > default.yaml

---

## 17. 错误处理

### 分层策略

| 层 | 策略 |
|-----|------|
| **Domain** | 定义领域异常：`DataSourceUnavailable`、`ScoringFailed`、`StockNotFound`、`InvalidDimension` |
| **Infrastructure** | 捕获技术异常 → 转译为领域异常（如 `httpx.Timeout` → `DataSourceTimeout`） |
| **Application** | 业务异常翻译：领域异常 → 友好消息 |
| **API** | 统一异常中间件 → HTTP status code + 友好消息 |

### LLM异常处理

- 单只股票评分失败：skip该股票，继续下一页，结果标注"评分异常"
- 批量评分中断：返回已完成部分 + 未完成数量
- JSON解析失败：自动重试一次，仍失败标注"解析异常"

---

## 18. 测试策略

| 层 | 测试类型 | 工具 |
|-----|---------|------|
| Domain | 纯逻辑单元测试（不Mock外部依赖） | pytest |
| Application | 单元测试（Mock Repository） | pytest + pytest-mock |
| Infrastructure | 集成测试（真实API录制/VCR模式） | pytest + fixtures |
| API | 集成测试（HTTP端点） | httpx + pytest-asyncio |
| CLI | 集成测试（命令参数/输出） | typer.testing.CliRunner |
| Frontend | 组件测试 | Vitest + React Testing Library |

---

## 19. 前端页面规划（初版）

| 页面 | 功能 |
|------|------|
| 首页/Dashboard | 概览：今日推荐、市场总览、最近筛选 |
| 选股中心 | 发起筛选、查看结果、维度配置 |
| AI对话 | 自然语言选股对话 |
| 我的关注 | 关注列表管理 |
| 监控管理 | 监控任务CRUD、推送渠道配置 |
| 筛选历史 | 历史筛选任务和结果回顾 |
| 设置 | LLM配置、数据源账号、偏好设置 |

---

## 20. 不在本期范围

- 实盘交易接口
- 回测引擎
- 多用户系统（本期单用户模式）
- 移动端App
- 量化策略编辑器
