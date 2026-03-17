import { Card, Button, Radio, Space, Empty } from 'antd'
import { FilePdfOutlined, FileWordOutlined } from '@ant-design/icons'
import { useState } from 'react'

const ReportGeneration: React.FC = () => {
  const [reportType, setReportType] = useState<'standard' | 'traceability'>('standard')

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>报告生成</h1>

      <Card title="报告类型">
        <Radio.Group value={reportType} onChange={(e) => setReportType(e.target.value)}>
          <Radio value="standard">标准报告（对外）</Radio>
          <Radio value="traceability">溯源报告（内部审核）</Radio>
        </Radio.Group>
        <p style={{ marginTop: 16, color: '#999' }}>
          {reportType === 'standard'
            ? '用于正式交付、存档、对外发布，数据经过处理，只展示关键信息'
            : '用于工程师深度审核、问题追溯，每个数据点都有原始出处'}
        </p>
      </Card>

      <Card title="报告模板" style={{ marginTop: 16 }}>
        <Empty description="选择测试数据后显示可用模板" />
      </Card>

      <Card title="生成选项" style={{ marginTop: 16 }}>
        <Empty description="配置报告生成选项" />
      </Card>

      <Card title="生成报告" style={{ marginTop: 16 }}>
        <Space>
          <Button type="primary" icon={<FilePdfOutlined />} disabled>
            生成PDF
          </Button>
          <Button icon={<FileWordOutlined />} disabled>
            生成Word
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default ReportGeneration
