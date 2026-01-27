/**
 * 导入历史页面组件
 */
import React from 'react';
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Modal,
  Descriptions,
} from 'antd';
import {
  HistoryOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { getImportLogs, getImportLog } from '../api/import_export';
import './ImportHistory.css';

const ImportHistory = () => {
  const [selectedLog, setSelectedLog] = React.useState(null);
  const [detailVisible, setDetailVisible] = React.useState(false);

  // 获取导入历史
  const { data: logsData, isLoading } = useQuery({
    queryKey: ['import-logs'],
    queryFn: () => getImportLogs(50, 0),
  });

  // 查看详情
  const handleViewDetail = async (logId) => {
    try {
      const log = await getImportLog(logId);
      setSelectedLog(log);
      setDetailVisible(true);
    } catch (error) {
      console.error('获取导入记录详情失败:', error);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'import_log_id',
      key: 'import_log_id',
      width: 80,
    },
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 100,
      render: (platform) => (
        <Tag color="blue">{platform}</Tag>
      ),
    },
    {
      title: '总行数',
      dataIndex: 'total_rows',
      key: 'total_rows',
      width: 100,
    },
    {
      title: '成功导入',
      dataIndex: 'imported_rows',
      key: 'imported_rows',
      width: 100,
      render: (count) => (
        <span style={{ color: '#52c41a' }}>
          <CheckCircleOutlined /> {count}
        </span>
      ),
    },
    {
      title: '跳过',
      dataIndex: 'skipped_rows',
      key: 'skipped_rows',
      width: 100,
      render: (count) => (
        <span style={{ color: '#faad14' }}>
          {count}
        </span>
      ),
    },
    {
      title: '导入时间',
      dataIndex: 'imported_at',
      key: 'imported_at',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record.import_log_id)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  // 解析字段映射
  const parseFieldMapping = (mappingStr) => {
    if (!mappingStr) return [];
    try {
      const mapping = JSON.parse(mappingStr);
      return Object.entries(mapping).map(([col, field]) => ({
        column: col,
        field: field,
      }));
    } catch (error) {
      return [];
    }
  };

  return (
    <div className="import-history">
      <Card
        title={
          <span>
            <HistoryOutlined /> 导入历史
          </span>
        }
        className="history-card"
      >
        <Table
          dataSource={logsData}
          columns={columns}
          rowKey="import_log_id"
          loading={isLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 详情Modal */}
      <Modal
        title="导入记录详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedLog && (
          <div>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="导入ID">
                {selectedLog.import_log_id}
              </Descriptions.Item>
              <Descriptions.Item label="文件名">
                {selectedLog.filename}
              </Descriptions.Item>
              <Descriptions.Item label="平台">
                <Tag color="blue">{selectedLog.platform}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="导入时间">
                {new Date(selectedLog.imported_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
              <Descriptions.Item label="总行数">
                {selectedLog.total_rows}
              </Descriptions.Item>
              <Descriptions.Item label="成功导入">
                <span style={{ color: '#52c41a' }}>
                  <CheckCircleOutlined /> {selectedLog.imported_rows}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="跳过行数">
                <span style={{ color: '#faad14' }}>
                  {selectedLog.skipped_rows}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="成功率">
                {selectedLog.total_rows > 0
                  ? `${((selectedLog.imported_rows / selectedLog.total_rows) * 100).toFixed(1)}%`
                  : '0%'}
              </Descriptions.Item>
            </Descriptions>

            {selectedLog.field_mapping && (
              <div style={{ marginTop: 24 }}>
                <h4>字段映射配置</h4>
                <Table
                  dataSource={parseFieldMapping(selectedLog.field_mapping)}
                  columns={[
                    {
                      title: '列',
                      dataIndex: 'column',
                      key: 'column',
                    },
                    {
                      title: '映射字段',
                      dataIndex: 'field',
                      key: 'field',
                    },
                  ]}
                  pagination={false}
                  size="small"
                  rowKey="column"
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ImportHistory;
