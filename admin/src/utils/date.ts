/**
 * 格式化日期字符串为本地时间格式
 * @param dateString ISO格式的日期字符串
 * @returns 格式化后的日期字符串
 */
export function formatDate(dateString: string): string {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
} 