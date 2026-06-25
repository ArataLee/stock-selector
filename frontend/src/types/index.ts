export interface QuoteResponse {
  stock_code: string;
  stock_name: string;
  price: number;
  pe_ttm: number | null;
  pb: number | null;
  market_cap: number | null;
  volume: number | null;
}

export interface FinancialReportResponse {
  period: string;
  revenue_yoy: number | null;
  profit_yoy: number | null;
  roe: number | null;
  gross_margin: number | null;
  net_margin: number | null;
}

export interface ScreenResultResponse {
  stock_code: string;
  stock_name: string;
  dimension_scores: Record<string, number>;
  composite_score: number;
  tier: string;
  reasoning: string;
}

export interface ScreeningResponse {
  task_id: number;
  results: ScreenResultResponse[];
  count: number;
}

export interface DataSourceItem {
  id: string;
  name: string;
  type: string;
  priority: number;
  enabled: boolean;
}

export interface ProviderItem {
  id: string;
  api_base: string;
  model: string;
  default: boolean;
}

export interface PromptItem {
  id: string;
  scenario: string;
  description: string;
}

export interface WatchlistItem {
  stock_code: string;
  added_at: string;
}
