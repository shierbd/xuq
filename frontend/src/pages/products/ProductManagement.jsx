/**
 * 商品管理主页面
 */
import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Space,
  Button,
  Select,
  Input,
  Pagination,
  Statistic,
  Row,
  Col,
  message,
  Modal,
  Tabs,
} from 'antd';
import {
  ReloadOutlined,
  TranslationOutlined,
  FilterOutlined,
  BarChartOutlined,
  TableOutlined,
} from '@ant-design/icons';
import ProductTable from '../../components/ProductTable';
import ProductVisualization from '../../components/ProductVisualization';
import ClusterOverview from '../../components/ClusterOverview';
import {
  getProducts,
  getStatistics,
  getUniqueTags,
  translateProducts,
  translateProductsSync,
} from '../../api/products';
import {
  analyzeDemands,
  getDemandAnalysisStatistics,
} from '../../api/demand_analysis';
import {
  identifyProducts,
  getDeliveryIdentificationStatistics,
} from '../../api/delivery_identification';
import {
  extractAllAttributes,
  extractMissingAttributes,
  getAttributeExtractionStatistics,
} from '../../api/attribute_extraction';
import {
  analyzeAllTopProducts,
  getAnalysisStatistics,
} from '../../api/top_product_analysis';
import './ProductManagement.css';
import axios from 'axios';

const { Option } = Select;

const ProductManagement = () => {
  const queryClient = useQueryClient();

  // 筛选状态
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 50,
    platform: null,
    ai_status: null,
    translation_status: null,
    search: '',
    cluster_name: '',
    min_price: null,
    max_price: null,
    min_rating: null,
    max_rating: null,
    min_review_count: null,
    max_review_count: null,
    tags: [],
    sort_by: 'product_id',
    sort_order: 'desc',
  });

  // 高级筛选展开状态
  const [advancedFilterVisible, setAdvancedFilterVisible] = useState(false);

  // 选中的商品
  const [selectedProductIds, setSelectedProductIds] = useState([]);

  // [REQ-013] P6.1: Tab切换状态
  const [activeTab, setActiveTab] = useState('list');

  // [REQ-003] P2.1: 聚类状态
  const [clusterLoading, setClusterLoading] = useState(false);

  // [REQ-004] P3.1: 需求分析状态
  const [demandAnalysisLoading, setDemandAnalysisLoading] = useState(false);

  // [REQ-005] P3.2: 交付产品识别状态
  const [deliveryIdentificationLoading, setDeliveryIdentificationLoading] = useState(false);

  // [REQ-010] P5.1: 属性提取状态
  const [attributeExtractionLoading, setAttributeExtractionLoading] = useState(false);

  // [REQ-011] P5.2: Top商品AI分析状态
  const [topProductAnalysisLoading, setTopProductAnalysisLoading] = useState(false);

  // [REQ-012] P5.3: AI辅助兜底状态
  const [aiAssistLoading, setAiAssistLoading] = useState(false);

  // [REQ-003] P2.1: 开始聚类
  const handleStartClustering = async () => {
    Modal.confirm({
      title: '确认聚类',
      content: '确定要对所有商品进行语义聚类分析吗？这可能需要几分钟时间。',
      onOk: async () => {
        try {
          setClusterLoading(true);
          message.loading({ content: '正在进行聚类分析...', key: 'clustering', duration: 0 });

          const response = await axios.post('/api/products/cluster', {
            min_cluster_size: 15,
            min_samples: 5,
            use_cache: true,
          });

          message.destroy('clustering');

          if (response.data.success) {
            message.success('聚类分析完成！');
            // 刷新数据
            refetchProducts();
            // 切换到聚类结果Tab
            setActiveTab('clusters');
          } else {
            message.error(response.data.message || '聚类分析失败');
          }
        } catch (error) {
          message.destroy('clustering');
          console.error('聚类失败:', error);
          message.error('聚类分析失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setClusterLoading(false);
        }
      },
    });
  };

  // [REQ-004] P3.1: 需求分析
  const handleAnalyzeDemands = async () => {
    // 创建自定义对话框
    let maxClusters = null;
    let skipAnalyzed = true;

    Modal.confirm({
      title: '需求分析配置',
      content: (
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4 }}>分析数量（留空表示不限制）：</label>
            <Input
              type="number"
              placeholder="例如：10、50、100"
              onChange={(e) => {
                maxClusters = e.target.value ? parseInt(e.target.value) : null;
              }}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'flex', alignItems: 'center' }}>
              <input
                type="checkbox"
                defaultChecked={true}
                onChange={(e) => {
                  skipAnalyzed = e.target.checked;
                }}
                style={{ marginRight: 8 }}
              />
              只分析未分析的簇（节省成本）
            </label>
          </div>
          <div style={{ color: '#666', fontSize: '12px', marginTop: 12 }}>
            提示：每个簇分析成本约 $0.0001，预计总成本约 $0.14
          </div>
        </div>
      ),
      width: 500,
      onOk: async () => {
        try {
          setDemandAnalysisLoading(true);
          message.loading({ content: '正在进行需求分析...', key: 'analyzing', duration: 0 });

          const response = await analyzeDemands({
            cluster_ids: null,
            top_n: 10,
            batch_size: 5,
            ai_provider: 'deepseek',
            max_clusters: maxClusters,
            skip_analyzed: skipAnalyzed,
            force_reanalyze: false
          });

          message.destroy('analyzing');

          if (response.success) {
            message.success('需求分析完成！');
            queryClient.invalidateQueries(['demandAnalysisStats']);
            refetchProducts();
          } else {
            message.error(response.message || '需求分析失败');
          }
        } catch (error) {
          message.destroy('analyzing');
          console.error('需求分析失败:', error);
          message.error('需求分析失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setDemandAnalysisLoading(false);
        }
      },
    });
  };

  // [REQ-004] P3.1: 重新分析已分析的簇
  const handleReanalyzeDemands = async () => {
    let maxClusters = null;

    Modal.confirm({
      title: '重新分析已分析的簇',
      content: (
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4 }}>重新分析数量（留空表示全部）：</label>
            <Input
              type="number"
              placeholder="例如：10、50、100"
              onChange={(e) => {
                maxClusters = e.target.value ? parseInt(e.target.value) : null;
              }}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: 12 }}>
            ⚠️ 警告：这将覆盖已有的分析结果！
          </div>
        </div>
      ),
      width: 500,
      okText: '确认重新分析',
      okType: 'danger',
      onOk: async () => {
        try {
          setDemandAnalysisLoading(true);
          message.loading({ content: '正在重新分析...', key: 'reanalyzing', duration: 0 });

          const response = await analyzeDemands({
            cluster_ids: null,
            top_n: 10,
            batch_size: 5,
            ai_provider: 'deepseek',
            max_clusters: maxClusters,
            skip_analyzed: false,
            force_reanalyze: true
          });

          message.destroy('reanalyzing');

          if (response.success) {
            message.success('重新分析完成！');
            queryClient.invalidateQueries(['demandAnalysisStats']);
            refetchProducts();
          } else {
            message.error(response.message || '重新分析失败');
          }
        } catch (error) {
          message.destroy('reanalyzing');
          console.error('重新分析失败:', error);
          message.error('重新分析失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setDemandAnalysisLoading(false);
        }
      },
    });
  };

  // [REQ-005] P3.2: 交付产品识别
  const handleIdentifyDelivery = async () => {
    Modal.confirm({
      title: '确认交付产品识别',
      content: '确定要识别所有商品的交付形式吗？这将使用关键词规则和AI识别。',
      onOk: async () => {
        try {
          setDeliveryIdentificationLoading(true);
          message.loading({ content: '正在识别交付产品...', key: 'identifying', duration: 0 });

          const response = await identifyProducts({
            product_ids: null,
            use_ai_for_unmatched: false,
            batch_size: 100,
            ai_provider: 'deepseek'
          });

          message.destroy('identifying');

          if (response.success) {
            message.success('交付产品识别完成！');
            queryClient.invalidateQueries(['deliveryIdentificationStats']);
            refetchProducts();
          } else {
            message.error(response.message || '交付产品识别失败');
          }
        } catch (error) {
          message.destroy('identifying');
          console.error('交付产品识别失败:', error);
          message.error('交付产品识别失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setDeliveryIdentificationLoading(false);
        }
      },
    });
  };

  // [REQ-010] P5.1: 属性提取
  const handleExtractAttributes = async () => {
    Modal.confirm({
      title: '确认属性提取',
      content: '确定要提取所有商品的属性吗？这将使用代码规则提取交付形式和关键词。',
      onOk: async () => {
        try {
          setAttributeExtractionLoading(true);
          message.loading({ content: '正在提取商品属性...', key: 'extracting', duration: 0 });

          const response = await extractAllAttributes({
            batch_size: 100
          });

          message.destroy('extracting');

          if (response.success) {
            message.success('属性提取完成！');
            queryClient.invalidateQueries(['attributeExtractionStats']);
            refetchProducts();
          } else {
            message.error(response.message || '属性提取失败');
          }
        } catch (error) {
          message.destroy('extracting');
          console.error('属性提取失败:', error);
          message.error('属性提取失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setAttributeExtractionLoading(false);
        }
      },
    });
  };

  // [REQ-011] P5.2: Top商品AI深度分析
  const handleAnalyzeTopProducts = async () => {
    Modal.confirm({
      title: '确认Top商品AI分析',
      content: '确定要对所有簇的Top 3商品进行AI深度分析吗？这将调用AI分析用户需求、验证交付形式和补充关键词。预计成本：$1.5-3。',
      onOk: async () => {
        try {
          setTopProductAnalysisLoading(true);
          message.loading({ content: '正在分析Top商品...', key: 'analyzing', duration: 0 });

          const response = await analyzeAllTopProducts(3, 'deepseek');

          message.destroy('analyzing');

          if (response.success) {
            message.success('Top商品分析完成！');
            queryClient.invalidateQueries(['topProductAnalysisStats']);
            refetchProducts();
          } else {
            message.error(response.message || 'Top商品分析失败');
          }
        } catch (error) {
          message.destroy('analyzing');
          console.error('Top商品分析失败:', error);
          message.error('Top商品分析失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setTopProductAnalysisLoading(false);
        }
      },
    });
  };

  // [REQ-012] P5.3: AI辅助兜底
  const handleAiAssist = async () => {
    Modal.confirm({
      title: '确认AI辅助兜底',
      content: '确定要对代码规则无法识别的商品使用AI识别交付形式吗？这将处理所有delivery_type为空的商品。预计成本：$0.2-0.5。',
      onOk: async () => {
        try {
          setAiAssistLoading(true);
          message.loading({ content: '正在使用AI识别...', key: 'aiAssisting', duration: 0 });

          const response = await extractMissingAttributes({
            max_products: null,
            batch_size: 10
          });

          message.destroy('aiAssisting');

          if (response.success) {
            message.success('AI辅助识别完成！');
            queryClient.invalidateQueries(['attributeExtractionStats']);
            refetchProducts();
          } else {
            message.error(response.message || 'AI辅助识别失败');
          }
        } catch (error) {
          message.destroy('aiAssisting');
          console.error('AI辅助识别失败:', error);
          message.error('AI辅助识别失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setAiAssistLoading(false);
        }
      },
    });
  };

  // 获取商品列表
  const {
    data: productsData,
    isLoading: productsLoading,
    refetch: refetchProducts,
  } = useQuery({
    queryKey: ['products', filters],
    queryFn: () => getProducts(filters),
  });

  // 获取统计信息
  const { data: statsData } = useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
  });

  // 获取标签列表
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: getUniqueTags,
  });

  // [REQ-004] P3.1: 获取需求分析统计
  const { data: demandAnalysisStats } = useQuery({
    queryKey: ['demandAnalysisStats'],
    queryFn: getDemandAnalysisStatistics,
  });

  // [REQ-005] P3.2: 获取交付产品识别统计
  const { data: deliveryIdentificationStats } = useQuery({
    queryKey: ['deliveryIdentificationStats'],
    queryFn: getDeliveryIdentificationStatistics,
  });

  // [REQ-010] P5.1: 获取属性提取统计
  const { data: attributeExtractionStats } = useQuery({
    queryKey: ['attributeExtractionStats'],
    queryFn: getAttributeExtractionStatistics,
  });

  // [REQ-011] P5.2: 获取Top商品AI分析统计
  const { data: topProductAnalysisStats } = useQuery({
    queryKey: ['topProductAnalysisStats'],
    queryFn: getAnalysisStatistics,
  });

  // 翻译Mutation
  const translateMutation = useMutation({
    mutationFn: translateProducts,
    onSuccess: () => {
      message.success('翻译任务已提交，正在后台处理');
      queryClient.invalidateQueries(['products']);
    },
    onError: (error) => {
      message.error(`翻译失败: ${error.message}`);
    },
  });

  // 同步翻译Mutation
  const translateSyncMutation = useMutation({
    mutationFn: translateProductsSync,
    onSuccess: (data) => {
      message.success(data.message);
      queryClient.invalidateQueries(['products']);
      setSelectedProductIds([]);
    },
    onError: (error) => {
      message.error(`翻译失败: ${error.message}`);
    },
  });

  // 处理筛选变化
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: 1, // 重置到第一页
    }));
  };

  // 处理分页变化
  const handlePageChange = (page, pageSize) => {
    setFilters(prev => ({
      ...prev,
      page,
      page_size: pageSize,
    }));
  };

  // 处理选中变化
  const handleSelectionChange = useCallback((selectedIds) => {
    setSelectedProductIds(selectedIds);
  }, []);

  // 翻译选中商品
  const handleTranslateSelected = () => {
    if (selectedProductIds.length === 0) {
      message.warning('请先选择要翻译的商品');
      return;
    }

    if (selectedProductIds.length <= 10) {
      // 少量商品使用同步翻译
      Modal.confirm({
        title: '确认翻译',
        content: `确定要翻译选中的 ${selectedProductIds.length} 个商品吗？`,
        onOk: () => {
          translateSyncMutation.mutate(selectedProductIds);
        },
      });
    } else {
      // 大量商品使用异步翻译
      Modal.confirm({
        title: '确认翻译',
        content: `确定要翻译选中的 ${selectedProductIds.length} 个商品吗？翻译将在后台进行。`,
        onOk: () => {
          translateMutation.mutate(selectedProductIds);
        },
      });
    }
  };

  // 翻译当前页
  const handleTranslateCurrentPage = () => {
    const currentPageIds = productsData?.items?.map(item => item.product_id) || [];
    if (currentPageIds.length === 0) {
      message.warning('当前页没有商品');
      return;
    }

    Modal.confirm({
      title: '确认翻译',
      content: `确定要翻译当前页的 ${currentPageIds.length} 个商品吗？`,
      onOk: () => {
        if (currentPageIds.length <= 10) {
          translateSyncMutation.mutate(currentPageIds);
        } else {
          translateMutation.mutate(currentPageIds);
        }
      },
    });
  };

  // 翻译未完成的商品
  const handleTranslateUncompleted = () => {
    const uncompletedIds = productsData?.items
      ?.filter(item => !item.translation_status || item.translation_status !== 'completed')
      ?.map(item => item.product_id) || [];

    if (uncompletedIds.length === 0) {
      message.info('当前页所有商品都已翻译');
      return;
    }

    Modal.confirm({
      title: '确认翻译',
      content: `确定要翻译当前页未完成的 ${uncompletedIds.length} 个商品吗？`,
      onOk: () => {
        if (uncompletedIds.length <= 10) {
          translateSyncMutation.mutate(uncompletedIds);
        } else {
          translateMutation.mutate(uncompletedIds);
        }
      },
    });
  };

  return (
    <div className="product-management">
      <div className="content">
        {/* 统计卡片 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总商品数"
                value={statsData?.total || 0}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已标注"
                value={statsData?.by_ai_status?.completed || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="待标注"
                value={statsData?.by_ai_status?.pending || 0}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已选中"
                value={selectedProductIds.length}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 筛选器 */}
        <Card className="filter-card" style={{ marginBottom: 16 }}>
          <Space wrap>
            <Select
              placeholder="平台"
              style={{ width: 120 }}
              allowClear
              value={filters.platform}
              onChange={(value) => handleFilterChange('platform', value)}
            >
              <Option value="etsy">Etsy</Option>
              <Option value="amazon">Amazon</Option>
              <Option value="gumroad">Gumroad</Option>
            </Select>

            <Select
              placeholder="AI状态"
              style={{ width: 120 }}
              allowClear
              value={filters.ai_status}
              onChange={(value) => handleFilterChange('ai_status', value)}
            >
              <Option value="completed">已完成</Option>
              <Option value="pending">待处理</Option>
              <Option value="failed">失败</Option>
            </Select>

            <Select
              placeholder="翻译状态"
              style={{ width: 120 }}
              allowClear
              value={filters.translation_status}
              onChange={(value) => handleFilterChange('translation_status', value)}
            >
              <Option value="completed">已翻译</Option>
              <Option value="pending">翻译中</Option>
              <Option value="failed">失败</Option>
            </Select>

            <Input
              placeholder="搜索商品名称"
              style={{ width: 200 }}
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              allowClear
            />

            <Select
              placeholder="排序方式"
              style={{ width: 150 }}
              value={`${filters.sort_by}_${filters.sort_order}`}
              onChange={(value) => {
                const lastUnderscoreIndex = value.lastIndexOf('_');
                const sort_by = value.substring(0, lastUnderscoreIndex);
                const sort_order = value.substring(lastUnderscoreIndex + 1);
                setFilters(prev => ({ ...prev, sort_by, sort_order, page: 1 }));
              }}
            >
              <Option value="product_id_desc">ID (降序)</Option>
              <Option value="product_id_asc">ID (升序)</Option>
              <Option value="price_desc">价格 (高到低)</Option>
              <Option value="price_asc">价格 (低到高)</Option>
              <Option value="rating_desc">评分 (高到低)</Option>
              <Option value="rating_asc">评分 (低到高)</Option>
              <Option value="review_count_desc">评价数 (多到少)</Option>
              <Option value="review_count_asc">评价数 (少到多)</Option>
            </Select>

            <Button
              icon={<FilterOutlined />}
              onClick={() => setAdvancedFilterVisible(!advancedFilterVisible)}
            >
              {advancedFilterVisible ? '收起' : '高级筛选'}
            </Button>

            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetchProducts()}
            >
              刷新
            </Button>

            <Button
              type="primary"
              icon={<TranslationOutlined />}
              onClick={handleTranslateSelected}
              disabled={selectedProductIds.length === 0}
              loading={translateMutation.isPending || translateSyncMutation.isPending}
            >
              翻译选中 ({selectedProductIds.length})
            </Button>

            <Button
              icon={<TranslationOutlined />}
              onClick={handleTranslateCurrentPage}
              loading={translateMutation.isPending || translateSyncMutation.isPending}
            >
              翻译当前页
            </Button>

            <Button
              icon={<TranslationOutlined />}
              onClick={handleTranslateUncompleted}
              loading={translateMutation.isPending || translateSyncMutation.isPending}
            >
              翻译未完成
            </Button>

            <Button
              type="primary"
              danger
              onClick={handleStartClustering}
              loading={clusterLoading}
            >
              开始聚类
            </Button>

            <Button
              type="primary"
              onClick={handleAnalyzeDemands}
              loading={demandAnalysisLoading}
              style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
            >
              需求分析
            </Button>

            <Button
              onClick={handleReanalyzeDemands}
              loading={demandAnalysisLoading}
              style={{ borderColor: '#52c41a', color: '#52c41a' }}
            >
              重新分析
            </Button>

            <Button
              type="primary"
              onClick={handleIdentifyDelivery}
              loading={deliveryIdentificationLoading}
              style={{ backgroundColor: '#1890ff', borderColor: '#1890ff' }}
            >
              识别交付产品
            </Button>

            <Button
              type="primary"
              onClick={handleExtractAttributes}
              loading={attributeExtractionLoading}
              style={{ backgroundColor: '#722ed1', borderColor: '#722ed1' }}
            >
              提取属性
            </Button>

            <Button
              type="primary"
              onClick={handleAnalyzeTopProducts}
              loading={topProductAnalysisLoading}
              style={{ backgroundColor: '#fa8c16', borderColor: '#fa8c16' }}
            >
              Top商品AI分析
            </Button>

            <Button
              type="primary"
              onClick={handleAiAssist}
              loading={aiAssistLoading}
              style={{ backgroundColor: '#eb2f96', borderColor: '#eb2f96' }}
            >
              AI辅助兜底
            </Button>
          </Space>

          {/* 高级筛选 */}
          {advancedFilterVisible && (
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
              <Space wrap>
                <Input
                  placeholder="类别名称"
                  style={{ width: 150 }}
                  value={filters.cluster_name}
                  onChange={(e) => handleFilterChange('cluster_name', e.target.value)}
                  allowClear
                />
                <Input
                  placeholder="最低价格"
                  type="number"
                  style={{ width: 120 }}
                  value={filters.min_price}
                  onChange={(e) => handleFilterChange('min_price', e.target.value ? parseFloat(e.target.value) : null)}
                  prefix="$"
                />
                <Input
                  placeholder="最高价格"
                  type="number"
                  style={{ width: 120 }}
                  value={filters.max_price}
                  onChange={(e) => handleFilterChange('max_price', e.target.value ? parseFloat(e.target.value) : null)}
                  prefix="$"
                />
                <Input
                  placeholder="最低评分"
                  type="number"
                  style={{ width: 120 }}
                  value={filters.min_rating}
                  onChange={(e) => handleFilterChange('min_rating', e.target.value ? parseFloat(e.target.value) : null)}
                  min={0}
                  max={5}
                  step={0.1}
                />
                <Input
                  placeholder="最高评分"
                  type="number"
                  style={{ width: 120 }}
                  value={filters.max_rating}
                  onChange={(e) => handleFilterChange('max_rating', e.target.value ? parseFloat(e.target.value) : null)}
                  min={0}
                  max={5}
                  step={0.1}
                />
                <Input
                  placeholder="最低评价数"
                  type="number"
                  style={{ width: 120 }}
                  value={filters.min_review_count}
                  onChange={(e) => handleFilterChange('min_review_count', e.target.value ? parseInt(e.target.value) : null)}
                />
                <Input
                  placeholder="最高评价数"
                  type="number"
                  style={{ width: 120 }}
                  value={filters.max_review_count}
                  onChange={(e) => handleFilterChange('max_review_count', e.target.value ? parseInt(e.target.value) : null)}
                />
                <Select
                  mode="multiple"
                  placeholder="选择标签"
                  style={{ minWidth: 200 }}
                  value={filters.tags}
                  onChange={(value) => handleFilterChange('tags', value)}
                  maxTagCount={2}
                >
                  {tagsData?.tags?.map(tag => (
                    <Option key={tag} value={tag}>{tag}</Option>
                  ))}
                </Select>
                <Button
                  onClick={() => {
                    setFilters(prev => ({
                      ...prev,
                      min_price: null,
                      max_price: null,
                      min_review_count: null,
                      tags: [],
                      page: 1,
                    }));
                  }}
                >
                  清空高级筛选
                </Button>
              </Space>
            </div>
          )}
        </Card>

        {/* [REQ-013] P6.1: Tab切换 - 商品列表 / 数据可视化 */}
        <Card>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'list',
                label: (
                  <span>
                    <TableOutlined />
                    商品列表
                  </span>
                ),
                children: (
                  <>
                    <ProductTable
                      data={productsData?.items || []}
                      loading={productsLoading}
                      onSelectionChange={handleSelectionChange}
                      selectedRows={selectedProductIds}
                    />

                    {/* 分页 */}
                    <div style={{ marginTop: 16, textAlign: 'right' }}>
                      <Pagination
                        current={filters.page}
                        pageSize={filters.page_size}
                        total={productsData?.total || 0}
                        onChange={handlePageChange}
                        showSizeChanger
                        showQuickJumper
                        showTotal={(total) => `共 ${total} 条`}
                        pageSizeOptions={[10, 20, 50, 100, 200]}
                      />
                    </div>
                  </>
                ),
              },
              {
                key: 'visualization',
                label: (
                  <span>
                    <BarChartOutlined />
                    数据可视化
                  </span>
                ),
                children: <ProductVisualization />,
              },
              {
                key: 'clusters',
                label: (
                  <span>
                    <BarChartOutlined />
                    聚类结果
                  </span>
                ),
                children: <ClusterOverview />,
              },
            ]}
          />
        </Card>
      </div>
    </div>
  );
};

export default ProductManagement;
