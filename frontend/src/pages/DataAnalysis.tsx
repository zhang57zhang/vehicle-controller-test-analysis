import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { testDataApi, signalMappingApi, customSignalApi, analysisApi } from '../services/api'
import { useProjectStore } from '../stores/project'
import type { TestDataFile, SignalMapping, CustomSignal } from '../types'

// shadcn/ui components
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
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
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Plus, Play, Trash2, Edit } from 'lucide-react'

type ToastMessage = {
  type: 'success' | 'error'
  message: string
}

interface AnalysisConfig {
  test_data_id?: string
  sampling_rate?: number
  interpolation_method?: 'linear' | 'spline' | 'step'
}

interface AnalysisResult {
  id: string
  indicator_id: string
  indicator_name: string
  result_value: number | string
  result_status: 'pass' | 'warning' | 'fail'
  calculated_at: string
}

/**
 * 数据分析页面
 * 功能：信号映射配置、分析参数配置、执行分析、查看结果、自定义信号管理
 */
const DataAnalysis: React.FC = () => {
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

  // 测试数据列表
  const [testDataList, setTestDataList] = useState<TestDataFile[]>([])
  const [loadingTestData, setLoadingTestData] = useState(false)

  // 信号映射
  const [signalMappings, setSignalMappings] = useState<SignalMapping[]>([])
  const [loadingMappings, setLoadingMappings] = useState(false)

  // 自定义信号
  const [customSignals, setCustomSignals] = useState<CustomSignal[]>([])
  const [loadingCustomSignals, setLoadingCustomSignals] = useState(false)

  // 分析配置
  const [analysisConfig, setAnalysisConfig] = useState<AnalysisConfig>({
    sampling_rate: 100,
    interpolation_method: 'linear',
  })

  // 分析结果
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [hasAnalyzed, setHasAnalyzed] = useState(false)

  // 对话框状态
  const [signalMappingDialogOpen, setSignalMappingDialogOpen] = useState(false)
  const [editingSignalMapping, setEditingSignalMapping] = useState<SignalMapping | null>(null)
  const [signalMappingFormData, setSignalMappingFormData] = useState({
    signal_alias: '',
    dbc_signal: '',
    data_source_signal: '',
    from_unit: '',
    to_unit: '',
    formula: 'x',
    description: '',
  })

  const [customSignalDialogOpen, setCustomSignalDialogOpen] = useState(false)
  const [editingCustomSignal, setEditingCustomSignal] = useState<CustomSignal | null>(null)
  const [customSignalFormData, setCustomSignalFormData] = useState({
    signal_alias: '',
    calculation: '',
    input_signals: '',
    unit: '',
    description: '',
  })

  // 如果没有选择项目，跳转到项目页面
  useEffect(() => {
    if (!currentProject) {
      showToast('error', '请先选择或创建一个项目')
      navigate('/projects')
      return
    }
    loadData()
  }, [currentProject])

  // 加载数据
  const loadData = async () => {
    if (!currentProject) return

    try {
      setLoadingTestData(true)
      setLoadingMappings(true)
      setLoadingCustomSignals(true)

      const [testData, mappings, signals] = await Promise.all([
        testDataApi.getTestDataList(currentProject.id),
        signalMappingApi.getSignalMappings(currentProject.id),
        customSignalApi.getCustomSignals(currentProject.id),
      ])

      setTestDataList(testData)
      setSignalMappings(mappings)
      setCustomSignals(signals)
    } catch (error) {
      showToast('error', '加载数据失败')
      console.error('加载数据失败:', error)
    } finally {
      setLoadingTestData(false)
      setLoadingMappings(false)
      setLoadingCustomSignals(false)
    }
  }

  // 打开创建信号映射对话框
  const handleCreateSignalMapping = () => {
    setEditingSignalMapping(null)
    setSignalMappingFormData({
      signal_alias: '',
      dbc_signal: '',
      data_source_signal: '',
      from_unit: '',
      to_unit: '',
      formula: 'x',
      description: '',
    })
    setSignalMappingDialogOpen(true)
  }

  // 打开编辑信号映射对话框
  const handleEditSignalMapping = (mapping: SignalMapping) => {
    setEditingSignalMapping(mapping)
    setSignalMappingFormData({
      signal_alias: mapping.signal_alias,
      dbc_signal: mapping.dbc_signal || '',
      data_source_signal: mapping.data_source_signal || '',
      from_unit: mapping.unit_conversion?.from_unit || '',
      to_unit: mapping.unit_conversion?.to_unit || '',
      formula: mapping.unit_conversion?.formula || 'x',
      description: mapping.description || '',
    })
    setSignalMappingDialogOpen(true)
  }

  // 提交信号映射表单
  const handleSubmitSignalMapping = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!signalMappingFormData.signal_alias.trim()) {
      showToast('error', '请输入信号别名')
      return
    }

    try {
      const data = {
        signal_alias: signalMappingFormData.signal_alias,
        dbc_signal: signalMappingFormData.dbc_signal || undefined,
        data_source_signal: signalMappingFormData.data_source_signal || undefined,
        unit_conversion:
          signalMappingFormData.from_unit || signalMappingFormData.to_unit
            ? {
                from_unit: signalMappingFormData.from_unit,
                to_unit: signalMappingFormData.to_unit,
                formula: signalMappingFormData.formula,
              }
            : undefined,
        description: signalMappingFormData.description || undefined,
      }

      if (editingSignalMapping) {
        await signalMappingApi.updateSignalMapping(editingSignalMapping.id, data)
        showToast('success', '信号映射更新成功')
      } else {
        await signalMappingApi.createSignalMapping(currentProject!.id, data)
        showToast('success', '信号映射创建成功')
      }

      setSignalMappingDialogOpen(false)
      loadData()
    } catch (error) {
      showToast('error', editingSignalMapping ? '更新信号映射失败' : '创建信号映射失败')
      console.error('提交信号映射失败:', error)
    }
  }

  // 删除信号映射
  const handleDeleteSignalMapping = async (id: string) => {
    try {
      await signalMappingApi.deleteSignalMapping(id)
      showToast('success', '信号映射删除成功')
      loadData()
    } catch (error) {
      showToast('error', '删除信号映射失败')
      console.error('删除信号映射失败:', error)
    }
  }

  // 打开创建自定义信号对话框
  const handleCreateCustomSignal = () => {
    setEditingCustomSignal(null)
    setCustomSignalFormData({
      signal_alias: '',
      calculation: '',
      input_signals: '',
      unit: '',
      description: '',
    })
    setCustomSignalDialogOpen(true)
  }

  // 打开编辑自定义信号对话框
  const handleEditCustomSignal = (signal: CustomSignal) => {
    setEditingCustomSignal(signal)
    setCustomSignalFormData({
      signal_alias: signal.signal_alias,
      calculation: signal.calculation,
      input_signals: signal.input_signals.join(', '),
      unit: signal.unit,
      description: signal.description || '',
    })
    setCustomSignalDialogOpen(true)
  }

  // 提交自定义信号表单
  const handleSubmitCustomSignal = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!customSignalFormData.signal_alias.trim()) {
      showToast('error', '请输入信号别名')
      return
    }

    try {
      const data = {
        signal_alias: customSignalFormData.signal_alias,
        calculation: customSignalFormData.calculation,
        input_signals: customSignalFormData.input_signals
          .split(',')
          .map((s) => s.trim())
          .filter((s) => s),
        unit: customSignalFormData.unit,
        description: customSignalFormData.description || undefined,
      }

      if (editingCustomSignal) {
        await customSignalApi.updateCustomSignal(editingCustomSignal.id, data)
        showToast('success', '自定义信号更新成功')
      } else {
        await customSignalApi.createCustomSignal(currentProject!.id, data)
        showToast('success', '自定义信号创建成功')
      }

      setCustomSignalDialogOpen(false)
      loadData()
    } catch (error) {
      showToast('error', editingCustomSignal ? '更新自定义信号失败' : '创建自定义信号失败')
      console.error('提交自定义信号失败:', error)
    }
  }

  // 删除自定义信号
  const handleDeleteCustomSignal = async (id: string) => {
    try {
      await customSignalApi.deleteCustomSignal(id)
      showToast('success', '自定义信号删除成功')
      loadData()
    } catch (error) {
      showToast('error', '删除自定义信号失败')
      console.error('删除自定义信号失败:', error)
    }
  }

  // 执行分析
  const handleExecuteAnalysis = async () => {
    if (!analysisConfig.test_data_id) {
      showToast('error', '请选择测试数据')
      return
    }

    try {
      setAnalyzing(true)
      setAnalysisResults([])

      await analysisApi.executeAnalysis(analysisConfig.test_data_id, {
        timeSync: {
          target_sampling_rate: analysisConfig.sampling_rate,
          interpolation_method: analysisConfig.interpolation_method,
        },
      })

      const results = await analysisApi.getAnalysisResults(analysisConfig.test_data_id)

      setAnalysisResults(
        results.map((r: any) => ({
          ...r,
          indicator_name: r.indicator_id,
        }))
      )

      setHasAnalyzed(true)
      showToast('success', '分析完成')
    } catch (error) {
      showToast('error', '执行分析失败')
      console.error('执行分析失败:', error)
    } finally {
      setAnalyzing(false)
    }
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

      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold">数据分析</h1>
        <p className="text-muted-foreground">配置分析参数并执行数据分析</p>
      </div>

      <Tabs defaultValue="analysis" className="space-y-6">
        <TabsList>
          <TabsTrigger value="analysis">分析配置</TabsTrigger>
          <TabsTrigger value="signals">信号映射</TabsTrigger>
          <TabsTrigger value="custom">自定义信号</TabsTrigger>
        </TabsList>

        {/* 分析配置 */}
        <TabsContent value="analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>选择测试数据</CardTitle>
              <CardDescription>选择要分析的测试数据文件</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {loadingTestData ? (
                <div className="text-muted-foreground">加载中...</div>
              ) : testDataList.length === 0 ? (
                <div className="text-muted-foreground">
                  暂无测试数据，请先在数据导入页面上传
                </div>
              ) : (
                <Select
                  value={analysisConfig.test_data_id}
                  onValueChange={(value) =>
                    setAnalysisConfig({ ...analysisConfig, test_data_id: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择测试数据文件" />
                  </SelectTrigger>
                  <SelectContent>
                    {testDataList.map((data) => (
                      <SelectItem key={data.id} value={data.id}>
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
              <CardTitle>分析参数配置</CardTitle>
              <CardDescription>配置时间同步和采样参数</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="sampling_rate">采样率 (Hz)</Label>
                  <Input
                    id="sampling_rate"
                    type="number"
                    value={analysisConfig.sampling_rate}
                    onChange={(e) =>
                      setAnalysisConfig({
                        ...analysisConfig,
                        sampling_rate: parseInt(e.target.value) || 100,
                      })
                    }
                    min={1}
                    max={10000}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="interpolation_method">插值方法</Label>
                  <Select
                    value={analysisConfig.interpolation_method}
                    onValueChange={(value: 'linear' | 'spline' | 'step') =>
                      setAnalysisConfig({ ...analysisConfig, interpolation_method: value })
                    }
                  >
                    <SelectTrigger id="interpolation_method">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="linear">线性插值</SelectItem>
                      <SelectItem value="spline">样条插值</SelectItem>
                      <SelectItem value="step">阶梯插值</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button onClick={handleExecuteAnalysis} disabled={analyzing || !analysisConfig.test_data_id}>
                <Play className="mr-2 h-4 w-4" />
                {analyzing ? '分析中...' : '开始分析'}
              </Button>
            </CardContent>
          </Card>

          {/* 分析结果 */}
          {hasAnalyzed && (
            <Card>
              <CardHeader>
                <CardTitle>分析结果</CardTitle>
                <CardDescription>
                  {analysisResults.length} 个分析指标
                </CardDescription>
              </CardHeader>
              <CardContent>
                {analysisResults.length === 0 ? (
                  <div className="text-muted-foreground">暂无分析结果</div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>指标名称</TableHead>
                          <TableHead>结果值</TableHead>
                          <TableHead>状态</TableHead>
                          <TableHead>计算时间</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {analysisResults.map((result) => (
                          <TableRow key={result.id}>
                            <TableCell className="font-medium">{result.indicator_name}</TableCell>
                            <TableCell>{result.result_value}</TableCell>
                            <TableCell>
                              <span
                                className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                                  result.result_status === 'pass'
                                    ? 'bg-green-500/10 text-green-500'
                                    : result.result_status === 'warning'
                                    ? 'bg-yellow-500/10 text-yellow-500'
                                    : 'bg-red-500/10 text-red-500'
                                }`}
                              >
                                {result.result_status.toUpperCase()}
                              </span>
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {formatDate(result.calculated_at)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 信号映射 */}
        <TabsContent value="signals" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>信号映射配置</CardTitle>
                  <CardDescription>配置DBC信号与数据源信号的映射关系</CardDescription>
                </div>
                <Dialog open={signalMappingDialogOpen} onOpenChange={setSignalMappingDialogOpen}>
                  <DialogTrigger asChild>
                    <Button onClick={handleCreateSignalMapping}>
                      <Plus className="mr-2 h-4 w-4" />
                      添加映射
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>
                        {editingSignalMapping ? '编辑信号映射' : '添加信号映射'}
                      </DialogTitle>
                      <DialogDescription>
                        {editingSignalMapping ? '编辑信号映射配置' : '配置DBC信号与数据源信号的映射关系'}
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleSubmitSignalMapping}>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="signal_alias">信号别名 *</Label>
                          <Input
                            id="signal_alias"
                            value={signalMappingFormData.signal_alias}
                            onChange={(e) =>
                              setSignalMappingFormData({
                                ...signalMappingFormData,
                                signal_alias: e.target.value,
                              })
                            }
                            placeholder="例如：电池电压"
                            autoFocus
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="dbc_signal">DBC信号</Label>
                          <Input
                            id="dbc_signal"
                            value={signalMappingFormData.dbc_signal}
                            onChange={(e) =>
                              setSignalMappingFormData({
                                ...signalMappingFormData,
                                dbc_signal: e.target.value,
                              })
                            }
                            placeholder="例如：Battery_Voltage"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="data_source_signal">数据源信号</Label>
                          <Input
                            id="data_source_signal"
                            value={signalMappingFormData.data_source_signal}
                            onChange={(e) =>
                              setSignalMappingFormData({
                                ...signalMappingFormData,
                                data_source_signal: e.target.value,
                              })
                            }
                            placeholder="例如：V_BAT"
                          />
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label htmlFor="from_unit">原始单位</Label>
                            <Input
                              id="from_unit"
                              value={signalMappingFormData.from_unit}
                              onChange={(e) =>
                                setSignalMappingFormData({
                                  ...signalMappingFormData,
                                  from_unit: e.target.value,
                                })
                              }
                              placeholder="例如：V"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="to_unit">目标单位</Label>
                            <Input
                              id="to_unit"
                              value={signalMappingFormData.to_unit}
                              onChange={(e) =>
                                setSignalMappingFormData({
                                  ...signalMappingFormData,
                                  to_unit: e.target.value,
                                })
                              }
                              placeholder="例如：mV"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="formula">转换公式</Label>
                          <Input
                            id="formula"
                            value={signalMappingFormData.formula}
                            onChange={(e) =>
                              setSignalMappingFormData({
                                ...signalMappingFormData,
                                formula: e.target.value,
                              })
                            }
                            placeholder="例如：x*1000"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="description">描述</Label>
                          <Input
                            id="description"
                            value={signalMappingFormData.description}
                            onChange={(e) =>
                              setSignalMappingFormData({
                                ...signalMappingFormData,
                                description: e.target.value,
                              })
                            }
                            placeholder="可选"
                          />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setSignalMappingDialogOpen(false)}
                        >
                          取消
                        </Button>
                        <Button type="submit">{editingSignalMapping ? '保存' : '添加'}</Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {loadingMappings ? (
                <div className="text-muted-foreground">加载中...</div>
              ) : signalMappings.length === 0 ? (
                <div className="text-muted-foreground">暂无信号映射，点击"添加映射"创建</div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>信号别名</TableHead>
                        <TableHead>DBC信号</TableHead>
                        <TableHead>数据源信号</TableHead>
                        <TableHead>单位转换</TableHead>
                        <TableHead>描述</TableHead>
                        <TableHead className="text-right">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {signalMappings.map((mapping) => (
                        <TableRow key={mapping.id}>
                          <TableCell className="font-medium">{mapping.signal_alias}</TableCell>
                          <TableCell>{mapping.dbc_signal || '-'}</TableCell>
                          <TableCell>{mapping.data_source_signal || '-'}</TableCell>
                          <TableCell>
                            {mapping.unit_conversion
                              ? `${mapping.unit_conversion.from_unit} → ${mapping.unit_conversion.to_unit}`
                              : '-'}
                          </TableCell>
                          <TableCell className="max-w-[200px] truncate" title={mapping.description}>
                            {mapping.description || '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleEditSignalMapping(mapping)}
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
                                    <AlertDialogTitle>删除信号映射</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      确定要删除信号映射 "{mapping.signal_alias}" 吗？
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>取消</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() => handleDeleteSignalMapping(mapping.id)}
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
        </TabsContent>

        {/* 自定义信号 */}
        <TabsContent value="custom" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>自定义信号</CardTitle>
                  <CardDescription>创建基于计算的自定义信号</CardDescription>
                </div>
                <Dialog open={customSignalDialogOpen} onOpenChange={setCustomSignalDialogOpen}>
                  <DialogTrigger asChild>
                    <Button onClick={handleCreateCustomSignal}>
                      <Plus className="mr-2 h-4 w-4" />
                      添加信号
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>
                        {editingCustomSignal ? '编辑自定义信号' : '添加自定义信号'}
                      </DialogTitle>
                      <DialogDescription>
                        {editingCustomSignal ? '编辑自定义信号配置' : '创建基于计算的自定义信号'}
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleSubmitCustomSignal}>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="custom_signal_alias">信号别名 *</Label>
                          <Input
                            id="custom_signal_alias"
                            value={customSignalFormData.signal_alias}
                            onChange={(e) =>
                              setCustomSignalFormData({
                                ...customSignalFormData,
                                signal_alias: e.target.value,
                              })
                            }
                            placeholder="例如：电池功率"
                            autoFocus
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="calculation">计算公式 *</Label>
                          <Input
                            id="calculation"
                            value={customSignalFormData.calculation}
                            onChange={(e) =>
                              setCustomSignalFormData({
                                ...customSignalFormData,
                                calculation: e.target.value,
                              })
                            }
                            placeholder="例如：signal1 * signal2"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="input_signals">输入信号</Label>
                          <Input
                            id="input_signals"
                            value={customSignalFormData.input_signals}
                            onChange={(e) =>
                              setCustomSignalFormData({
                                ...customSignalFormData,
                                input_signals: e.target.value,
                              })
                            }
                            placeholder="例如：signal1, signal2 (用逗号分隔)"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="unit">单位</Label>
                          <Input
                            id="unit"
                            value={customSignalFormData.unit}
                            onChange={(e) =>
                              setCustomSignalFormData({
                                ...customSignalFormData,
                                unit: e.target.value,
                              })
                            }
                            placeholder="例如：W"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="custom_description">描述</Label>
                          <Input
                            id="custom_description"
                            value={customSignalFormData.description}
                            onChange={(e) =>
                              setCustomSignalFormData({
                                ...customSignalFormData,
                                description: e.target.value,
                              })
                            }
                            placeholder="可选"
                          />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setCustomSignalDialogOpen(false)}
                        >
                          取消
                        </Button>
                        <Button type="submit">{editingCustomSignal ? '保存' : '添加'}</Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {loadingCustomSignals ? (
                <div className="text-muted-foreground">加载中...</div>
              ) : customSignals.length === 0 ? (
                <div className="text-muted-foreground">暂无自定义信号，点击"添加信号"创建</div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>信号别名</TableHead>
                        <TableHead>计算公式</TableHead>
                        <TableHead>输入信号</TableHead>
                        <TableHead>单位</TableHead>
                        <TableHead>描述</TableHead>
                        <TableHead className="text-right">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {customSignals.map((signal) => (
                        <TableRow key={signal.id}>
                          <TableCell className="font-medium">{signal.signal_alias}</TableCell>
                          <TableCell className="font-mono text-sm">{signal.calculation}</TableCell>
                          <TableCell>{signal.input_signals.join(', ')}</TableCell>
                          <TableCell>{signal.unit}</TableCell>
                          <TableCell className="max-w-[200px] truncate" title={signal.description}>
                            {signal.description || '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleEditCustomSignal(signal)}
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
                                    <AlertDialogTitle>删除自定义信号</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      确定要删除自定义信号 "{signal.signal_alias}" 吗？
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>取消</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() => handleDeleteCustomSignal(signal.id)}
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
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default DataAnalysis
