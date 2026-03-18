import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { projectApi } from '../services/api'
import { useProjectStore } from '../stores/project'
import type { Project } from '../types'

// shadcn/ui components
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog'
import { Plus, Edit, Eye, Trash2, FileText } from 'lucide-react'

type ToastMessage = {
  type: 'success' | 'error'
  message: string
}

/**
 * 项目管理页面
 * 功能：项目列表展示、创建、编辑、删除项目
 */
const ProjectManager: React.FC = () => {
  const navigate = useNavigate()
  const { projects, setProjects, addProject, updateProject: updateStoreProject, removeProject } = useProjectStore()

  const [loading, setLoading] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [formData, setFormData] = useState({ name: '', description: '' })

  // Toast状态
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const showToast = (type: 'success' | 'error', message: string) => {
    const newToast: ToastMessage = { type, message }
    setToasts(prev => [...prev, newToast])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t !== newToast))
    }, 3000)
  }

  // 加载项目列表
  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      setLoading(true)
      const data = await projectApi.getProjects()
      setProjects(data)
    } catch (error) {
      showToast('error', '加载项目列表失败')
      console.error('加载项目失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 打开创建项目对话框
  const handleCreate = () => {
    setEditingProject(null)
    setFormData({ name: '', description: '' })
    setDialogOpen(true)
  }

  // 打开编辑项目对话框
  const handleEdit = (project: Project) => {
    setEditingProject(project)
    setFormData({ name: project.name, description: project.description || '' })
    setDialogOpen(true)
  }

  // 提交表单（创建或编辑）
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name.trim()) {
      showToast('error', '请输入项目名称')
      return
    }

    try {
      if (editingProject) {
        // 编辑项目
        const updatedProject = await projectApi.updateProject(editingProject.id, {
          name: formData.name,
          description: formData.description,
        })
        updateStoreProject(updatedProject)
        showToast('success', '项目更新成功')
      } else {
        // 创建项目
        const newProject = await projectApi.createProject({
          name: formData.name,
          description: formData.description,
        })
        addProject(newProject)
        showToast('success', '项目创建成功')
      }

      setDialogOpen(false)
      setFormData({ name: '', description: '' })
      setEditingProject(null)
    } catch (error) {
      showToast('error', editingProject ? '更新项目失败' : '创建项目失败')
      console.error('提交项目失败:', error)
    }
  }

  // 删除项目
  const handleDelete = async (id: string, name: string) => {
    try {
      await projectApi.deleteProject(id)
      removeProject(id)
      showToast('success', `项目 "${name}" 删除成功`)
    } catch (error) {
      showToast('error', '删除项目失败')
      console.error('删除项目失败:', error)
    }
  }

  // 查看项目详情
  const handleView = (project: Project) => {
    navigate(`/projects/${project.id}`)
  }

  // 格式化时间
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  return (
    <div className="space-y-6">
      {/* Toast notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toast, index) => (
          <div
            key={index}
            className={`flex items-center gap-2 rounded-lg p-4 shadow-lg ${
              toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
            }`}
          >
            {toast.type === 'success' ? (
              <div className="h-5 w-5 rounded-full bg-white/20 flex items-center justify-center">
                <span className="text-sm font-bold">✓</span>
              </div>
            ) : (
              <div className="h-5 w-5 rounded-full bg-white/20 flex items-center justify-center">
                <span className="text-sm font-bold">✕</span>
              </div>
            )}
            <span>{toast.message}</span>
          </div>
        ))}
      </div>

      {/* 页面标题和操作栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">项目管理</h1>
          <p className="text-muted-foreground">管理和配置您的测试项目</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleCreate}>
              <Plus className="mr-2 h-4 w-4" />
              新建项目
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingProject ? '编辑项目' : '新建项目'}</DialogTitle>
              <DialogDescription>
                {editingProject ? '编辑项目信息' : '创建一个新的测试项目'}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">项目名称 *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="请输入项目名称"
                    maxLength={100}
                    autoFocus
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">项目描述</Label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="请输入项目描述（可选）"
                    maxLength={500}
                    className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setDialogOpen(false)
                    setFormData({ name: '', description: '' })
                    setEditingProject(null)
                  }}
                >
                  取消
                </Button>
                <Button type="submit">{editingProject ? '保存' : '创建'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* 项目列表 */}
      <Card>
        <CardHeader>
          <CardTitle>项目列表</CardTitle>
          <CardDescription>共 {projects.length} 个项目</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">加载中...</div>
            </div>
          ) : projects.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <FileText className="h-16 w-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">暂无项目</p>
              <p className="text-sm mt-1">点击"新建项目"创建您的第一个项目</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[200px]">项目名称</TableHead>
                    <TableHead>描述</TableHead>
                    <TableHead className="w-[150px]">DBC文件</TableHead>
                    <TableHead className="w-[180px]">创建时间</TableHead>
                    <TableHead className="w-[180px]">更新时间</TableHead>
                    <TableHead className="w-[200px] text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {projects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell className="font-medium">{project.name}</TableCell>
                      <TableCell className="max-w-[300px] truncate" title={project.description}>
                        {project.description || '-'}
                      </TableCell>
                      <TableCell>
                        {project.dbc_file ? (
                          <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-1 text-xs font-medium text-blue-500">
                            已配置
                          </span>
                        ) : (
                          <span className="inline-flex items-center rounded-full bg-gray-500/10 px-2 py-1 text-xs font-medium text-gray-500">
                            未配置
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(project.created_at)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(project.updated_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleView(project)}
                            title="查看"
                            className="h-8 w-8"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(project)}
                            title="编辑"
                            className="h-8 w-8"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                title="删除"
                                className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>删除项目</AlertDialogTitle>
                                <AlertDialogDescription>
                                  确定要删除项目 "{project.name}" 吗？删除后将无法恢复！
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>取消</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDelete(project.id, project.name)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  删除
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default ProjectManager
