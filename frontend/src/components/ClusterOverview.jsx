/**
 * [REQ-003] P2.2: 聚类结果展示组件
 * 展示所有簇的概览信息
 */
import React, { useEffect, useState } from 'react';
import { Card, Table, Statistic, Row, Col, Spin, message, Tag, Button, Space } from 'antd';
import { ClusterOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const ClusterOverview = () => {
    const [loading, setLoading] = useState(true);
    const [clusterData, setClusterData] = useState([]);
    const [statistics, setStatistics] = useState(null);

    useEffect(() => {
        fetchClusterData();
    }, []);

    const fetchClusterData = async () => {
        try {
            setLoading(true);

            // 获取簇汇总数据
            const summaryResponse = await axios.get('http://localhost:8000/api/products/cluster/summary');
            if (summaryResponse.data.success) {
                setClusterData(summaryResponse.data.data);
            }

            // 获取聚类统计信息
            const statsResponse = await axios.get('http://localhost:8000/api/products/clusters/statistics');
            if (statsResponse.data.success) {
                setStatistics(statsResponse.data.data);
            }
        } catch (error) {
            console.error('获取聚类数据失败:', error);
            message.error('获取聚类数据失败');
        } finally {
            setLoading(false);
        }
    };

    const columns = [
        {
            title: '簇ID',
            dataIndex: 'cluster_id',
            key: 'cluster_id',
            width: 80,
            render: (id) => (
                id === -1 ? (
                    <Tag color="red">噪音点</Tag>
                ) : (
                    <Tag color="blue">簇 {id}</Tag>
                )
            ),
        },
        {
            title: '簇大小',
            dataIndex: 'cluster_size',
            key: 'cluster_size',
            width: 100,
            sorter: (a, b) => a.cluster_size - b.cluster_size,
        },
        {
            title: '平均评分',
            dataIndex: 'avg_rating',
            key: 'avg_rating',
            width: 100,
            render: (rating) => rating ? rating.toFixed(2) : '-',
            sorter: (a, b) => (a.avg_rating || 0) - (b.avg_rating || 0),
        },
        {
            title: '平均价格',
            dataIndex: 'avg_price',
            key: 'avg_price',
            width: 100,
            render: (price) => price ? `$${price.toFixed(2)}` : '-',
            sorter: (a, b) => (a.avg_price || 0) - (b.avg_price || 0),
        },
        {
            title: '总评价数',
            dataIndex: 'total_reviews',
            key: 'total_reviews',
            width: 120,
            render: (reviews) => reviews ? reviews.toLocaleString() : '-',
            sorter: (a, b) => (a.total_reviews || 0) - (b.total_reviews || 0),
        },
        {
            title: '示例商品',
            dataIndex: 'example_products',
            key: 'example_products',
            ellipsis: true,
            render: (products) => (
                <div style={{ maxWidth: 400 }}>
                    {products && products.slice(0, 3).map((product, index) => (
                        <div key={index} style={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            fontSize: '12px',
                            color: '#666'
                        }}>
                            • {product}
                        </div>
                    ))}
                </div>
            ),
        },
    ];

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" tip="加载聚类数据中..." />
            </div>
        );
    }

    return (
        <div style={{ padding: '20px' }}>
            {/* 统计卡片 */}
            {statistics && (
                <Row gutter={16} style={{ marginBottom: 20 }}>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="总簇数"
                                value={statistics.total_clusters || 0}
                                prefix={<ClusterOutlined />}
                                valueStyle={{ color: '#3f8600' }}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="已聚类商品"
                                value={statistics.clustered_products || 0}
                                valueStyle={{ color: '#1890ff' }}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="噪音点"
                                value={statistics.noise_products || 0}
                                valueStyle={{ color: '#faad14' }}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="聚类覆盖率"
                                value={statistics.cluster_rate || 0}
                                suffix="%"
                                valueStyle={{ color: '#722ed1' }}
                            />
                        </Card>
                    </Col>
                </Row>
            )}

            {/* 簇列表 */}
            <Card
                title="簇概览"
                extra={
                    <Space>
                        <Button
                            icon={<ReloadOutlined />}
                            onClick={fetchClusterData}
                        >
                            刷新
                        </Button>
                    </Space>
                }
            >
                <Table
                    columns={columns}
                    dataSource={clusterData}
                    rowKey="cluster_id"
                    pagination={{
                        pageSize: 20,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `共 ${total} 个簇`,
                    }}
                />
            </Card>
        </div>
    );
};

export default ClusterOverview;
