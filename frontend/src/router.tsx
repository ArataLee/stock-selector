import { createBrowserRouter } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Screening from './pages/Screening';
import Chat from './pages/Chat';
import Watchlist from './pages/Watchlist';
import Monitoring from './pages/Monitoring';
import History from './pages/History';
import Settings from './pages/Settings';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'screening', element: <Screening /> },
      { path: 'chat', element: <Chat /> },
      { path: 'watchlist', element: <Watchlist /> },
      { path: 'monitoring', element: <Monitoring /> },
      { path: 'history', element: <History /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
]);

export default router;
