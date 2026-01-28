/**
 * 商品表格组件 - 使用TanStack Table + 虚拟滚动
 */
import React, { useMemo, useState, useRef, useEffect } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Checkbox, Tag, Button, Space, message } from 'antd';
import './ProductTable.css';

const ProductTable = ({
  data = [],
  loading = false,
  onSelectionChange,
  selectedRows = []
}) => {
  const [rowSelection, setRowSelection] = useState({});
  const tableContainerRef = useRef(null);

  // 同步外部选中状态
  useEffect(() => {
    const newSelection = {};
    selectedRows.forEach(id => {
      const index = data.findIndex(item => item.product_id === id);
      if (index !== -1) {
        newSelection[index] = true;
      }
    });

    // 只有当选中状态真正改变时才更新
    const currentKeys = Object.keys(rowSelection).filter(k => rowSelection[k]);
    const newKeys = Object.keys(newSelection).filter(k => newSelection[k]);

    if (currentKeys.length !== newKeys.length ||
        !currentKeys.every(k => newKeys.includes(k))) {
      setRowSelection(newSelection);
    }
  }, [selectedRows]); // 只依赖 selectedRows，不依赖 data

  // 定义表格列
  const columns = useMemo(
    () => [
      {
        id: 'select',
        header: ({ table }) => (
          <Checkbox
            checked={table.getIsAllRowsSelected()}
            indeterminate={table.getIsSomeRowsSelected()}
            onChange={table.getToggleAllRowsSelectedHandler()}
          />
        ),
        cell: ({ row }) => (
          <Checkbox
            checked={row.getIsSelected()}
            disabled={!row.getCanSelect()}
            onChange={row.getToggleSelectedHandler()}
          />
        ),
        size: 50,
      },
      {
        accessorKey: 'product_id',
        header: 'ID',
        size: 80,
      },
      {
        accessorKey: 'product_name',
        header: '商品名称',
        size: 300,
        cell: ({ getValue }) => (
          <div className="product-name" title={getValue()}>
            {getValue()}
          </div>
        ),
      },
      {
        accessorKey: 'product_name_cn',
        header: '中文名称',
        size: 200,
        cell: ({ getValue }) => (
          <div className="product-name-cn" title={getValue()}>
            {getValue() || '-'}
          </div>
        ),
      },
      {
        accessorKey: 'platform',
        header: '平台',
        size: 80,
        cell: ({ getValue }) => (
          <Tag color="blue">{getValue()}</Tag>
        ),
      },
      {
        accessorKey: 'price',
        header: '价格',
        size: 100,
        cell: ({ getValue }) => {
          const price = getValue();
          return price ? `$${price.toFixed(2)}` : '-';
        },
      },
      {
        accessorKey: 'rating',
        header: '评分',
        size: 80,
        cell: ({ getValue }) => {
          const rating = getValue();
          return rating ? rating.toFixed(1) : '-';
        },
      },
      {
        accessorKey: 'review_count',
        header: '评价数',
        size: 100,
        cell: ({ getValue }) => {
          const count = getValue();
          return count ? count.toLocaleString() : '-';
        },
      },
      {
        accessorKey: 'ai_analysis_status',
        header: 'AI状态',
        size: 100,
        cell: ({ getValue }) => {
          const status = getValue();
          const colorMap = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
          };
          return <Tag color={colorMap[status] || 'default'}>{status}</Tag>;
        },
      },
      {
        accessorKey: 'translation_status',
        header: '翻译状态',
        size: 100,
        cell: ({ getValue }) => {
          const status = getValue();
          if (!status) return <Tag>未翻译</Tag>;
          const colorMap = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
          };
          return <Tag color={colorMap[status] || 'default'}>{status}</Tag>;
        },
      },
      {
        accessorKey: 'tags',
        header: '标签',
        size: 250,
        cell: ({ getValue }) => {
          const tags = getValue();
          if (!tags || tags.length === 0) return '-';
          return (
            <div className="tags-container">
              {tags.slice(0, 3).map((tag, idx) => (
                <Tag key={idx} color="purple" style={{ marginBottom: 4 }}>
                  {tag}
                </Tag>
              ))}
              {tags.length > 3 && <span>+{tags.length - 3}</span>}
            </div>
          );
        },
      },
    ],
    []
  );

  // 创建表格实例
  const table = useReactTable({
    data,
    columns,
    state: {
      rowSelection,
    },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
  });

  // 虚拟滚动配置
  const { rows } = table.getRowModel();
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => 60,
    overscan: 10,
  });

  // 通知父组件选中状态变化
  useEffect(() => {
    const selectedIds = Object.keys(rowSelection)
      .filter(key => rowSelection[key])
      .map(key => data[parseInt(key)]?.product_id)
      .filter(Boolean);

    if (onSelectionChange) {
      onSelectionChange(selectedIds);
    }
  }, [rowSelection]); // 移除 data 和 onSelectionChange 依赖

  if (loading) {
    return <div className="loading">加载中...</div>;
  }

  return (
    <div className="product-table-container">
      <div className="table-wrapper" ref={tableContainerRef}>
        <table className="product-table">
          <thead>
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    style={{
                      width: `${header.getSize()}px`,
                      minWidth: `${header.getSize()}px`,
                      maxWidth: `${header.getSize()}px`
                    }}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map(virtualRow => {
              const row = rows[virtualRow.index];
              return (
                <tr
                  key={row.id}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                    display: 'flex', // 使用flex布局确保对齐
                  }}
                >
                  {row.getVisibleCells().map(cell => (
                    <td
                      key={cell.id}
                      style={{
                        width: `${cell.column.getSize()}px`,
                        minWidth: `${cell.column.getSize()}px`,
                        maxWidth: `${cell.column.getSize()}px`,
                        flex: 'none' // 防止flex自动调整宽度
                      }}
                    >
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ProductTable;
