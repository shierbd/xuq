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
} from 'antd';
import {
  ReloadOutlined,
  TranslationOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import ProductTable from '../../components/ProductTable';
import {
  getProducts,
  getStatistics,
  getUniqueTags,
  translateProducts,
  translateProductsSync,
} from '../../api/products';
import './ProductManagement.css';

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
    min_price: null,
    max_price: null,
    min_review_count: null,
    tags: [],
    sort_by: 'product_id',
    sort_order: 'desc',
  });

  // 高级筛选展开状态
  const [advancedFilterVisible, setAdvancedFilterVisible] = useState(false);

  // 选中的商品
  const [selectedProductIds, setSelectedProductIds] = useState([]);

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
          </Space>

          {/* 高级筛选 */}
          {advancedFilterVisible && (
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
              <Space wrap>
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
                  placeholder="最低评价数"
                  type="number"
                  style={{ width: 120 }}
                  value={filters.min_review_count}
                  onChange={(e) => handleFilterChange('min_review_count', e.target.value ? parseInt(e.target.value) : null)}
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

        {/* 商品表格 */}
        <Card>
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
        </Card>
      </div>
    </div>
  );
};

export default ProductManagement;
