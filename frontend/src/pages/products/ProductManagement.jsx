/**
 * 商品管理主页面
 */
import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Space,
  Button,
  Select,
  Input,
  InputNumber,
  Pagination,
  Statistic,
  Row,
  Col,
  message,
  Modal,
  Tabs,
  Form,
  Progress,
  Typography,
} from 'antd';
import {
  ReloadOutlined,
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
  updateProduct,
  deleteProduct,
  batchDeleteProducts,
} from '../../api/products';
import {
  analyzeDemands,
} from '../../api/demand_analysis';
import {
  identifyProducts,
} from '../../api/delivery_identification';
import {
  extractAllAttributes,
  extractMissingAttributes,
} from '../../api/attribute_extraction';
import {
  analyzeAllTopProducts,
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
    search: '',
    cluster_id: null,
    cluster_name: '',
    min_price: null,
    max_price: null,
    min_rating: null,
    max_rating: null,
    min_review_count: null,
    max_review_count: null,
    sort_by: 'product_id',
    sort_order: 'desc',
  });

  // 高级筛选展开状态
  const [advancedFilterVisible, setAdvancedFilterVisible] = useState(false);

  // 选中的商品
  const [selectedProductIds, setSelectedProductIds] = useState([]);

  // 编辑商品弹窗
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [editForm] = Form.useForm();

  // [REQ-013] P6.1: Tab切换状态
  const [activeTab, setActiveTab] = useState('list');

  // [REQ-003] P2.1: 聚类状态
  const [clusterLoading, setClusterLoading] = useState(false);

  // 生成簇关键词/词根（异步任务）
  const handleGenerateClusterKeywords = async () => {
    const config = {
      topN: 10,
      minWordLen: 3,
      method: 'tfidf',
      overwrite: true
    };

    Modal.confirm({
      title: '生成簇关键词/词根',
      content: (
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4 }}>Top 关键词数量</label>
            <InputNumber
              min={3}
              max={50}
              defaultValue={10}
              style={{ width: '100%' }}
              onChange={(value) => {
                config.topN = value || 10;
              }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4 }}>最小词长</label>
            <InputNumber
              min={2}
              max={10}
              defaultValue={3}
              style={{ width: '100%' }}
              onChange={(value) => {
                config.minWordLen = value || 3;
              }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', marginBottom: 4 }}>提取方法</label>
            <Select
              defaultValue="tfidf"
              style={{ width: '100%' }}
              onChange={(value) => {
                config.method = value;
              }}
            >
              <Option value="tfidf">TF-IDF（推荐）</Option>
              <Option value="tf">TF（频次）</Option>
            </Select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'flex', alignItems: 'center' }}>
              <input
                type="checkbox"
                defaultChecked={true}
                onChange={(e) => {
                  config.overwrite = e.target.checked;
                }}
                style={{ marginRight: 8 }}
              />
              覆盖已生成结果
            </label>
          </div>
        </div>
      ),
      width: 420,
      onOk: async () => {
        try {
          setKeywordTaskLoading(true);
          message.loading({ content: '正在提交关键词任务...', key: 'cluster-keywords', duration: 0 });

          const response = await axios.post('/api/products/cluster-keywords/async', {
            cluster_ids: null,
            top_n: config.topN,
            min_word_len: config.minWordLen,
            overwrite: config.overwrite,
            method: config.method
          });

          message.destroy('cluster-keywords');

          const taskId = response.data?.task_id;
          if (taskId) {
            startTaskPolling(taskId, '生成簇关键词', () => {
              setActiveTab('clusters');
            });
          } else {
            message.error(response.data?.message || '关键词任务提交失败');
          }
        } catch (error) {
          message.destroy('cluster-keywords');
          console.error('生成关键词失败:', error);
          message.error('生成关键词失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setKeywordTaskLoading(false);
        }
      },
    });
  };
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

  // Async task progress (cluster/keywords)
  const [taskModalOpen, setTaskModalOpen] = useState(false);
  const [taskProgress, setTaskProgress] = useState(0);
  const [taskMessage, setTaskMessage] = useState('');
  const [taskTitle, setTaskTitle] = useState('');
  const [taskStatus, setTaskStatus] = useState('pending');
  const [taskId, setTaskId] = useState('');
  const [keywordTaskLoading, setKeywordTaskLoading] = useState(false);
  const taskPollRef = useRef(null);

  const stopTaskPolling = useCallback(() => {
    if (taskPollRef.current) {
      clearInterval(taskPollRef.current);
      taskPollRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => stopTaskPolling();
  }, [stopTaskPolling]);

  const startTaskPolling = useCallback((id, title, onSuccess) => {
    stopTaskPolling();
    setTaskId(id);
    setTaskTitle(title);
    setTaskModalOpen(true);
    setTaskStatus('pending');
    setTaskProgress(0);
    setTaskMessage('queued');

    const poll = async () => {
      try {
        const response = await axios.get(`/api/tasks/${id}`);
        const task = response.data?.data;
        if (!task) return;
        setTaskMessage(task.message || task.status || '');
        setTaskStatus(task.status || 'pending');

        if (task.status === 'success') {
          stopTaskPolling();
          message.success(`${title}完成`);
          if (onSuccess) onSuccess(task);
          setTimeout(() => setTaskModalOpen(false), 800);
        } else if (task.status === 'failed') {
          stopTaskPolling();
          const errorMsg = task.error || 'unknown error';
          setTaskMessage(`failed: ${errorMsg}`);
          message.error(`${title}失败: ${errorMsg}`);
        }
      } catch (error) {
        stopTaskPolling();
        message.error('任务状态获取失败: ' + (error.response?.data?.detail || error.message));
      }
    };

    poll();
    taskPollRef.current = setInterval(poll, 2000);
  }, [stopTaskPolling]);

  // [REQ-002] 更新商品
  const updateMutation = useMutation({
    mutationFn: ({ productId, data }) => updateProduct(productId, data),
    onSuccess: () => {
      message.success('商品更新成功');
      setEditModalOpen(false);
      setEditingProduct(null);
      editForm.resetFields();
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['statistics']);
    },
    onError: (error) => {
      message.error('商品更新失败: ' + (error.response?.data?.detail || error.message));
    },
  });

  // [REQ-002] 删除商品
  const deleteMutation = useMutation({
    mutationFn: (productId) => deleteProduct(productId),
    onSuccess: () => {
      message.success('商品删除成功');
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['statistics']);
    },
    onError: (error) => {
      message.error('商品删除失败: ' + (error.response?.data?.detail || error.message));
    },
  });

  // [REQ-002] 批量删除商品
  const batchDeleteMutation = useMutation({
    mutationFn: (productIds) => batchDeleteProducts(productIds),
    onSuccess: (data) => {
      message.success(`已删除 ${deletedCount} 个商品`);
      setSelectedProductIds([]);
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['statistics']);
    },
    onError: (error) => {
      message.error('批量删除失败: ' + (error.response?.data?.detail || error.message));
    },
  });

  // [REQ-003] P2.1: 开始聚类
  const handleStartClustering = async () => {
    Modal.confirm({
      title: '确认聚类',
      content: '确认要对所有商品进行语义聚类分析吗？这将提交到后台任务，请稍等...',
      onOk: async () => {
        try {
          setClusterLoading(true);
          message.loading({ content: '正在提交聚类任务...', key: 'clustering', duration: 0 });

          const response = await axios.post('/api/products/cluster-large/async', null, {
            params: {
              batch_size: 1000,
              min_cluster_size: 10,
              min_samples: 3,
              use_cache: true
            }
          });

          message.destroy('clustering');

          const taskId = response.data?.task_id;
          if (taskId) {
            startTaskPolling(taskId, '聚类分析', () => {
              refetchProducts();
              setActiveTab('clusters');
            });
          } else {
            message.error(response.data?.message || '聚类任务提交失败');
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
    // 使用对象来存储配置，避免闭包问题
    const config = {
      maxClusters: null,
      skipAnalyzed: true
    };

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
                const value = e.target.value ? parseInt(e.target.value) : null;
                config.maxClusters = value;
                console.log('[DEBUG] Frontend: maxClusters changed to:', value);
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
                  config.skipAnalyzed = e.target.checked;
                  console.log('[DEBUG] Frontend: skipAnalyzed changed to:', e.target.checked);
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
          console.log('[DEBUG] Frontend: Sending request with config:', config);
          setDemandAnalysisLoading(true);
          message.loading({ content: '正在进行需求分析...', key: 'analyzing', duration: 0 });

          const response = await analyzeDemands({
            cluster_ids: null,
            top_n: 10,
            batch_size: 5,
            ai_provider: 'deepseek',
            max_clusters: config.maxClusters,
            skip_analyzed: config.skipAnalyzed,
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
    // 使用对象来存储配置，避免闭包问题
    const config = {
      maxClusters: null
    };

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
                const value = e.target.value ? parseInt(e.target.value) : null;
                config.maxClusters = value;
                console.log('[DEBUG] Frontend (Reanalyze): maxClusters changed to:', value);
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
          console.log('[DEBUG] Frontend (Reanalyze): Sending request with config:', config);
          setDemandAnalysisLoading(true);
          message.loading({ content: '正在重新分析...', key: 'reanalyzing', duration: 0 });

          const response = await analyzeDemands({
            cluster_ids: null,
            top_n: 10,
            batch_size: 5,
            ai_provider: 'deepseek',
            max_clusters: config.maxClusters,
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

  // 打开编辑弹窗
  const handleEditProduct = (product) => {
    setEditingProduct(product);
    editForm.setFieldsValue({
      product_name: product.product_name || '',
      shop_name: product.shop_name || '',
    });
    setEditModalOpen(true);
  };

  // 提交编辑
  const handleEditSubmit = async () => {
    if (!editingProduct) return;
    try {
      const values = await editForm.validateFields();
      updateMutation.mutate({
        productId: editingProduct.product_id,
        data: values,
      });
    } catch (error) {
      // 表单校验失败时保持弹窗打开
    }
  };

  // 删除单个商品
  const handleDeleteProduct = (product) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定删除商品 #${product.product_id} 吗？`,
      okType: 'danger',
      onOk: () => deleteMutation.mutateAsync(product.product_id)
        .then(() => {
          setSelectedProductIds(prev => prev.filter(id => id !== product.product_id));
        }),
    });
  };

  // 批量删除
  const handleBatchDelete = () => {
    if (!selectedProductIds.length) {
      message.warning('请先选择要删除的商品');
      return;
    }
    Modal.confirm({
      title: '确认批量删除',
      content: `确定删除选中的 ${selectedProductIds.length} 个商品吗？`,
      okType: 'danger',
      onOk: () => batchDeleteMutation.mutateAsync(selectedProductIds),
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
                value={statsData?.data?.total_products || 0}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均评分"
                value={statsData?.data?.rating_stats?.avg || 0}
                precision={2}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均价格"
                value={statsData?.data?.price_stats?.avg || 0}
                precision={2}
                prefix="$"
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
              danger
              onClick={handleStartClustering}
              loading={clusterLoading}
            >
              开始聚类
            </Button>

            <Button
              onClick={handleGenerateClusterKeywords}
              loading={keywordTaskLoading}
              style={{ borderColor: '#13c2c2', color: '#13c2c2' }}
            >
              生成簇关键词
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
            <Button
              danger
              onClick={handleBatchDelete}
              disabled={!selectedProductIds.length}
              loading={batchDeleteMutation.isPending}
            >
              批量删除
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
                  placeholder="簇ID"
                  type="number"
                  style={{ width: 120 }}
                  value={filters.cluster_id}
                  onChange={(e) => handleFilterChange('cluster_id', e.target.value ? parseInt(e.target.value, 10) : null)}
                  min={-1}
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
                <Button
                  onClick={() => {
                    setFilters(prev => ({
                      ...prev,
                      cluster_name: '',
                      cluster_id: null,
                      min_price: null,
                      max_price: null,
                      min_rating: null,
                      max_rating: null,
                      min_review_count: null,
                      max_review_count: null,
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
                      onEdit={handleEditProduct}
                      onDelete={handleDeleteProduct}
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

      <Modal
        title={taskTitle || '任务进度'}
        open={taskModalOpen}
        onCancel={() => setTaskModalOpen(false)}
        footer={null}
        maskClosable={taskStatus !== 'running'}
        closable={taskStatus !== 'running'}
      >
        <Progress
          percent={taskProgress}
          status={taskStatus === 'failed' ? 'exception' : taskStatus === 'success' ? 'success' : 'active'}
        />
        <div style={{ marginTop: 12 }}>
          <Typography.Text>{taskMessage || taskStatus}</Typography.Text>
        </div>
        <div style={{ marginTop: 8, color: '#999', fontSize: '12px' }}>Task ID: {taskId}</div>
      </Modal>

      <Modal
        title={editingProduct ? `编辑商品 #${editingProduct.product_id}` : '编辑商品'}
        open={editModalOpen}
        onCancel={() => {
          setEditModalOpen(false);
          setEditingProduct(null);
          editForm.resetFields();
        }}
        onOk={handleEditSubmit}
        okText="保存"
        confirmLoading={updateMutation.isPending}
      >
        <Form
          form={editForm}
          layout="vertical"
        >
          <Form.Item
            label="商品名称"
            name="product_name"
            rules={[{ required: true, message: '请输入商品名称' }]}
          >
            <Input placeholder="请输入商品名称" />
          </Form.Item>
          <Form.Item label="店铺名称" name="shop_name">
            <Input placeholder="请输入店铺名称" />
          </Form.Item>
          <Form.Item label="价格" name="price">
            <InputNumber
              min={0}
              step={0.01}
              style={{ width: '100%' }}
              placeholder="请输入价格"
            />
          </Form.Item>
          <Form.Item label="评分" name="rating">
            <InputNumber
              min={0}
              max={5}
              step={0.1}
              style={{ width: '100%' }}
              placeholder="请输入评分"
            />
          </Form.Item>
          <Form.Item label="评价数" name="review_count">
            <InputNumber
              min={0}
              step={1}
              style={{ width: '100%' }}
              placeholder="请输入评价数"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProductManagement;




