import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, Button, Space, Tag } from 'antd';
import { useNavigate } from 'react-router-dom';
import { SearchOutlined, StarOutlined, MessageOutlined } from '@ant-design/icons';
import { configApi } from '../api/config';
import { userApi } from '../api/user';
import type { DataSourceItem } from '../types';

const marketStatusColors: Record<string, string> = {
  '交易中': 'green',
  '盘前': 'gold',
  '午间休市': 'orange',
  '已闭市': 'default',
  '休市': 'default',
};

function getTodayKey() {
  return new Date().toISOString().slice(0, 10);
}
function readTodayCount(): number {
  try {
    const data = JSON.parse(localStorage.getItem('screening_counts') || '{}');
    return data[getTodayKey()] || 0;
  } catch { return 0; }
}
function incrementTodayCount(n: number) {
  try {
    const data = JSON.parse(localStorage.getItem('screening_counts') || '{}');
    const key = getTodayKey();
    data[key] = (data[key] || 0) + n;
    localStorage.setItem('screening_counts', JSON.stringify(data));
  } catch {}
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [sources, setSources] = useState<DataSourceItem[]>([]);
  const [watchCount, setWatchCount] = useState(0);
  const [marketStatus, setMarketStatus] = useState('加载中');
  const [todayCount, setTodayCount] = useState(readTodayCount());

  useEffect(() => {
    configApi.getDataSources().then(d => setSources(d.sources)).catch(() => {});
    userApi.getWatchlist().then(d => setWatchCount(d.items?.length || 0)).catch(() => {});
    fetch('/api/market/status')
      .then(r => r.json())
      .then(d => setMarketStatus(d.status))
      .catch(() => setMarketStatus('未知'));
    setTodayCount(readTodayCount());

    const onCountUpdate = () => setTodayCount(readTodayCount());
    window.addEventListener('screening-count-updated', onCountUpdate);
    return () => window.removeEventListener('screening-count-updated', onCountUpdate);
  }, []);

  const enabledSources = sources.filter(s => s.enabled);

  return (
    <div>
      <Typography.Title level={3}>仪表盘</Typography.Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="可用数据源" value={enabledSources.length} suffix={`/ ${sources.length}`} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="关注股票" value={watchCount} /></Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ color: 'rgba(0,0,0,0.45)', fontSize: 14, marginBottom: 8 }}>市场状态</div>
            <Tag color={marketStatusColors[marketStatus] || 'default'} style={{ fontSize: 18, padding: '4px 12px' }}>
              {marketStatus}
            </Tag>
          </Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="今日筛选" value={todayCount} suffix="只" /></Card>
        </Col>
      </Row>

      <Card title="快捷操作">
        <Space size="large">
          <Button type="primary" icon={<SearchOutlined />} size="large" onClick={() => navigate('/screening')}>
            开始选股
          </Button>
          <Button icon={<MessageOutlined />} size="large" onClick={() => navigate('/chat')}>
            AI对话
          </Button>
          <Button icon={<StarOutlined />} size="large" onClick={() => navigate('/watchlist')}>
            管理关注
          </Button>
        </Space>
      </Card>

      <Card title="数据源状态" style={{ marginTop: 16 }}>
        {sources.map(s => (
          <div key={s.id} style={{ marginBottom: 8 }}>
            <span style={{ marginRight: 16 }}>{s.name}</span>
            <span style={{ color: s.enabled ? '#52c41a' : '#d9d9d9' }}>
              {s.enabled ? '● 可用' : '○ 未启用'}
            </span>
            {s.type === 'account' && !s.enabled && (
              <span style={{ marginLeft: 16, color: '#faad14' }}>（需配置账号）</span>
            )}
          </div>
        ))}
      </Card>
    </div>
  );
};

export default Dashboard;
