// 应用初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('词根聚类需求挖掘系统 v2.0.0 已加载');

    // 检查系统状态
    checkSystemStatus();

    // 每30秒检查一次状态
    setInterval(checkSystemStatus, 30000);
});

// 检查系统状态
async function checkSystemStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();

        const statusEl = document.getElementById('status');
        if (statusEl) {
            if (data.status === 'ok') {
                statusEl.innerHTML = '● 运行中';
                statusEl.className = 'text-green-600';
            } else {
                statusEl.innerHTML = '● 异常';
                statusEl.className = 'text-red-600';
            }
        }
    } catch (error) {
        console.error('状态检查失败:', error);
        const statusEl = document.getElementById('status');
        if (statusEl) {
            statusEl.innerHTML = '● 离线';
            statusEl.className = 'text-gray-400';
        }
    }
}

// HTMX 事件监听
document.body.addEventListener('htmx:beforeRequest', function(event) {
    console.log('HTMX 请求开始:', event.detail.path);
});

document.body.addEventListener('htmx:afterRequest', function(event) {
    console.log('HTMX 请求完成:', event.detail.path);
});

document.body.addEventListener('htmx:responseError', function(event) {
    console.error('HTMX 请求错误:', event.detail);
    alert('请求失败，请稍后重试');
});

// 工具函数：显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    } text-white z-50`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 工具函数：格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 工具函数：格式化数字
function formatNumber(num) {
    return num.toLocaleString('zh-CN');
}
