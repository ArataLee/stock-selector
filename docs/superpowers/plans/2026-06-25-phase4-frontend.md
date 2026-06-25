# Phase 4: Frontend — React + TypeScript + Ant Design + ECharts

> **For agentic workers:** Use superpowers:subagent-driven-development to implement.

**Goal:** Web UI for stock screening — dashboard, screening center, AI chat, watchlist, monitoring management.

**Architecture:** Vite + React 19 + TypeScript + Ant Design 5 + ECharts + React Router v7. API calls via fetch wrapper, no state management library (React context + hooks sufficient for single-user).

---

### Task 1: Vite + React project scaffold

**Files:**
- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/tsconfig.node.json`
- `frontend/vite.config.ts`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/vite-env.d.ts`

Setup:
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install antd @ant-design/icons echarts echarts-for-react react-router-dom
npm install -D @types/react @types/react-dom
```

Then clean up the default Vite boilerplate and replace with a basic Ant Design layout.

---

### Task 2: API client layer

**Files:**
- `frontend/src/api/client.ts` — fetch wrapper with base URL, error handling
- `frontend/src/api/market.ts` — quote, financials
- `frontend/src/api/screening.ts` — create task, get results
- `frontend/src/api/llm.ts` — score, chat, report
- `frontend/src/api/user.ts` — profile, watchlist
- `frontend/src/api/config.ts` — providers, data-sources, prompts
- `frontend/src/api/notification.ts` — monitors, channels
- `frontend/src/types/index.ts` — TypeScript interfaces

---

### Task 3: Layout + Routing

**Files:**
- `frontend/src/layouts/MainLayout.tsx` — Ant Design Layout with Sider
- `frontend/src/router.tsx` — React Router config
- Update `App.tsx` to use Router

Pages (placeholder → real):
- `/` → Dashboard
- `/screening` → Screening Center
- `/chat` → AI Chat
- `/watchlist` → Watchlist
- `/monitoring` → Monitor Management
- `/history` → History
- `/settings` → Settings

---

### Task 4: Dashboard page

**Files:**
- `frontend/src/pages/Dashboard.tsx`

Content: overview cards (market status, recent screenings), quick-action buttons.

---

### Task 5: Screening Center page

**Files:**
- `frontend/src/pages/Screening.tsx`
- `frontend/src/components/StockCard.tsx`

Content: stock code input (tag-based), dimension selector, "Start Screening" button, results table with tier badges (red/yellow/green), score bar chart.

---

### Task 6: AI Chat page

**Files:**
- `frontend/src/pages/Chat.tsx`

Content: chat interface with message bubbles, stock context injection, SSE streaming display.

---

### Task 7: Watchlist + Settings + History + Monitoring pages

**Files:**
- `frontend/src/pages/Watchlist.tsx`
- `frontend/src/pages/Settings.tsx`
- `frontend/src/pages/History.tsx`
- `frontend/src/pages/Monitoring.tsx`

Content: CRUD forms for each, Ant Design Table/Form components, ECharts integration for history.

---

### Task 8: Build + verify

```bash
cd frontend
npm run build
```

Ensure production build succeeds. Then add a proxy to Vite config for API calls to backend.

---

## Phase 4 Complete — Verification

```bash
# Start backend
cd backend && python -m src.cli.main server start &

# Start frontend
cd frontend && npm run dev

# Open http://localhost:5173
```
