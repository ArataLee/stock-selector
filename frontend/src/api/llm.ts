import { api } from './client';
import type { ScreenResultResponse } from '../types';

export const llmApi = {
  score: (stockCode: string) =>
    api.post<ScreenResultResponse>(`/llm/score/${stockCode}`),
  generateReport: (stocksData: unknown[]) =>
    api.post<{ report: string }>('/llm/reports/generate', stocksData),
};
