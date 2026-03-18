import { Card, Descriptions, Tabs, Table, Button, Space, Tag, Empty, Spin, message, Popconfirm } from 'antd'
import { ArrowLeftOutlined, EditOutlined, DeleteOutlined, DownloadOutlined, PlusOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { projectApi, testDataApi, dbcApi, signalMappingApi } from '../services/api'
import { useProjectStore } from '../stores/project'
import type { Project, TestDataFile, DBCFile, SignalMapping } from '../types'
import dayjs from 'dayjs'

const { TabPane } = Tabs

/**
 * 项目详情页面
 * 功能：显示项目基本信息、DBC文件列表、测试数据文件列表、信号映射配置
 */
const ProjectDetail: React.FC = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const { setCurrentProject } = useProjectStore()

  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState<Project | null>(null)
  const [testDataList, setTestDataList] = useState<TestDataFile[]>([])
  const [dbcList, setDBCList] = useState<DBCFile[]>([])
  const [signalMappings, setSignalMappings] = useState<SignalMapping[]>([])
  const [activeTab, setActiveTab] = useState('info')

  useEffect(() => {
    if (id) {
      loadProjectDetail(id)
    }
  }, [id])

  // 加载项目详情
  const loadProjectDetail = async (projectId: string) => {
    try {
      setLoading(true)
      const [projectData, testData, dbc, mappings] = await Promise.all([
        projectApi.getProject(projectId),
        testDataApi.getTestDataList(projectId),
        dbcApi.getDBCList(projectId),
        signalMappingApi.getSignalMappings(projectId),
      ])

      setProject(projectData)
      setTestDataList(testData)
      setDBCList(dbc)
      setSignalMappings(mappings)
      setCurrentProject(projectData)
    } catch (error) {
      message.error('加载项目详情失败')
      console.error('加载项目详情失败:', error)
      navigate('/projects')
    } finally {
      setLoading(false)
    }
  }

  // 删除测试数据
  const handleDeleteTestData = async (testDataId: string) => {
    try {
      await testDataApi.deleteTestData(testDataId)
      message.success('删除成功')
      if (id) {
        loadProjectDetail(id)
      }
    } catch (error) {
      message.error('删除失败')
      console.error('删除测试数据失败:', error)
    }
  }

  // 删除DBC文件
  const handleDeleteDBC = async (dbcId: string) => {
    try {
      await dbcApi.deleteDBC?.(dbcId)
      message.success('删除成功')
      if (id) {
        loadProjectDetail(id)
      }
    } catch (error) {
      message.error('删除失败')
      console.error('删除DBC文件失败:', error)
    }
  }

  // 导入信号映射
  const handleImportSignalMappings = async () => {
    message.info('导入信号映射功能开发中')
  }

  // 导出信号映射
  const handleExportSignalMappings = async () => {
    if (!project) return

    try {
      const blob = await signalMappingApi.exportSignalMappings(project.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${project.name}_信号映射.xlsx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch (error) {
      message.error('导出失败')
      console.error('导出信号映射失败:', error)
    }
  }

  // 测试数据表格列
  const testDataColumns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      width: 100,
      render: (format: string) => <Tag color="blue">{format.toUpperCase()}</Tag>,
    },
    {
      title: '数据类型',
      dataIndex: 'data_type',
      key: 'data_type',
      width: 120,
      render: (type: string) => <Tag color="green">{type}</Tag>,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 120,
      render: (size: number) => `${(size / 1024 / 1024).toFixed(2)} MB`,
    },
    {
      title: '上传时间',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: TestDataFile) => (
        <Popconfirm
          title="确认删除"
          description="确定要删除这个测试数据文件吗？"
          onConfirm={() => handleDeleteTestData(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ]

  // DBC文件表格列
  const dbcColumns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 100,
      render: (version: string) => version || '-',
    },
    {
      title: '上传时间',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: DBCFile) => (
        <Popconfirm
          title="确认删除"
          description="确定要删除这个DBC文件吗？"
          onConfirm={() => handleDeleteDBC(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ]

  // 信号映射表格列
  const signalMappingColumns = [
    {
      title: '信号别名',
      dataIndex: 'signal_alias',
      key: 'signal_alias',
    },
    {
      title: 'DBC信号',
      dataIndex: 'dbc_signal',
      key: 'dbc_signal',
      render: (text: string) => text || '-',
    },
    {
      title: '数据源信号',
      dataIndex: 'data_source_signal',
      key: 'data_source_signal',
      render: (text: string) => text || '-',
    },
    {
      title: '单位转换',
      dataIndex: 'unit_conversion',
      key: 'unit_conversion',
      width: 200,
      render: (conversion: any) => {
        if (!conversion) return '-'
        return `${conversion.from_unit} → ${conversion.to_unit}`
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
  ]

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  if (!project) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Empty description="项目不存在" />
        <Button type="primary" icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')}>
          返回项目列表
        </Button>
      </div>
    )
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')}>
          返回
        </Button>
        <Button icon={<EditOutlined />} onClick={() => navigate(`/projects/${project.id}/edit`)}>
          编辑项目
        </Button>
      </Space>

      <Card>
        <Tabs activeKey={activeTab} onChange={(key) => setActiveTab(key)}>
          <TabPane tab="基本信息" key="info">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="项目ID" span={2}>{project.id}</Descriptions.Item>
              <Descriptions.Item label="项目名称" span={2}>
                <span style={{ fontSize: 18, fontWeight: 500 }}>{project.name}</span>
              </Descriptions.Item>
              <Descriptions.Item label="项目描述" span={2}>
                {project.description || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="DBC文件" span={2}>
                {project.dbc_file ? <Tag color="blue">已配置</Tag> : <Tag>未配置</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">{dayjs(project.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{dayjs(project.updated_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
            </Descriptions>
          </TabPane>

          <TabPane tab={`测试数据 (${testDataList.length})`} key="testdata">
            {testDataList.length > 0 ? (
              <Table
                columns={testDataColumns}
                dataSource={testDataList}
                rowKey="id"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total) => `共 ${total} 个文件`,
                }}
                scroll={{ x: 800 }}
              />
            ) : (
              <Empty description="暂无测试数据" />
            )}
          </TabPane>

          <TabPane tab={`DBC文件 (${dbcList.length})`} key="dbc">
            {dbcList.length > 0 ? (
              <Table
                columns={dbcColumns}
                dataSource={dbcList}
                rowKey="id"
                pagination={false}
                scroll={{ x: 600 }}
              />
            ) : (
              <Empty description="暂无DBC文件" />
            )}
          </TabPane>

          <TabPane
            tab={
              <span>
                信号映射 ({signalMappings.length})
                {signalMappings.length > 0 && (
                  <Button
                    type="link"
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleExportSignalMappings()
                    }}
                  >
                    导出
                  </Button>
                )}
              </span>
            }
            key="mappings"
          >
            <Space style={{ marginBottom: 16 }}>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleImportSignalMappings}>
                导入信号映射
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleExportSignalMappings}>
                导出信号映射
              </Button>
            </Space>

            {signalMappings.length > 0 ? (
              <Table
                columns={signalMappingColumns}
                dataSource={signalMappings}
                rowKey="id"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total) => `共 ${total} 个映射`,
                }}
                scroll={{ x: 1000 }}
              />
            ) : (
              <Empty description="暂无信号映射配置" />
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default ProjectDetail
