import { api } from './client';

export const notificationApi = {
  getTasks: () => api.get<{ tasks: unknown[] }>('/notification/tasks'),
  createTask: (task: Record<string, unknown>) => api.post('/notification/tasks', task),
  updateTask: (id: string, status: string) => api.put(`/notification/tasks/${id}?status=${status}`),
  deleteTask: (id: string) => api.delete(`/notification/tasks/${id}`),
  getChannels: () => api.get<{ channels: unknown[] }>('/notification/channels'),
  createChannel: (channel: Record<string, unknown>) => api.post('/notification/channels', channel),
  deleteChannel: (id: string) => api.delete(`/notification/channels/${id}`),
};
