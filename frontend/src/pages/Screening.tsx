import React, { useState } from 'react';
import { Input, Button, Select, Table, Tag, Space, Typography, Spin, message, Tabs, InputNumber } from 'antd';
import { SearchOutlined, BulbOutlined } from '@ant-design/icons';
import { screeningApi } from '../api/screening';
import type { ScreenResultResponse } from '../types';

const dimensionOptions = [
  { label: '财务成长性', value: 'financial' },
  { label: '行业赛道', value: 'industry' },
  { label: '估值合理性', value: 'valuation' },
];

const tierColors: Record<string, string> = {
  '不推荐': 'red',
  '推荐': 'orange',
  '力荐': 'green',
};

const Screening: React.FC = () => {
  const [codes, setCodes] = useState('');
  const [dimensions, setDimensions] = useState<string[]>(['financial', 'industry', 'valuation']);
  const [results, setResults] = useState<ScreenResultResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('discover');
  const [discoverQuery, setDiscoverQuery] = useState('');
  const [discoverCount, setDiscoverCount] = useState(5);

  const handleScreen = async () => {
    const codeList = codes.split(/[,，\s]+/).filter(Boolean);
    if (codeList.length === 0) {
      message.warning('请输入至少一个股票代码');
      return;
    }
    setLoading(true);
    try {
      const resp = await screeningApi.create(codeList, dimensions);
      setResults(resp.results);
      message.success(`筛选完成，共 ${resp.count} 只股票`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '未知错误';
      message.error(`筛选失败: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDiscover = async () => {
    if (!discoverQuery.trim()) {
      message.warning('请描述你想找什么类型的股票');
      return;
    }
    setLoading(true);
    try {
      const resp = await fetch('/api/screening/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: discoverQuery.trim(), count: discoverCount }),
      }).then(r => {
        if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Unknown error'); });
        return r.json();
      });
      setResults(resp.results || []);
      message.success(`发现 ${resp.count} 只推荐股票`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '未知错误';
      message.error(`发现失败: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '股票', dataIndex: 'stock_name', key: 'name', render: (text: string, r: ScreenResultResponse) => `${text}(${r.stock_code})` },
    { title: '综合评分', dataIndex: 'composite_score', key: 'score', sorter: (a: ScreenResultResponse, b: ScreenResultResponse) => a.composite_score - b.composite_score,
      render: (v: number) => <span style={{ fontWeight: 'bold', fontSize: 18 }}>{v.toFixed(0)}</span> },
    { title: '档位', dataIndex: 'tier', key: 'tier',
      render: (t: string) => <Tag color={tierColors[t] || 'default'}>{t}</Tag> },
    { title: '评分详情', dataIndex: 'dimension_scores', key: 'dims',
      render: (d: Record<string, number>) => Object.entries(d).map(([k, v]) => (
        <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ width: 80, fontSize: 12 }}>{k}</span>
          <div style={{ flex: 1, height: 8, background: '#f0f0f0', borderRadius: 4 }}>
            <div style={{ width: `${v}%`, height: 8, background: v >= 80 ? '#52c41a' : v >= 60 ? '#faad14' : '#ff4d4f', borderRadius: 4 }} />
          </div>
          <span style={{ fontSize: 12, width: 30 }}>{v.toFixed(0)}</span>
        </div>
      )),
    },
    { title: '推荐理由', dataIndex: 'reasoning', key: 'reasoning', ellipsis: true, width: 250 },
  ];

  const tabItems = [
    {
      key: 'discover',
      label: <span><BulbOutlined /> 智能发现</span>,
      children: (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Typography.Text strong style={{ display: 'block', marginBottom: 8 }}>描述你想要的股票</Typography.Text>
            <Input.TextArea
              placeholder="例如：推荐5只半导体相关股票、帮我找消费板块的成长股、人工智能龙头股"
              value={discoverQuery}
              onChange={e => setDiscoverQuery(e.target.value)}
              rows={3}
              onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleDiscover(); }}}
            />
          </div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div>
              <Typography.Text strong style={{ marginRight: 8 }}>推荐数量</Typography.Text>
              <InputNumber min={1} max={20} value={discoverCount} onChange={v => setDiscoverCount(v || 5)} />
            </div>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleDiscover} loading={loading} size="large">
              开始发现
            </Button>
          </div>
        </Space>
      ),
    },
    {
      key: 'codes',
      label: <span><SearchOutlined /> 代码筛选</span>,
      children: (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Typography.Text strong style={{ display: 'block', marginBottom: 8 }}>股票代码</Typography.Text>
            <Input.TextArea
              placeholder="输入股票代码，用逗号、空格或换行分隔，如：600001, 000001, 300750"
              value={codes}
              onChange={e => setCodes(e.target.value)}
              rows={3}
            />
          </div>
          <div>
            <Typography.Text strong style={{ display: 'block', marginBottom: 8 }}>评估维度</Typography.Text>
            <Select mode="multiple" style={{ width: '100%' }} value={dimensions} onChange={setDimensions} options={dimensionOptions} />
          </div>
          <Button type="primary" icon={<SearchOutlined />} onClick={handleScreen} loading={loading} size="large">开始筛选</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={3}>选股中心</Typography.Title>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} style={{ marginBottom: 24 }} />

      {loading && <Spin tip="正在分析中，请稍候..."><div style={{ height: 100 }} /></Spin>}

      {results.length > 0 && (
        <Table dataSource={results} columns={columns} rowKey="stock_code" pagination={false} bordered />
      )}
    </div>
  );
};

export default Screening;
