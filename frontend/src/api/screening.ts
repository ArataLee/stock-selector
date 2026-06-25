import { api } from './client';
import type { ScreeningResponse } from '../types';

export const screeningApi = {
  create: (codes: string[], dimensions?: string[]) =>
    api.post<ScreeningResponse>('/screening/tasks', { codes, dimensions }),
  preScreen: (universe = 'all') =>
    api.post<{ message: string }>('/screening/pre-screen', { universe }),
};
