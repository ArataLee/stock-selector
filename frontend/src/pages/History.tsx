import React from 'react';
import { Typography, Empty } from 'antd';

const History: React.FC = () => {
  return (
    <div>
      <Typography.Title level={3}>筛选历史</Typography.Title>
      <Empty description="暂无筛选历史">
        <Typography.Paragraph type="secondary">
          完成选股筛选后，结果将显示在这里，方便回顾和对比。
        </Typography.Paragraph>
      </Empty>
    </div>
  );
};

export default History;
