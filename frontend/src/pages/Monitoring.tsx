import React, { useEffect, useState } from 'react';
import { Typography, Card, Button, Table, Modal, Form, Input, Select, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { notificationApi } from '../api/notification';

const channelTypeOptions = [
  { label: '企业微信', value: 'wecom' },
  { label: '飞书', value: 'feishu' },
  { label: '钉钉', value: 'dingtalk' },
];

const Monitoring: React.FC = () => {
  const [tasks, setTasks] = useState<unknown[]>([]);
  const [channels, setChannels] = useState<unknown[]>([]);
  const [taskModal, setTaskModal] = useState(false);
  const [channelModal, setChannelModal] = useState(false);
  const [taskForm] = Form.useForm();
  const [channelForm] = Form.useForm();

  const load = async () => {
    try { const t = await notificationApi.getTasks(); setTasks(t.tasks || []); } catch {}
    try { const c = await notificationApi.getChannels(); setChannels(c.channels || []); } catch {}
  };

  useEffect(() => { load(); }, []);

  const handleCreateTask = async (values: Record<string, unknown>) => {
    try {
      await notificationApi.createTask(values);
      message.success('监控任务已创建');
      setTaskModal(false);
      taskForm.resetFields();
      load();
    } catch (e: unknown) { message.error(`创建失败: ${e instanceof Error ? e.message : '未知错误'}`); }
  };

  const handleCreateChannel = async (values: Record<string, unknown>) => {
    try {
      await notificationApi.createChannel(values);
      message.success('推送渠道已添加');
      setChannelModal(false);
      channelForm.resetFields();
      load();
    } catch (e: unknown) { message.error(`添加失败: ${e instanceof Error ? e.message : '未知错误'}`); }
  };

  const handleDeleteTask = async (id: string) => {
    try { await notificationApi.deleteTask(id); message.success('已删除'); load(); }
    catch (e: unknown) { message.error(`失败: ${e instanceof Error ? e.message : '未知错误'}`); }
  };

  const handleDeleteChannel = async (id: string) => {
    try { await notificationApi.deleteChannel(id); message.success('已删除'); load(); }
    catch (e: unknown) { message.error(`失败: ${e instanceof Error ? e.message : '未知错误'}`); }
  };

  return (
    <div>
      <Typography.Title level={3}>监控管理</Typography.Title>

      <Card title="推送渠道" extra={<Button icon={<PlusOutlined />} onClick={() => setChannelModal(true)}>添加渠道</Button>}
           style={{ marginBottom: 16 }}>
        <Table dataSource={channels as object[]} rowKey="id" pagination={false}
               locale={{ emptyText: '暂无推送渠道，请添加企微/飞书/钉钉机器人' }}>
          <Table.Column title="名称" dataIndex="name" />
          <Table.Column title="类型" dataIndex="type" render={(t: string) => <Tag>{t}</Tag>} />
          <Table.Column title="Webhook" dataIndex="webhook_url" ellipsis />
          <Table.Column title="操作" render={(_: unknown, r: { id: string }) => (
            <Popconfirm title="确定删除？" onConfirm={() => handleDeleteChannel(r.id)}>
              <Button danger icon={<DeleteOutlined />} size="small">删除</Button>
            </Popconfirm>
          )} />
        </Table>
      </Card>

      <Card title="监控任务" extra={<Button icon={<PlusOutlined />} onClick={() => setTaskModal(true)}>创建任务</Button>}>
        <Table dataSource={tasks as object[]} rowKey="id" pagination={false}
               locale={{ emptyText: '暂无监控任务，默认关闭' }}>
          <Table.Column title="名称" dataIndex="name" />
          <Table.Column title="Cron" dataIndex="cron_expr" />
          <Table.Column title="范围" dataIndex="universe_type" />
          <Table.Column title="状态" dataIndex="status" render={(s: string) => (
            <Tag color={s === 'active' ? 'green' : s === 'paused' ? 'orange' : 'default'}>{s}</Tag>
          )} />
          <Table.Column title="操作" render={(_: unknown, r: { id: string }) => (
            <Popconfirm title="确定删除？" onConfirm={() => handleDeleteTask(r.id)}>
              <Button danger icon={<DeleteOutlined />} size="small">删除</Button>
            </Popconfirm>
          )} />
        </Table>
      </Card>

      <Modal title="创建监控任务" open={taskModal} onCancel={() => setTaskModal(false)} onOk={() => taskForm.submit()}>
        <Form form={taskForm} layout="vertical" onFinish={handleCreateTask}
              initialValues={{ cron_expr: '0 18 * * 1-5', universe_type: 'all', dimensions: ['financial', 'industry', 'valuation'] }}>
          <Form.Item name="name" label="任务名称"><Input placeholder="每日扫描" /></Form.Item>
          <Form.Item name="cron_expr" label="Cron表达式"><Input placeholder="0 18 * * 1-5" /></Form.Item>
          <Form.Item name="universe_type" label="扫描范围">
            <Select options={[{ label: '全市场', value: 'all' }, { label: '仅关注', value: 'watchlist' }]} />
          </Form.Item>
          <Form.Item name="dimensions" label="评估维度">
            <Select mode="multiple" options={[
              { label: '财务成长性', value: 'financial' },
              { label: '行业赛道', value: 'industry' },
              { label: '估值合理性', value: 'valuation' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="添加推送渠道" open={channelModal} onCancel={() => setChannelModal(false)} onOk={() => channelForm.submit()}>
        <Form form={channelForm} layout="vertical" onFinish={handleCreateChannel}>
          <Form.Item name="name" label="渠道名称"><Input placeholder="我的企微机器人" /></Form.Item>
          <Form.Item name="type" label="渠道类型" rules={[{ required: true }]}>
            <Select options={channelTypeOptions} />
          </Form.Item>
          <Form.Item name="webhook_url" label="Webhook URL" rules={[{ required: true }]}>
            <Input placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Monitoring;
