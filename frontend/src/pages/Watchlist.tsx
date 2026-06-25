import React, { useEffect, useState } from 'react';
import { Input, Button, List, Typography, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { userApi } from '../api/user';

interface WatchItem {
  stock_code: string;
  added_at: string;
}

const Watchlist: React.FC = () => {
  const [items, setItems] = useState<WatchItem[]>([]);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const d = await userApi.getWatchlist();
      setItems(d.items || []);
    } catch { setItems([]); }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!code.trim()) return;
    setLoading(true);
    try {
      await userApi.addToWatchlist(code.trim());
      message.success(`已添加 ${code.trim()}`);
      setCode('');
      load();
    } catch (e: unknown) {
      message.error(`添加失败: ${e instanceof Error ? e.message : '未知错误'}`);
    } finally { setLoading(false); }
  };

  const handleRemove = async (c: string) => {
    try {
      await userApi.removeFromWatchlist(c);
      message.success(`已移除 ${c}`);
      load();
    } catch (e: unknown) {
      message.error(`移除失败: ${e instanceof Error ? e.message : '未知错误'}`);
    }
  };

  return (
    <div>
      <Typography.Title level={3}>我的关注</Typography.Title>

      <Space.Compact style={{ width: '100%', marginBottom: 24 }}>
        <Input
          placeholder="股票代码，如 600001.SH"
          value={code}
          onChange={e => setCode(e.target.value)}
          onPressEnter={handleAdd}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} loading={loading}>添加</Button>
      </Space.Compact>

      <List
        dataSource={items}
        renderItem={item => (
          <List.Item
            actions={[
              <Popconfirm title="确定移除？" onConfirm={() => handleRemove(item.stock_code)} key="del">
                <Button danger icon={<DeleteOutlined />} size="small">移除</Button>
              </Popconfirm>
            ]}
          >
            <List.Item.Meta
              title={item.stock_code}
              description={`添加时间: ${item.added_at}`}
            />
          </List.Item>
        )}
        locale={{ emptyText: '暂无关注股票' }}
      />
    </div>
  );
};

export default Watchlist;
