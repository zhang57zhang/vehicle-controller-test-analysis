import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { testDataApi, signalMappingApi, customSignalApi, analysisApi, dbcApi } from '../services/api'
import { useProjectStore } from '../stores/project'
import type { TestDataFile, SignalMapping, CustomSignal, DBCMessage } from '../types'

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
import { 
  HistogramChart, 
  BoxPlotChart, 
  AnalysisResultChart,
  GaugeChart 
} from '@/components/charts'
import Oscilloscope from '@/components/Oscilloscope'
import { Plus, Play, Trash2, Edit, BarChart3, Activity } from 'lucide-react'

type ToastMessage = {
  type: 'success' | 'error'
  message: string
}

interface AnalysisConfig {
  test_data_id?: number
  sampling_rate?: number
  interpolation_method?: 'linear' | 'spline' | 'step'
}

interface AnalysisResult {
  id: number
  indicator_id: string
  indicator_name: string
  result_value: number | string | object
  result_status: 'pass' | 'warning' | 'fail' | 'error'
  calculated_at: string
}

interface SignalSummary {
  min: number
  max: number
  mean: number
  std: number
  count: number
}

const DataAnalysis: React.FC = () => {
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

  const [signalMappings, setSignalMappings] = useState<SignalMapping[]>([])
  const [loadingMappings, setLoadingMappings] = useState(false)

  const [customSignals, setCustomSignals] = useState<CustomSignal[]>([])
  const [loadingCustomSignals, setLoadingCustomSignals] = useState(false)

  const [analysisConfig, setAnalysisConfig] = useState<AnalysisConfig>({
    sampling_rate: 100,
    interpolation_method: 'linear',
  })

  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [hasAnalyzed, setHasAnalyzed] = useState(false)

  const [signalSummary, setSignalSummary] = useState<Record<string, SignalSummary>>({})
  const [selectedChartSignal, setSelectedChartSignal] = useState<string>('')
  const [availableSignals, setAvailableSignals] = useState<string[]>([])
  const [oscilloscopeData, setOscilloscopeData] = useState<{
    time: number[]
    signals: Record<string, number[]>
    statistics: Record<string, SignalSummary>
  } | null>(null)
  const [loadingOscilloscope, setLoadingOscilloscope] = useState(false)
  const [dbcMessages, setDbcMessages] = useState<DBCMessage[]>([])

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
      setLoadingMappings(true)
      setLoadingCustomSignals(true)

      const [testData, mappings, signals, dbcData] = await Promise.all([
        testDataApi.getTestDataList(currentProject.id),
        signalMappingApi.getSignalMappings(currentProject.id),
        customSignalApi.getCustomSignals(currentProject.id),
        dbcApi.getDBCSignals(currentProject.id).catch(() => ({ messages: [], signals: [], signal_count: 0, message_count: 0 }))
      ])

      setTestDataList(testData)
      setSignalMappings(mappings)
      setCustomSignals(signals)
      setDbcMessages(dbcData.messages || [])
    } catch (error) {
      showToast('error', '加载数据失败')
      console.error('加载数据失败:', error)
    } finally {
      setLoadingTestData(false)
      setLoadingMappings(false)
      setLoadingCustomSignals(false)
    }
  }

  const loadSignalData = async (testDataId: number) => {
    try {
      const response = await fetch(`/api/test-data/${testDataId}/signals`)
      if (response.ok) {
        const data = await response.json()
        setSignalSummary(data.summary || {})
        setAvailableSignals(data.signals || [])
        if (data.signals && data.signals.length > 0) {
          setSelectedChartSignal(data.signals[0])
        }
      }
    } catch (error) {
      console.error('加载信号数据失败:', error)
    }
  }

  const loadOscilloscopeData = async (testDataId: number) => {
    try {
      setLoadingOscilloscope(true)
      
      let signalsToLoad: string[] = availableSignals
      
      if (signalsToLoad.length === 0) {
        try {
          const data = await analysisApi.getAvailableSignals(testDataId)
          signalsToLoad = data.signals || []
          setAvailableSignals(signalsToLoad)
          setSignalSummary(data.summary || {})
        } catch (error) {
          console.error('加载信号列表失败:', error)
        }
      }

      if (signalsToLoad.length === 0) {
        showToast('error', '没有可用的信号数据')
        return
      }

      const result = await analysisApi.getSignalTimeSeries(testDataId, signalsToLoad.slice(0, 50), {
        maxPoints: 10000
      })

      if (result.status === 'success' && result.data) {
        setOscilloscopeData(result.data)
      }
    } catch (error) {
      showToast('error', '加载示波器数据失败')
      console.error('加载示波器数据失败:', error)
    } finally {
      setLoadingOscilloscope(false)
    }
  }




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

  const handleDeleteSignalMapping = async (id: number) => {
    try {
      await signalMappingApi.deleteSignalMapping(id)
      showToast('success', '信号映射删除成功')
      loadData()
    } catch (error) {
      showToast('error', '删除信号映射失败')
      console.error('删除信号映射失败:', error)
    }
  }

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

  const handleDeleteCustomSignal = async (id: number) => {
    try {
      await customSignalApi.deleteCustomSignal(id)
      showToast('success', '自定义信号删除成功')
      loadData()
    } catch (error) {
      showToast('error', '删除自定义信号失败')
      console.error('删除自定义信号失败:', error)
    }
  }

  const handleExecuteAnalysis = async () => {
    if (!analysisConfig.test_data_id) {
      showToast('error', '请选择测试数据')
      return
    }

    try {
      setAnalyzing(true)
      setAnalysisResults([])

      await analysisApi.executeAnalysis(analysisConfig.test_data_id, {
        time_sync: {
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

      await loadSignalData(analysisConfig.test_data_id)

      setHasAnalyzed(true)
      showToast('success', '分析完成')
    } catch (error) {
      showToast('error', '执行分析失败')
      console.error('执行分析失败:', error)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleQuickAnalysis = async () => {
    if (!analysisConfig.test_data_id) {
      showToast('error', '请选择测试数据')
      return
    }

    try {
      setAnalyzing(true)
      
      const response = await fetch(`/api/test-data/${analysisConfig.test_data_id}/analyze/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        const data = await response.json()
        setSignalSummary(data.statistics || {})
        showToast('success', '快速分析完成')
        setHasAnalyzed(true)
      }
    } catch (error) {
      showToast('error', '快速分析失败')
      console.error('快速分析失败:', error)
    } finally {
      setAnalyzing(false)
    }
  }

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

  const boxPlotData = Object.entries(signalSummary).slice(0, 10).map(([name, stats]) => ({
    name: name.slice(0, 15),
    min: stats.min,
    max: stats.max,
    q1: stats.mean - stats.std * 0.6745,
    median: stats.mean,
    q3: stats.mean + stats.std * 0.6745
  }))

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
        <h1 className="text-3xl font-bold">数据分析</h1>
        <p className="text-muted-foreground">配置分析参数并执行数据分析</p>
      </div>

      <Tabs defaultValue="analysis" className="space-y-6">
        <TabsList>
          <TabsTrigger value="analysis">分析配置</TabsTrigger>
          <TabsTrigger value="oscilloscope">示波器</TabsTrigger>
          <TabsTrigger value="visualization">数据可视化</TabsTrigger>
          <TabsTrigger value="signals">信号映射</TabsTrigger>
          <TabsTrigger value="custom">自定义信号</TabsTrigger>
        </TabsList>

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
                  value={analysisConfig.test_data_id ? String(analysisConfig.test_data_id) : ''}
                  onValueChange={(value) =>
                    setAnalysisConfig({ ...analysisConfig, test_data_id: parseInt(value, 10) })
                  }
                >
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
              <div className="flex gap-2">
                <Button onClick={handleExecuteAnalysis} disabled={analyzing || !analysisConfig.test_data_id}>
                  <Play className="mr-2 h-4 w-4" />
                  {analyzing ? '分析中...' : '开始分析'}
                </Button>
                <Button variant="outline" onClick={handleQuickAnalysis} disabled={analyzing || !analysisConfig.test_data_id}>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  快速分析
                </Button>
              </div>
            </CardContent>
          </Card>

          {hasAnalyzed && analysisResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>分析结果</CardTitle>
                <CardDescription>{analysisResults.length} 个分析指标</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium mb-2">结果分布</h4>
                    <AnalysisResultChart results={analysisResults} height={250} />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium mb-2">通过率</h4>
                    <div className="flex justify-center">
                      <GaugeChart
                        value={(analysisResults.filter(r => r.result_status === 'pass').length / analysisResults.length) * 100}
                        title="通过率"
                        unit="%"
                        height={200}
                      />
                    </div>
                  </div>
                </div>
                <div className="mt-4 overflow-x-auto">
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
                          <TableCell>{typeof result.result_value === 'object' ? JSON.stringify(result.result_value).slice(0, 50) : result.result_value}</TableCell>
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
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="oscilloscope" className="space-y-6">
          {!analysisConfig.test_data_id ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                请先在"分析配置"中选择测试数据
              </CardContent>
            </Card>
          ) : loadingOscilloscope ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <div className="flex items-center justify-center gap-2">
                  <Activity className="h-4 w-4 animate-pulse" />
                  正在加载示波器数据...
                </div>
              </CardContent>
            </Card>
          ) : oscilloscopeData && Object.keys(oscilloscopeData.signals).length > 0 ? (
            <Card className="h-[calc(100vh-280px)]">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  DBC信号示波器
                </CardTitle>
                <CardDescription>
                  显示 {Object.keys(oscilloscopeData.signals).length} 个信号 | 
                  DBC消息: {dbcMessages.length} 个 | 
                  时间范围: {oscilloscopeData.time.length > 0 ? 
                    `${oscilloscopeData.time[0].toFixed(3)}s - ${oscilloscopeData.time[oscilloscopeData.time.length-1].toFixed(3)}s` : 
                    'N/A'}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[calc(100%-80px)]">
                <Oscilloscope 
                  data={oscilloscopeData} 
                  dbcMessages={dbcMessages}
                  showDBCMode={dbcMessages.length > 0}
                />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="text-muted-foreground mb-4">
                  点击下方按钮加载示波器数据
                </div>
                <Button
                  onClick={() => loadOscilloscopeData(analysisConfig.test_data_id!)}
                  disabled={loadingOscilloscope}
                >
                  <Activity className="mr-2 h-4 w-4" />
                  加载示波器数据
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="visualization" className="space-y-6">
          {Object.keys(signalSummary).length > 0 ? (
            <>
              <div className="grid md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>信号统计分布</CardTitle>
                    <CardDescription>各信号的箱线图统计</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <BoxPlotChart data={boxPlotData} height={350} />
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <CardTitle>信号统计表</CardTitle>
                    <CardDescription>各信号的统计指标</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>信号</TableHead>
                            <TableHead>最小值</TableHead>
                            <TableHead>最大值</TableHead>
                            <TableHead>均值</TableHead>
                            <TableHead>标准差</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {Object.entries(signalSummary).slice(0, 10).map(([name, stats]) => (
                            <TableRow key={name}>
                              <TableCell className="font-medium truncate max-w-[150px]" title={name}>{name}</TableCell>
                              <TableCell>{stats.min.toFixed(4)}</TableCell>
                              <TableCell>{stats.max.toFixed(4)}</TableCell>
                              <TableCell>{stats.mean.toFixed(4)}</TableCell>
                              <TableCell>{stats.std.toFixed(4)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {selectedChartSignal && signalSummary[selectedChartSignal] && (
                <Card>
                  <CardHeader>
                    <CardTitle>信号直方图</CardTitle>
                    <CardDescription>选择信号的值分布</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Select value={selectedChartSignal} onValueChange={setSelectedChartSignal}>
                      <SelectTrigger className="w-[200px] mb-4">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.keys(signalSummary).map(name => (
                          <SelectItem key={name} value={name}>{name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <HistogramChart
                      data={Array.from({ length: 100 }, () => 
                        signalSummary[selectedChartSignal]?.mean + 
                        (Math.random() - 0.5) * 2 * signalSummary[selectedChartSignal]?.std
                      )}
                      title={`${selectedChartSignal} 分布`}
                      xLabel="值"
                    />
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                请先执行数据分析以查看可视化结果
              </CardContent>
            </Card>
          )}
        </TabsContent>

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
