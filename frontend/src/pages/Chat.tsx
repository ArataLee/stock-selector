import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Typography, Card, Space, message } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined } from '@ant-design/icons';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: '你好！我是A股成长股分析助手。你可以问我关于选股、财务分析、行业趋势等问题。' },
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    try {
      const response = await fetch('/api/llm/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: input }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errData.detail || `HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let assistantContent = '';
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n').filter(l => l.startsWith('data: '));
        for (const line of lines) {
          const token = line.slice(6);
          assistantContent += token;
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: 'assistant', content: assistantContent };
            return updated;
          });
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '未知错误';
      message.error(`发送失败: ${msg}`);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 180px)' }}>
      <Typography.Title level={3}>AI对话</Typography.Title>

      <Card style={{ flex: 1, marginBottom: 16, overflow: 'auto' }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 16, display: 'flex', gap: 12 }}>
            <div style={{ fontSize: 20 }}>
              {m.role === 'user' ? <UserOutlined /> : <RobotOutlined style={{ color: '#1890ff' }} />}
            </div>
            <div style={{ flex: 1, background: m.role === 'assistant' ? '#f6f8fa' : '#e6f7ff', padding: '8px 16px', borderRadius: 8, whiteSpace: 'pre-wrap' }}>
              {m.content || (m.role === 'assistant' && '...')}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </Card>

      <Space.Compact style={{ width: '100%' }}>
        <Input
          value={input}
          onChange={e => setInput(e.target.value)}
          onPressEnter={handleSend}
          placeholder="输入你的问题..."
          size="large"
        />
        <Button type="primary" icon={<SendOutlined />} onClick={handleSend} size="large">
          发送
        </Button>
      </Space.Compact>
    </div>
  );
};

export default Chat;
