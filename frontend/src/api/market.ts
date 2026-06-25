import { api } from './client';
import type { QuoteResponse, FinancialReportResponse } from '../types';

export const marketApi = {
  getQuote: (code: string) => api.get<QuoteResponse>(`/market/stocks/${code}/quote`),
  getFinancials: (code: string, periods = 4) =>
    api.get<FinancialReportResponse[]>(`/market/stocks/${code}/financials?periods=${periods}`),
};
