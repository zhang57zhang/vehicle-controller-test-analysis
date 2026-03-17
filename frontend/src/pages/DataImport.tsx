import { Card, Upload, Button, message, Progress, Row, Col } from 'antd'
import { InboxOutlined, UploadOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'

const { Dragger } = Upload

const DataImport: React.FC = () => {
  const props: UploadProps = {
    name: 'file',
    multiple: true,
    action: '/api/upload', // 临时占位，后续连接后端API
    onChange(info) {
      const { status } = info.file
      if (status === 'done') {
        message.success(`${info.file.name} 上传成功`)
      } else if (status === 'error') {
        message.error(`${info.file.name} 上传失败`)
      }
    },
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>数据导入</h1>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="上传测试数据">
            <Dragger {...props}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持格式：.mat, .csv, .xlsx, .log, .blf, .asc, .xml, .json
              </p>
            </Dragger>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="上传DBC文件">
            <Dragger {...props}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽DBC文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持格式：.dbc, .arxml, .xml
              </p>
            </Dragger>
          </Card>

          <Card title="导入测试用例" style={{ marginTop: 16 }}>
            <Upload {...props}>
              <Button icon={<UploadOutlined />}>选择Excel文件</Button>
            </Upload>
          </Card>
        </Col>
      </Row>

      <Card title="上传进度" style={{ marginTop: 16 }}>
        <p style={{ color: '#999' }}>暂无上传任务</p>
      </Card>
    </div>
  )
}

export default DataImport
