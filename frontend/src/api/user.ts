import { api } from './client';

export const userApi = {
  getProfile: () => api.get<{ default_dimensions: string[]; default_universe: string; batch_size: number }>('/user/profile'),
  updatePreferences: (prefs: Record<string, unknown>) => api.put('/user/profile/preferences', prefs),
  getWatchlist: () => api.get<{ items: { stock_code: string; added_at: string }[] }>('/user/watchlist'),
  addToWatchlist: (code: string) => api.post('/user/watchlist', { stock_code: code }),
  removeFromWatchlist: (code: string) => api.delete(`/user/watchlist/${code}`),
};
