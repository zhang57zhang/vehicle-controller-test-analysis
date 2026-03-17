import { Card, Table, Button, Space, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useState } from 'react'

const ProjectManager: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([])

  const columns = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button type="link" icon={<EditOutlined />}>编辑</Button>
          <Popconfirm title="确定要删除这个项目吗？">
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card title="项目管理" extra={<Button type="primary" icon={<PlusOutlined />}>新建项目</Button>}>
        <Table columns={columns} dataSource={projects} rowKey="id" />
      </Card>
    </div>
  )
}

export default ProjectManager
