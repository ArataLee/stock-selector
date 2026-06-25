import { api } from './client';
import type { DataSourceItem, ProviderItem, PromptItem } from '../types';

export const configApi = {
  getDataSources: () => api.get<{ sources: DataSourceItem[] }>('/config/data-sources'),
  getProviders: () => api.get<{ providers: ProviderItem[] }>('/config/llm-providers'),
  upsertProvider: (id: string, config: Record<string, unknown>) =>
    api.put(`/config/llm-providers/${id}`, config),
  setDataSourceAccount: (id: string, token: string) =>
    api.put(`/config/data-sources/${id}/account`, { token }),
  getPrompts: () => api.get<{ prompts: PromptItem[] }>('/config/prompts'),
};
