import { Card, Button, Empty } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'

const DataAnalysis: React.FC = () => {
  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>数据分析</h1>

      <Card title="选择测试数据">
        <Empty description="请先在数据导入页面上传测试数据" />
      </Card>

      <Card title="分析配置" style={{ marginTop: 16 }}>
        <Empty description="选择测试数据后配置分析规则" />
      </Card>

      <Card title="分析结果" style={{ marginTop: 16 }}>
        <Empty description="执行分析后显示结果" />
        <Button type="primary" icon={<PlayCircleOutlined />} disabled>
          开始分析
        </Button>
      </Card>
    </div>
  )
}

export default DataAnalysis
