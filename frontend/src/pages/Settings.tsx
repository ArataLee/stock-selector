import React, { useEffect, useState } from 'react';
import { Typography, Card, Table, Button, Modal, Form, Input, Switch, message, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { configApi } from '../api/config';
import type { DataSourceItem, ProviderItem } from '../types';

const Settings: React.FC = () => {
  const [sources, setSources] = useState<DataSourceItem[]>([]);
  const [providers, setProviders] = useState<ProviderItem[]>([]);
  const [providerModal, setProviderModal] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    try {
      const ds = await configApi.getDataSources();
      setSources(ds.sources);
    } catch {}
    try {
      const lp = await configApi.getProviders();
      setProviders(lp.providers);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const handleAddProvider = async (values: Record<string, unknown>) => {
    try {
      await configApi.upsertProvider(values.id as string, values);
      message.success('LLM Provider 已配置');
      setProviderModal(false);
      form.resetFields();
      load();
    } catch (e: unknown) {
      message.error(`配置失败: ${e instanceof Error ? e.message : '未知错误'}`);
    }
  };

  const handleSetToken = async (sourceId: string) => {
    const token = prompt(`请输入 ${sourceId} 的 Token:`);
    if (token) {
      try {
        await configApi.setDataSourceAccount(sourceId, token);
        message.success(`${sourceId} 账号已配置`);
        load();
      } catch (e: unknown) {
        message.error(`配置失败: ${e instanceof Error ? e.message : '未知错误'}`);
      }
    }
  };

  const sourceColumns = [
    { title: '数据源', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'type', key: 'type', render: (t: string) => <Tag>{t === 'free' ? '免费' : '需账号'}</Tag> },
    { title: '优先级', dataIndex: 'priority', key: 'priority' },
    { title: '状态', dataIndex: 'enabled', key: 'enabled',
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '已启用' : '未启用'}</Tag> },
    { title: '操作', key: 'action',
      render: (_: unknown, r: DataSourceItem) => r.type === 'account' ? (
        <Button size="small" onClick={() => handleSetToken(r.id)}>
          {r.enabled ? '更新Token' : '配置Token'}
        </Button>
      ) : null },
  ];

  const providerColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'API地址', dataIndex: 'api_base', key: 'api_base', ellipsis: true },
    { title: '模型', dataIndex: 'model', key: 'model' },
    { title: '默认', dataIndex: 'default', key: 'default', render: (v: boolean) => v ? <Tag color="blue">默认</Tag> : null },
  ];

  return (
    <div>
      <Typography.Title level={3}>设置</Typography.Title>

      <Card title="LLM Providers" extra={<Button icon={<PlusOutlined />} onClick={() => setProviderModal(true)}>添加</Button>}
           style={{ marginBottom: 16 }}>
        <Table dataSource={providers} columns={providerColumns} rowKey="id" pagination={false}
               locale={{ emptyText: '未配置LLM Provider，点击"添加"进行配置' }} />
      </Card>

      <Card title="数据源管理">
        <Table dataSource={sources} columns={sourceColumns} rowKey="id" pagination={false} />
      </Card>

      <Modal title="添加 LLM Provider" open={providerModal} onCancel={() => setProviderModal(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleAddProvider}>
          <Form.Item name="id" label="ID" rules={[{ required: true }]}>
            <Input placeholder="deepseek" />
          </Form.Item>
          <Form.Item name="api_base" label="API Base URL" rules={[{ required: true }]}>
            <Input placeholder="https://api.deepseek.com/v1" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: true }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item name="model" label="Model" rules={[{ required: true }]}>
            <Input placeholder="deepseek-chat" />
          </Form.Item>
          <Form.Item name="default" label="设为默认" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Settings;
