import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { testDataApi, dbcApi, testCaseApi } from '../services/api'
import { useProjectStore } from '../stores/project'
import type { TestDataFile, DBCFile, TestDataType } from '../types'

// shadcn/ui components
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Dropzone } from '@/components/ui/dropzone'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { UploadCloud, Trash2, CheckCircle2, XCircle } from 'lucide-react'

// 类型用于显示Toast消息
type ToastMessage = {
  type: 'success' | 'error'
  message: string
}

/**
 * 数据导入页面
 * 功能：上传测试数据文件、DBC文件、导入测试用例Excel
 */
const DataImport: React.FC = () => {
  const navigate = useNavigate()
  const { currentProject } = useProjectStore()

  // Toast状态
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const showToast = (type: 'success' | 'error', message: string) => {
    const newToast: ToastMessage = { type, message }
    setToasts(prev => [...prev, newToast])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t !== newToast))
    }, 3000)
  }

  // 测试数据上传状态
  const [testDataUploading, setTestDataUploading] = useState(false)
  const [testDataProgress, setTestDataProgress] = useState(0)
  const [testDataType, setTestDataType] = useState<TestDataType['type']>('MANUAL')

  // DBC文件上传状态
  const [dbcUploading, setDBCUploading] = useState(false)
  const [dbcProgress, setDBCProgress] = useState(0)

  // 测试用例上传状态
  const [testCaseUploading, setTestCaseUploading] = useState(false)
  const [testCaseProgress, setTestCaseProgress] = useState(0)

  // 已上传的文件列表
  const [uploadedTestDataList, setUploadedTestDataList] = useState<TestDataFile[]>([])
  const [uploadedDBCList, setUploadedDBCList] = useState<DBCFile[]>([])
  const [loading, setLoading] = useState(false)

  // 如果没有选择项目，跳转到项目页面
  useEffect(() => {
    if (!currentProject) {
      showToast('error', '请先选择或创建一个项目')
      navigate('/projects')
      return
    }
    loadUploadedFiles()
  }, [currentProject])

  // 加载已上传的文件列表
  const loadUploadedFiles = async () => {
    if (!currentProject) return

    try {
      setLoading(true)
      const [testData, dbc] = await Promise.all([
        testDataApi.getTestDataList(currentProject.id),
        dbcApi.getDBCList(currentProject.id),
      ])
      setUploadedTestDataList(testData)
      setUploadedDBCList(dbc)
    } catch (error) {
      showToast('error', '加载文件列表失败')
      console.error('加载文件列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 测试数据文件上传处理
  const handleTestDataFilesSelected = async (files: FileList) => {
    if (!currentProject || files.length === 0) return

    try {
      setTestDataUploading(true)
      setTestDataProgress(0)

      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)
        formData.append('data_type', testDataType)

        // 模拟进度
        const progressInterval = setInterval(() => {
          setTestDataProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval)
              return 90
            }
            return prev + 10
          })
        }, 200)

        await testDataApi.uploadTestData(currentProject.id, formData)

        clearInterval(progressInterval)
        const finalProgress = Math.round(((i + 1) / files.length) * 100)
        setTestDataProgress(finalProgress)

        showToast('success', `${file.name} 上传成功`)
      }

      setTestDataProgress(100)
      loadUploadedFiles()
    } catch (error) {
      showToast('error', '文件上传失败')
      console.error('文件上传失败:', error)
    } finally {
      setTestDataUploading(false)
      setTimeout(() => setTestDataProgress(0), 2000)
    }
  }

  // DBC文件上传处理
  const handleDBCFilesSelected = async (files: FileList) => {
    if (!currentProject || files.length === 0) return

    try {
      setDBCUploading(true)
      setDBCProgress(0)

      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)

        // 模拟进度
        const progressInterval = setInterval(() => {
          setDBCProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval)
              return 90
            }
            return prev + 10
          })
        }, 200)

        await dbcApi.uploadDBC(currentProject.id, formData)

        clearInterval(progressInterval)
        const finalProgress = Math.round(((i + 1) / files.length) * 100)
        setDBCProgress(finalProgress)

        showToast('success', `${file.name} 上传成功`)
      }

      setDBCProgress(100)
      loadUploadedFiles()
    } catch (error) {
      showToast('error', 'DBC文件上传失败')
      console.error('DBC文件上传失败:', error)
    } finally {
      setDBCUploading(false)
      setTimeout(() => setDBCProgress(0), 2000)
    }
  }

  // 测试用例上传处理
  const handleTestCaseFileSelected = async (files: FileList) => {
    if (!currentProject || files.length === 0) return

    try {
      setTestCaseUploading(true)
      setTestCaseProgress(0)

      const file = files[0]

      // 模拟进度
      const progressInterval = setInterval(() => {
        setTestCaseProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      await testCaseApi.importTestCases(currentProject.id, file)

      clearInterval(progressInterval)
      setTestCaseProgress(100)

      showToast('success', '测试用例导入成功')
    } catch (error) {
      showToast('error', '测试用例导入失败')
      console.error('测试用例导入失败:', error)
    } finally {
      setTestCaseUploading(false)
      setTimeout(() => setTestCaseProgress(0), 2000)
    }
  }

  // 删除测试数据文件
  const handleDeleteTestData = async (id: string, fileName: string) => {
    try {
      await testDataApi.deleteTestData(id)
      showToast('success', `${fileName} 删除成功`)
      loadUploadedFiles()
    } catch (error) {
      showToast('error', '删除失败')
      console.error('删除测试数据失败:', error)
    }
  }

  // 删除DBC文件
  const handleDeleteDBC = async (id: string, fileName: string) => {
    try {
      await dbcApi.deleteDBC(id)
      showToast('success', `${fileName} 删除成功`)
      loadUploadedFiles()
    } catch (error) {
      showToast('error', '删除失败')
      console.error('删除DBC文件失败:', error)
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  if (!currentProject) {
    return null
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
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <XCircle className="h-5 w-5" />
            )}
            <span>{toast.message}</span>
          </div>
        ))}
      </div>

      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold">数据导入</h1>
        <p className="text-muted-foreground">
          当前项目：<span className="font-semibold text-primary">{currentProject.name}</span>
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 左侧：测试数据上传 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>上传测试数据</CardTitle>
              {testDataUploading && (
                <CardContent className="pt-2">
                  <Progress value={testDataProgress} />
                  <p className="mt-2 text-sm text-muted-foreground">
                    {testDataProgress}%
                  </p>
                </CardContent>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="dataType">数据类型</Label>
                <Select value={testDataType} onValueChange={(value: TestDataType['type']) => setTestDataType(value)}>
                  <SelectTrigger id="dataType">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MIL">MIL测试</SelectItem>
                    <SelectItem value="HIL">HIL测试</SelectItem>
                    <SelectItem value="DVP">DVP验证</SelectItem>
                    <SelectItem value="VEHICLE">整车测试</SelectItem>
                    <SelectItem value="MANUAL">手动测试</SelectItem>
                    <SelectItem value="AUTO">自动测试</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Dropzone
                onFilesSelected={handleTestDataFilesSelected}
                accept=".mat,.csv,.xlsx,.log,.blf,.asc,.xml,.json"
                disabled={testDataUploading}
              >
                <UploadCloud className="h-12 w-12 text-muted-foreground" />
                <div className="text-sm">
                  <p className="font-medium">点击或拖拽文件到此区域上传</p>
                  <p className="text-muted-foreground">
                    支持格式：.mat, .csv, .xlsx, .log, .blf, .asc, .xml, .json
                  </p>
                </div>
              </Dropzone>
            </CardContent>
          </Card>

          {/* 已上传的测试数据列表 */}
          <Card>
            <CardHeader>
              <CardTitle>已上传的测试数据</CardTitle>
              <CardDescription>{uploadedTestDataList.length} 个文件</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-muted-foreground">加载中...</div>
                </div>
              ) : uploadedTestDataList.length === 0 ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  暂无数据
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>文件名</TableHead>
                        <TableHead className="w-[100px]">格式</TableHead>
                        <TableHead className="w-[120px]">类型</TableHead>
                        <TableHead className="w-[120px]">大小</TableHead>
                        <TableHead className="w-[100px]">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {uploadedTestDataList.map((file) => (
                        <TableRow key={file.id}>
                          <TableCell className="font-medium max-w-[200px] truncate" title={file.file_name}>
                            {file.file_name}
                          </TableCell>
                          <TableCell>
                            <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-1 text-xs font-medium text-blue-500">
                              {file.format.toUpperCase()}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className="inline-flex items-center rounded-full bg-green-500/10 px-2 py-1 text-xs font-medium text-green-500">
                              {file.data_type}
                            </span>
                          </TableCell>
                          <TableCell>{formatFileSize(file.file_size)}</TableCell>
                          <TableCell>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>确认删除</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    确定要删除 {file.file_name} 吗？此操作无法撤销。
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>取消</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDeleteTestData(file.id, file.file_name)}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                  >
                                    删除
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
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

        {/* 右侧：DBC文件上传和测试用例导入 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>上传DBC文件</CardTitle>
              {dbcUploading && (
                <CardContent className="pt-2">
                  <Progress value={dbcProgress} />
                  <p className="mt-2 text-sm text-muted-foreground">
                    {dbcProgress}%
                  </p>
                </CardContent>
              )}
            </CardHeader>
            <CardContent>
              <Dropzone
                onFilesSelected={handleDBCFilesSelected}
                accept=".dbc,.arxml,.xml"
                disabled={dbcUploading}
              >
                <UploadCloud className="h-12 w-12 text-muted-foreground" />
                <div className="text-sm">
                  <p className="font-medium">点击或拖拽DBC文件到此区域上传</p>
                  <p className="text-muted-foreground">
                    支持格式：.dbc, .arxml, .xml
                  </p>
                </div>
              </Dropzone>
            </CardContent>
          </Card>

          {/* 已上传的DBC文件列表 */}
          <Card>
            <CardHeader>
              <CardTitle>已上传的DBC文件</CardTitle>
              <CardDescription>{uploadedDBCList.length} 个文件</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-muted-foreground">加载中...</div>
                </div>
              ) : uploadedDBCList.length === 0 ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  暂无数据
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>文件名</TableHead>
                        <TableHead className="w-[100px]">版本</TableHead>
                        <TableHead className="w-[100px]">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {uploadedDBCList.map((file) => (
                        <TableRow key={file.id}>
                          <TableCell className="font-medium max-w-[200px] truncate" title={file.file_name}>
                            {file.file_name}
                          </TableCell>
                          <TableCell>{file.version || '-'}</TableCell>
                          <TableCell>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>确认删除</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    确定要删除 {file.file_name} 吗？此操作无法撤销。
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>取消</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDeleteDBC(file.id, file.file_name)}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                  >
                                    删除
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 测试用例导入 */}
          <Card>
            <CardHeader>
              <CardTitle>导入测试用例</CardTitle>
              {testCaseUploading && (
                <CardContent className="pt-2">
                  <Progress value={testCaseProgress} />
                  <p className="mt-2 text-sm text-muted-foreground">
                    {testCaseProgress}%
                  </p>
                </CardContent>
              )}
            </CardHeader>
            <CardContent>
              <Dropzone
                onFilesSelected={handleTestCaseFileSelected}
                accept=".xlsx,.xls"
                disabled={testCaseUploading}
              >
                <UploadCloud className="h-12 w-12 text-muted-foreground" />
                <div className="text-sm">
                  <p className="font-medium">点击或拖拽Excel文件到此区域</p>
                  <p className="text-muted-foreground">
                    支持格式：.xlsx, .xls
                  </p>
                </div>
              </Dropzone>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default DataImport
