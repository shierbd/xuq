/**
 * [REQ-013] P6.1: 商品数据可视化组件
 * 使用 ECharts 展示商品统计数据
 */
import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Row, Col, Spin, message } from 'antd';
import axios from 'axios';

const ProductVisualization = () => {
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null);

    useEffect(() => {
        fetchVisualizationData();
    }, []);

    const fetchVisualizationData = async () => {
        try {
            setLoading(true);
            const response = await axios.get('http://localhost:8000/api/products/visualization/data');
            if (response.data.success) {
                setData(response.data.data);
            } else {
                message.error('获取可视化数据失败');
            }
        } catch (error) {
            console.error('获取可视化数据失败:', error);
            message.error('获取可视化数据失败');
        } finally {
            setLoading(false);
        }
    };

    // 1. 类别大小分布（柱状图）
    const getClusterDistributionOption = () => {
        if (!data || !data.cluster_distribution) return {};

        return {
            title: {
                text: '类别大小分布 (Top 20)',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            xAxis: {
                type: 'category',
                data: data.cluster_distribution.map(item => item.name),
                axisLabel: {
                    rotate: 45,
                    interval: 0,
                    fontSize: 10
                }
            },
            yAxis: {
                type: 'value',
                name: '商品数量'
            },
            series: [{
                data: data.cluster_distribution.map(item => item.value),
                type: 'bar',
                itemStyle: {
                    color: '#5470c6'
                }
            }]
        };
    };

    // 2. 评分分布（直方图）
    const getRatingDistributionOption = () => {
        if (!data || !data.rating_distribution) return {};

        return {
            title: {
                text: '评分分布',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis'
            },
            xAxis: {
                type: 'category',
                data: data.rating_distribution.map(item => item.rating.toFixed(1)),
                name: '评分'
            },
            yAxis: {
                type: 'value',
                name: '商品数量'
            },
            series: [{
                data: data.rating_distribution.map(item => item.count),
                type: 'bar',
                itemStyle: {
                    color: '#91cc75'
                }
            }]
        };
    };

    // 3. 价格分布（柱状图）
    const getPriceDistributionOption = () => {
        if (!data || !data.price_distribution) return {};

        return {
            title: {
                text: '价格分布',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            xAxis: {
                type: 'category',
                data: data.price_distribution.map(item => item.range),
                name: '价格区间'
            },
            yAxis: {
                type: 'value',
                name: '商品数量'
            },
            series: [{
                data: data.price_distribution.map(item => item.count),
                type: 'bar',
                itemStyle: {
                    color: '#fac858'
                }
            }]
        };
    };

    // 4. 交付形式分布（饼图）
    const getDeliveryTypeDistributionOption = () => {
        if (!data || !data.delivery_type_distribution) return {};

        return {
            title: {
                text: '交付形式分布 (Top 15)',
                left: 'center'
            },
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c} ({d}%)'
            },
            legend: {
                orient: 'vertical',
                right: 10,
                top: 'middle',
                type: 'scroll'
            },
            series: [{
                name: '交付形式',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 16,
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: data.delivery_type_distribution.map(item => ({
                    name: item.type,
                    value: item.count
                }))
            }]
        };
    };

    // 5. 评价数分布（柱状图）
    const getReviewDistributionOption = () => {
        if (!data || !data.review_distribution) return {};

        return {
            title: {
                text: '评价数分布',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            xAxis: {
                type: 'category',
                data: data.review_distribution.map(item => item.range),
                name: '评价数区间'
            },
            yAxis: {
                type: 'value',
                name: '商品数量'
            },
            series: [{
                data: data.review_distribution.map(item => item.count),
                type: 'bar',
                itemStyle: {
                    color: '#ee6666'
                }
            }]
        };
    };

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" tip="加载可视化数据中..." />
            </div>
        );
    }

    if (!data) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <p>暂无可视化数据</p>
            </div>
        );
    }

    return (
        <div style={{ padding: '20px' }}>
            <Row gutter={[16, 16]}>
                {/* 类别大小分布 */}
                <Col span={24}>
                    <Card>
                        <ReactECharts
                            option={getClusterDistributionOption()}
                            style={{ height: '400px' }}
                        />
                    </Card>
                </Col>

                {/* 评分分布 */}
                <Col span={12}>
                    <Card>
                        <ReactECharts
                            option={getRatingDistributionOption()}
                            style={{ height: '350px' }}
                        />
                    </Card>
                </Col>

                {/* 价格分布 */}
                <Col span={12}>
                    <Card>
                        <ReactECharts
                            option={getPriceDistributionOption()}
                            style={{ height: '350px' }}
                        />
                    </Card>
                </Col>

                {/* 交付形式分布 */}
                <Col span={12}>
                    <Card>
                        <ReactECharts
                            option={getDeliveryTypeDistributionOption()}
                            style={{ height: '400px' }}
                        />
                    </Card>
                </Col>

                {/* 评价数分布 */}
                <Col span={12}>
                    <Card>
                        <ReactECharts
                            option={getReviewDistributionOption()}
                            style={{ height: '400px' }}
                        />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default ProductVisualization;
