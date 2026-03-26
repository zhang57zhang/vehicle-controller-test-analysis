import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '../stores/project'
import { testDataApi, reportApi } from '../services/api'
import type { TestDataFile } from '../types'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { FileText, FileDown, RefreshCw, File } from 'lucide-react'

type ToastMessage = {
  type: 'success' | 'error'
  message: string
}

interface Report {
  id: string
  report_number: string
  report_type: string
  report_date: string
  version: string
  status: string
  created_at: string
}

const ReportGeneration: React.FC = () => {
  const navigate = useNavigate()
  const { currentProject } = useProjectStore()
  
  const [toasts, setToasts] = useState<ToastMessage[]>([])
  
  const showToast = (type: 'success' | 'error', message: string) => {
    const newToast: ToastMessage = { type, message }
    setToasts(prev => [...prev, newToast])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t !== newToast))
    }, 3000)
  }
  
  const [testDataList, setTestDataList] = useState<TestDataFile[]>([])
  const [loadingTestData, setLoadingTestData] = useState(false)
  
  const [selectedTestDataId, setSelectedTestDataId] = useState<string>('')
  const [reportType, setReportType] = useState<'standard' | 'traceability'>('standard')
  const [reportFormat, setReportFormat] = useState<'pdf' | 'word'>('pdf')
  
  const [author, setAuthor] = useState('')
  const [reviewer, setReviewer] = useState('')
  const [approver, setApprover] = useState('')
  
  const [reports, setReports] = useState<Report[]>([])
  const [loadingReports, setLoadingReports] = useState(false)
  
  const [generating, setGenerating] = useState(false)
  
  useEffect(() => {
    if (!currentProject) {
      showToast('error', '请先选择或创建一个项目')
      navigate('/projects')
      return
    }
    loadData()
  }, [currentProject])
  
  const loadData = async () => {
    if (!currentProject) return
    
    try {
      setLoadingTestData(true)
      setLoadingReports(true)
      
      const [testData, projectReports] = await Promise.all([
        testDataApi.getTestDataList(currentProject.id),
        reportApi.getReports(currentProject.id)
      ])
      
      setTestDataList(testData)
      setReports(projectReports)
    } catch (error) {
      showToast('error', '加载数据失败')
      console.error('加载数据失败:', error)
    } finally {
      setLoadingTestData(false)
      setLoadingReports(false)
    }
  }
  
  const handleGenerateReport = async () => {
    if (!selectedTestDataId) {
      showToast('error', '请选择测试数据')
      return
    }
    
    try {
      setGenerating(true)
      
      const result = await reportApi.generateReport(selectedTestDataId, {
        reportType,
        format: reportFormat,
        author: author || undefined,
        reviewer: reviewer || undefined,
        approver: approver || undefined
      })
      
      showToast('success', `报告生成成功: ${result.report_number}`)
      
      loadData()
    } catch (error) {
      showToast('error', '报告生成失败')
      console.error('报告生成失败:', error)
    } finally {
      setGenerating(false)
    }
  }
  
  const handleDownloadReport = async (reportId: string, format: 'pdf' | 'word') => {
    try {
      const blob = await reportApi.downloadReport(String(reportId), format)
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${reportId}.${format === 'pdf' ? 'pdf' : 'docx'}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      showToast('success', '报告下载成功')
    } catch (error) {
      showToast('error', '报告下载失败')
      console.error('报告下载失败:', error)
    }
  }
  
  if (!currentProject) {
    return null
  }
  
  return (
    <div className="space-y-6">
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
      
      <div>
        <h1 className="text-3xl font-bold">报告生成</h1>
        <p className="text-muted-foreground">
          当前项目：<span className="font-semibold text-primary">{currentProject.name}</span>
        </p>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>选择测试数据</CardTitle>
              <CardDescription>选择要生成报告的测试数据</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingTestData ? (
                <div className="text-muted-foreground">加载中...</div>
              ) : testDataList.length === 0 ? (
                <div className="text-muted-foreground">暂无测试数据，请先上传</div>
              ) : (
                <Select value={selectedTestDataId} onValueChange={setSelectedTestDataId}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择测试数据文件" />
                  </SelectTrigger>
                  <SelectContent>
                    {testDataList.map((data) => (
                      <SelectItem key={data.id} value={String(data.id)}>
                        {data.file_name} ({data.format.toUpperCase()}, {data.data_type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>报告类型</CardTitle>
              <CardDescription>选择报告类型和格式</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>报告类型</Label>
                <Select value={reportType} onValueChange={(v: 'standard' | 'traceability') => setReportType(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">标准报告（对外）</SelectItem>
                    <SelectItem value="traceability">溯源报告（内部审核）</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  {reportType === 'standard'
                    ? '用于正式交付、存档、对外发布，数据经过处理，只展示关键信息'
                    : '用于工程师深度审核、问题追溯，每个数据点都有原始出处'}
                </p>
              </div>
              
              <div className="space-y-2">
                <Label>输出格式</Label>
                <Select value={reportFormat} onValueChange={(v: 'pdf' | 'word') => setReportFormat(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pdf">PDF格式</SelectItem>
                    <SelectItem value="word">Word格式</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>报告信息</CardTitle>
              <CardDescription>填写报告编制信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="author">编制人</Label>
                <Input
                  id="author"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  placeholder="输入编制人姓名"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reviewer">审核人</Label>
                <Input
                  id="reviewer"
                  value={reviewer}
                  onChange={(e) => setReviewer(e.target.value)}
                  placeholder="输入审核人姓名"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="approver">批准人</Label>
                <Input
                  id="approver"
                  value={approver}
                  onChange={(e) => setApprover(e.target.value)}
                  placeholder="输入批准人姓名"
                />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>生成报告</CardTitle>
              <CardDescription>点击按钮生成报告</CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                onClick={handleGenerateReport} 
                disabled={generating || !selectedTestDataId}
                className="w-full"
              >
                {generating ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    生成{reportType === 'standard' ? '标准' : '溯源'}报告
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
        
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>已生成的报告</CardTitle>
              <CardDescription>{reports.length} 份报告</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingReports ? (
                <div className="text-muted-foreground py-8 text-center">加载中...</div>
              ) : reports.length === 0 ? (
                <div className="text-muted-foreground py-8 text-center">暂无报告</div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>报告编号</TableHead>
                        <TableHead>类型</TableHead>
                        <TableHead>日期</TableHead>
                        <TableHead>状态</TableHead>
                        <TableHead className="text-right">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {reports.map((report) => (
                        <TableRow key={report.id}>
                          <TableCell className="font-medium">{report.report_number}</TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                              report.report_type === 'standard' 
                                ? 'bg-blue-500/10 text-blue-500' 
                                : 'bg-purple-500/10 text-purple-500'
                            }`}>
                              {report.report_type === 'standard' ? '标准' : '溯源'}
                            </span>
                          </TableCell>
                          <TableCell>{report.report_date}</TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                              report.status === 'completed' 
                                ? 'bg-green-500/10 text-green-500' 
                                : 'bg-yellow-500/10 text-yellow-500'
                            }`}>
                              {report.status === 'completed' ? '已完成' : '草稿'}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDownloadReport(report.id, 'pdf')}
                              >
                                <FileDown className="mr-1 h-4 w-4" />
                                PDF
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDownloadReport(report.id, 'word')}
                              >
                                <File className="mr-1 h-4 w-4" />
                                Word
                              </Button>
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
      </div>
    </div>
  )
}

export default ReportGeneration
