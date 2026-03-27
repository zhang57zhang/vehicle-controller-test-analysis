import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Move,
  Crosshair,
  Gauge,
  Maximize2,
  AlignJustify,
  Columns,
  Square,
  Ruler,
  Activity,
  Eye,
  EyeOff,
  Search,
  ChevronDown,
  ChevronRight
} from 'lucide-react'

interface SignalData {
  time: number[]
  signals: Record<string, number[]>
  statistics: Record<string, SignalStatistics>
}

interface SignalStatistics {
  min: number
  max: number
  mean: number
  std: number
  count: number
}

interface Cursor {
  id: string
  time: number
  color: string
  label: string
}

interface CursorMeasurement {
  cursor1: Cursor | null
  cursor2: Cursor | null
  delta: {
    time: number
    signals: Record<string, { value1: number; value2: number; delta: number }>
  } | null
}

interface SignalConfig {
  name: string
  color: string
  visible: boolean
  yMin: number
  yMax: number
  yOffset: number
  yScale: number
  separateYAxis: boolean
}

const DEFAULT_COLORS = [
  '#1890ff', '#52c41a', '#faad14', '#eb2f96', '#722ed1',
  '#13c2c2', '#fa8c16', '#a0d911', '#2f54eb', '#f5222d'
]

interface OscilloscopeProps {
  data: SignalData
  signalColors?: Record<string, string>
  onZoomChange?: (zoomState: { xMin: number; xMax: number }) => void
}

const Oscilloscope: React.FC<OscilloscopeProps> = ({
  data,
  signalColors = {},
  onZoomChange
}) => {
  const chartRef = useRef<ReactECharts>(null)
  const [signalConfigs, setSignalConfigs] = useState<SignalConfig[]>([])
  const [selectedSignals, setSelectedSignals] = useState<string[]>([])
  const [xRange, setXRange] = useState<[number, number]>([0, 0])
  const [originalXRange, setOriginalXRange] = useState<[number, number]>([0, 0])
  const [isPanning, setIsPanning] = useState(false)
  const [showCursor, setShowCursor] = useState(false)
  const [cursorMode, setCursorMode] = useState<'single' | 'differential'>('single')
  const [cursors, setCursors] = useState<Cursor[]>([])
  const [cursorMeasurement, setCursorMeasurement] = useState<CursorMeasurement>({
    cursor1: null,
    cursor2: null,
    delta: null
  })
  const [currentTimeValue, setCurrentTimeValue] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})
  const [separateYAxisMode, setSeparateYAxisMode] = useState(true)
  const [showStatistics, setShowStatistics] = useState(true)

  const signalNames = useMemo(() => Object.keys(data.signals), [data.signals])

  useEffect(() => {
    if (data.time && data.time.length > 0) {
      const minTime = Math.min(...data.time)
      const maxTime = Math.max(...data.time)
      setXRange([minTime, maxTime])
      setOriginalXRange([minTime, maxTime])
    }
  }, [data.time])

  useEffect(() => {
    const configs: SignalConfig[] = signalNames.map((name, index) => ({
      name,
      color: signalColors[name] || DEFAULT_COLORS[index % DEFAULT_COLORS.length],
      visible: false,
      yMin: data.statistics[name]?.min || 0,
      yMax: data.statistics[name]?.max || 1,
      yOffset: 0,
      yScale: 1,
      separateYAxis: separateYAxisMode
    }))
    setSignalConfigs(configs)
  }, [signalNames, data.statistics, signalColors, separateYAxisMode])

  const handleSignalToggle = (signalName: string) => {
    setSignalConfigs(prev => {
      const newConfigs = prev.map(c => 
        c.name === signalName ? { ...c, visible: !c.visible } : c
      )
      const visibleSignals = newConfigs.filter(c => c.visible).map(c => c.name)
      setSelectedSignals(visibleSignals)
      return newConfigs
    })
  }

  const handleSelectAll = () => {
    setSignalConfigs(prev => prev.map(c => ({ ...c, visible: true })))
    setSelectedSignals(signalNames)
  }

  const handleDeselectAll = () => {
    setSignalConfigs(prev => prev.map(c => ({ ...c, visible: false })))
    setSelectedSignals([])
  }

  const handleAutoFitX = useCallback(() => {
    setXRange(originalXRange)
    const chart = chartRef.current?.getEchartsInstance()
    if (chart) {
      chart.dispatchAction({
        type: 'dataZoom',
        start: 0,
        end: 100
      })
    }
    onZoomChange?.({ xMin: originalXRange[0], xMax: originalXRange[1] })
  }, [originalXRange, onZoomChange])

  const handleAutoFitY = useCallback(() => {
    const chart = chartRef.current?.getEchartsInstance()
    if (!chart) return
    
    const visibleSignals = signalConfigs.filter(c => c.visible)
    if (visibleSignals.length === 0) return

    let globalMin = Infinity
    let globalMax = -Infinity

    visibleSignals.forEach(config => {
      const stats = data.statistics[config.name]
      if (stats) {
        globalMin = Math.min(globalMin, stats.min)
        globalMax = Math.max(globalMax, stats.max)
      }
    })

    if (globalMin !== Infinity && globalMax !== -Infinity) {
      const padding = (globalMax - globalMin) * 0.1
      chart.setOption({
        yAxis: {
          min: globalMin - padding,
          max: globalMax + padding
        }
      })
    }
  }, [signalConfigs, data.statistics])

  const handleAutoFitXY = useCallback(() => {
    handleAutoFitX()
    handleAutoFitY()
  }, [handleAutoFitX, handleAutoFitY])

  const handleZoomIn = useCallback(() => {
    const chart = chartRef.current?.getEchartsInstance()
    if (!chart) return
    
    const option = chart.getOption() as any
    const currentStart = option.dataZoom?.[0]?.start || 0
    const currentEnd = option.dataZoom?.[0]?.end || 100
    const center = (currentStart + currentEnd) / 2
    const newRange = (currentEnd - currentStart) / 2
    const newStart = Math.max(0, center - newRange / 2)
    const newEnd = Math.min(100, center + newRange / 2)
    
    chart.dispatchAction({
      type: 'dataZoom',
      start: newStart,
      end: newEnd
    })
  }, [])

  const handleZoomOut = useCallback(() => {
    const chart = chartRef.current?.getEchartsInstance()
    if (!chart) return
    
    const option = chart.getOption() as any
    const currentStart = option.dataZoom?.[0]?.start || 0
    const currentEnd = option.dataZoom?.[0]?.end || 100
    const center = (currentStart + currentEnd) / 2
    const newRange = (currentEnd - currentStart) * 2
    const newStart = Math.max(0, center - newRange / 2)
    const newEnd = Math.min(100, center + newRange / 2)
    
    chart.dispatchAction({
      type: 'dataZoom',
      start: newStart,
      end: newEnd
    })
  }, [])

  const handleResetZoom = useCallback(() => {
    handleAutoFitXY()
    setCursors([])
    setCursorMeasurement({ cursor1: null, cursor2: null, delta: null })
    setShowCursor(false)
  }, [handleAutoFitXY])

  const togglePanMode = () => {
    setIsPanning(!isPanning)
  }

  const handleAddCursor = useCallback((time?: number) => {
    const cursorTime = time ?? (xRange[0] + xRange[1]) / 2
    const newCursor: Cursor = {
      id: `cursor_${Date.now()}`,
      time: cursorTime,
      color: cursors.length === 0 ? '#ff4d4f' : '#1890ff',
      label: cursors.length === 0 ? 'X1' : 'X2'
    }
    
    setCursors(prev => {
      const newCursors = [...prev, newCursor]
      if (newCursors.length === 1) {
        setCursorMeasurement({
          cursor1: newCursor,
          cursor2: null,
          delta: null
        })
      } else if (newCursors.length === 2) {
        const c1 = newCursors[0]
        const c2 = newCursors[1]
        const deltaTime = Math.abs(c2.time - c1.time)
        
        const signalDeltas: Record<string, { value1: number; value2: number; delta: number }> = {}
        selectedSignals.forEach(signalName => {
          const signalData = data.signals[signalName]
          const timeData = data.time
          
          const idx1 = findClosestIndex(timeData, c1.time)
          const idx2 = findClosestIndex(timeData, c2.time)
          
          if (idx1 !== -1 && idx2 !== -1) {
            const v1 = signalData[idx1]
            const v2 = signalData[idx2]
            signalDeltas[signalName] = {
              value1: v1,
              value2: v2,
              delta: Math.abs(v2 - v1)
            }
          }
        })
        
        setCursorMeasurement({
          cursor1: c1,
          cursor2: c2,
          delta: {
            time: deltaTime,
            signals: signalDeltas
          }
        })
      }
      return newCursors
    })
  }, [xRange, cursors, selectedSignals, data])

  const handleRemoveCursor = (cursorId: string) => {
    setCursors(prev => {
      const newCursors = prev.filter(c => c.id !== cursorId)
      if (newCursors.length === 0) {
        setCursorMeasurement({ cursor1: null, cursor2: null, delta: null })
      } else if (newCursors.length === 1) {
        setCursorMeasurement({
          cursor1: newCursors[0],
          cursor2: null,
          delta: null
        })
      }
      return newCursors
    })
  }

  const findClosestIndex = (arr: number[], target: number): number => {
    let closestIdx = 0
    let minDiff = Math.abs(arr[0] - target)
    for (let i = 1; i < arr.length; i++) {
      const diff = Math.abs(arr[i] - target)
      if (diff < minDiff) {
        minDiff = diff
        closestIdx = i
      }
    }
    return closestIdx
  }

  const handleChartClick = useCallback((params: any) => {
    if (showCursor && params.data) {
      const clickedTime = params.data[0]
      if (cursors.length < 2) {
        handleAddCursor(clickedTime)
      } else {
        setCursors([])
        setCursorMeasurement({ cursor1: null, cursor2: null, delta: null })
        handleAddCursor(clickedTime)
      }
    }
  }, [showCursor, cursors, handleAddCursor])

  const handleDataZoom = useCallback((params: any) => {
    if (params.batch) {
      const zoom = params.batch[0]
      const timeRange = originalXRange[1] - originalXRange[0]
      const newXMin = originalXRange[0] + timeRange * (zoom.start / 100)
      const newXMax = originalXRange[0] + timeRange * (zoom.end / 100)
      setXRange([newXMin, newXMax])
      onZoomChange?.({ xMin: newXMin, xMax: newXMax })
    }
  }, [originalXRange, onZoomChange])

  const handleMouseMove = useCallback((params: any) => {
    if (params.data) {
      setCurrentTimeValue(params.data[0])
    }
  }, [])

  const filteredSignalConfigs = useMemo(() => {
    if (!searchTerm) return signalConfigs
    return signalConfigs.filter(c => 
      c.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [signalConfigs, searchTerm])

  const groupedSignals = useMemo(() => {
    const groups: Record<string, SignalConfig[]> = {}
    filteredSignalConfigs.forEach(config => {
      const prefix = config.name.split('_')[0] || 'Other'
      if (!groups[prefix]) {
        groups[prefix] = []
      }
      groups[prefix].push(config)
    })
    return groups
  }, [filteredSignalConfigs])

  const chartOption = useMemo(() => {
    const visibleConfigs = signalConfigs.filter(c => c.visible && selectedSignals.includes(c.name))
    
    const series: any[] = visibleConfigs.map((config, index) => {
      const signalData = data.signals[config.name] || []
      const timeData = data.time || []
      
      const chartData = timeData.map((t, i) => [t, signalData[i]])
      
      const seriesConfig: any = {
        name: config.name,
        type: 'line',
        data: chartData,
        showSymbol: false,
        lineStyle: {
          width: 1.5,
          color: config.color
        },
        itemStyle: {
          color: config.color
        },
        emphasis: {
          focus: 'series'
        }
      }
      
      if (separateYAxisMode && index > 0) {
        seriesConfig.yAxisIndex = index
      }
      
      return seriesConfig
    })

    const yAxisConfigs = separateYAxisMode 
      ? visibleConfigs.map((config, index) => {
          const stats = data.statistics[config.name]
          const padding = stats ? (stats.max - stats.min) * 0.1 : 1
          return {
            type: 'value' as const,
            name: config.name,
            position: index === 0 ? 'left' as const : 'right' as const,
            offset: index > 0 ? (index - 1) * 60 : 0,
            axisLine: {
              show: true,
              lineStyle: { color: config.color }
            },
            axisLabel: {
              color: config.color,
              fontSize: 10
            },
            splitLine: {
              show: index === 0,
              lineStyle: { type: 'dashed' as any, opacity: 0.3 }
            },
            min: stats ? stats.min - padding : undefined,
            max: stats ? stats.max + padding : undefined
          }
        })
      : [{
          type: 'value' as const,
          name: 'Value',
          position: 'left' as const,
          splitLine: {
            show: true,
            lineStyle: { type: 'dashed' as any, opacity: 0.3 }
          }
        }]

    const cursorMarkLines = cursors.map(cursor => ({
      name: cursor.label,
      xAxis: cursor.time,
      lineStyle: {
        color: cursor.color,
        type: 'dashed' as const,
        width: 2
      },
      label: {
        show: true,
        formatter: `${cursor.label}: ${cursor.time.toFixed(3)}s`,
        position: 'start' as const
      }
    }))

    if (cursorMarkLines.length > 0 && series.length > 0) {
      series[0].markLine = {
        silent: false,
        symbol: 'none',
        data: cursorMarkLines
      }
    }

    return {
      animation: false,
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          snap: true,
          lineStyle: {
            color: '#7591a6',
            width: 1,
            type: 'dashed'
          }
        },
        formatter: (params: any[]) => {
          if (!params || params.length === 0) return ''
          const time = params[0].data[0]
          let html = `<div style="font-weight:bold;margin-bottom:4px">时间: ${time.toFixed(4)}s</div>`
          params.forEach((item: any) => {
            html += `<div style="display:flex;align-items:center;gap:4px">
              <span style="color:${item.color}">━━</span>
              <span>${item.seriesName}: ${item.data[1]?.toFixed(4) ?? 'N/A'}</span>
            </div>`
          })
          return html
        }
      },
      legend: {
        show: true,
        type: 'scroll',
        top: 5,
        left: 'center',
        itemWidth: 20,
        itemHeight: 10,
        textStyle: { fontSize: 11 }
      },
      grid: {
        left: separateYAxisMode ? '10%' : '5%',
        right: separateYAxisMode ? `${5 + (visibleConfigs.length - 1) * 5}%` : '5%',
        top: 50,
        bottom: 80,
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: '时间',
        nameLocation: 'middle',
        nameGap: 30,
        min: xRange[0],
        max: xRange[1],
        splitLine: {
          show: true,
          lineStyle: { type: 'dashed', opacity: 0.3 }
        }
      },
      yAxis: yAxisConfigs,
      dataZoom: [
        {
          type: 'inside',
          start: ((xRange[0] - originalXRange[0]) / (originalXRange[1] - originalXRange[0])) * 100,
          end: ((xRange[1] - originalXRange[0]) / (originalXRange[1] - originalXRange[0])) * 100,
          zoomOnMouseWheel: true,
          moveOnMouseMove: isPanning
        },
        {
          type: 'slider',
          show: true,
          start: ((xRange[0] - originalXRange[0]) / (originalXRange[1] - originalXRange[0])) * 100,
          end: ((xRange[1] - originalXRange[0]) / (originalXRange[1] - originalXRange[0])) * 100,
          height: 30,
          bottom: 10
        }
      ],
      toolbox: {
        show: true,
        right: 20,
        top: 5,
        feature: {
          dataZoom: {
            yAxisIndex: 'none',
            title: { zoom: '框选缩放', back: '还原' }
          },
          restore: { title: '还原' },
          saveAsImage: { title: '保存图片' }
        }
      },
      series
    }
  }, [signalConfigs, selectedSignals, data, separateYAxisMode, xRange, originalXRange, cursors, isPanning])

  const onChartEvents = useMemo(() => ({
    click: handleChartClick,
    datazoom: handleDataZoom,
    mousemove: handleMouseMove
  }), [handleChartClick, handleDataZoom, handleMouseMove])

  const visibleStats = useMemo(() => {
    return selectedSignals.map(name => ({
      name,
      stats: data.statistics[name],
      color: signalConfigs.find(c => c.name === name)?.color || DEFAULT_COLORS[0]
    })).filter(s => s.stats)
  }, [selectedSignals, data.statistics, signalConfigs])

  return (
    <div className="flex h-full w-full gap-4">
      <div className="w-72 flex-shrink-0 border rounded-lg overflow-hidden flex flex-col">
        <div className="p-3 border-b bg-muted/30">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-sm">信号列表</h3>
            <div className="flex gap-1">
              <Button size="sm" variant="ghost" onClick={handleSelectAll} title="全选">
                <Eye className="h-3 w-3" />
              </Button>
              <Button size="sm" variant="ghost" onClick={handleDeselectAll} title="全不选">
                <EyeOff className="h-3 w-3" />
              </Button>
            </div>
          </div>
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
            <Input
              placeholder="搜索信号..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-7 h-7 text-sm"
            />
          </div>
        </div>
        
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {Object.entries(groupedSignals).map(([group, configs]) => (
              <div key={group} className="mb-1">
                <div
                  className="flex items-center gap-1 px-2 py-1 cursor-pointer hover:bg-muted/50 rounded text-xs font-medium text-muted-foreground"
                  onClick={() => setExpandedGroups(prev => ({ ...prev, [group]: !prev[group] }))}
                >
                  {expandedGroups[group] ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                  <span>{group}</span>
                  <span className="ml-auto text-[10px]">({configs.length})</span>
                </div>
                {(expandedGroups[group] !== false) && configs.map(config => (
                  <div
                    key={config.name}
                    className="flex items-center gap-2 px-2 py-1.5 hover:bg-muted/50 rounded cursor-pointer"
                    onClick={() => handleSignalToggle(config.name)}
                  >
                    <Checkbox
                      checked={config.visible}
                      onCheckedChange={() => handleSignalToggle(config.name)}
                      className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                      style={{ accentColor: config.color }}
                    />
                    <div
                      className="w-3 h-3 rounded-sm"
                      style={{ backgroundColor: config.color }}
                    />
                    <span className="text-xs truncate flex-1" title={config.name}>
                      {config.name}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <div className="flex-1 flex flex-col gap-3">
        <div className="flex items-center gap-2 p-2 border rounded-lg bg-muted/20">
          <div className="flex items-center gap-1 border-r pr-2">
            <Button size="sm" variant="ghost" onClick={handleZoomIn} title="放大">
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={handleZoomOut} title="缩小">
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={handleResetZoom} title="重置">
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex items-center gap-1 border-r pr-2">
            <Button
              size="sm"
              variant={isPanning ? 'default' : 'ghost'}
              onClick={togglePanMode}
              title="平移模式"
            >
              <Move className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex items-center gap-1 border-r pr-2">
            <Button size="sm" variant="ghost" onClick={handleAutoFitX} title="X轴自适应">
              <AlignJustify className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={handleAutoFitY} title="Y轴自适应">
              <Columns className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={handleAutoFitXY} title="XY轴自适应">
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex items-center gap-1 border-r pr-2">
            <Button
              size="sm"
              variant={showCursor ? 'default' : 'ghost'}
              onClick={() => {
                setShowCursor(!showCursor)
                if (showCursor) {
                  setCursors([])
                  setCursorMeasurement({ cursor1: null, cursor2: null, delta: null })
                }
              }}
              title="光标测量"
            >
              <Crosshair className="h-4 w-4" />
            </Button>
            {showCursor && (
              <>
                <Button
                  size="sm"
                  variant={cursorMode === 'single' ? 'default' : 'ghost'}
                  onClick={() => setCursorMode('single')}
                  title="单光标"
                >
                  <Ruler className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant={cursorMode === 'differential' ? 'default' : 'ghost'}
                  onClick={() => setCursorMode('differential')}
                  title="差分光标"
                >
                  <Gauge className="h-4 w-4" />
                </Button>
                {cursors.length < 2 && (
                  <Button size="sm" variant="ghost" onClick={() => handleAddCursor()} title="添加光标">
                    添加
                  </Button>
                )}
              </>
            )}
          </div>

          <div className="flex items-center gap-1 border-r pr-2">
            <Button
              size="sm"
              variant={separateYAxisMode ? 'default' : 'ghost'}
              onClick={() => setSeparateYAxisMode(!separateYAxisMode)}
              title="分离Y轴"
            >
              <Square className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant={showStatistics ? 'default' : 'ghost'}
              onClick={() => setShowStatistics(!showStatistics)}
              title="显示统计"
            >
              <Activity className="h-4 w-4" />
            </Button>
          </div>

          {currentTimeValue !== null && (
            <div className="ml-auto text-xs text-muted-foreground">
              当前时间: {currentTimeValue.toFixed(4)}s
            </div>
          )}
        </div>

        <div className="flex-1 border rounded-lg overflow-hidden">
          <ReactECharts
            ref={chartRef}
            option={chartOption}
            style={{ height: '100%', width: '100%' }}
            opts={{ renderer: 'canvas' }}
            onEvents={onChartEvents}
            notMerge={true}
          />
        </div>

        {showStatistics && visibleStats.length > 0 && (
          <div className="border rounded-lg p-2 bg-muted/20">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {visibleStats.map(({ name, stats, color }) => (
                <div key={name} className="border rounded p-2 bg-background text-xs">
                  <div className="font-medium truncate mb-1" style={{ color }} title={name}>
                    {name}
                  </div>
                  <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground">
                    <span>最小:</span>
                    <span className="font-mono">{stats.min.toFixed(4)}</span>
                    <span>最大:</span>
                    <span className="font-mono">{stats.max.toFixed(4)}</span>
                    <span>均值:</span>
                    <span className="font-mono">{stats.mean.toFixed(4)}</span>
                    <span>标准差:</span>
                    <span className="font-mono">{stats.std.toFixed(4)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {showCursor && cursorMeasurement.cursor1 && (
          <div className="border rounded-lg p-2 bg-muted/20">
            <div className="text-xs font-medium mb-1">光标测量</div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              <div className="border rounded p-2 bg-background text-xs">
                <div className="font-medium" style={{ color: cursorMeasurement.cursor1.color }}>
                  {cursorMeasurement.cursor1.label}
                </div>
                <div className="text-muted-foreground">
                  时间: {cursorMeasurement.cursor1.time.toFixed(4)}s
                </div>
              </div>
              {cursorMeasurement.cursor2 && (
                <div className="border rounded p-2 bg-background text-xs">
                  <div className="font-medium" style={{ color: cursorMeasurement.cursor2.color }}>
                    {cursorMeasurement.cursor2.label}
                  </div>
                  <div className="text-muted-foreground">
                    时间: {cursorMeasurement.cursor2.time.toFixed(4)}s
                  </div>
                </div>
              )}
              {cursorMeasurement.delta && (
                <>
                  <div className="border rounded p-2 bg-background text-xs">
                    <div className="font-medium">ΔT</div>
                    <div className="text-muted-foreground font-mono">
                      {cursorMeasurement.delta.time.toFixed(4)}s
                    </div>
                  </div>
                  {cursorMeasurement.delta.signals && Object.entries(cursorMeasurement.delta.signals).slice(0, 3).map(([signal, data]) => (
                    <div key={signal} className="border rounded p-2 bg-background text-xs">
                      <div className="font-medium truncate">{signal}</div>
                      <div className="text-muted-foreground">
                        <div>V1: {data.value1.toFixed(4)}</div>
                        <div>V2: {data.value2.toFixed(4)}</div>
                        <div className="font-mono">Δ: {data.delta.toFixed(4)}</div>
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
            {cursors.length > 0 && (
              <div className="flex gap-1 mt-2">
                {cursors.map(cursor => (
                  <Button
                    key={cursor.id}
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRemoveCursor(cursor.id)}
                    className="text-xs"
                    style={{ color: cursor.color }}
                  >
                    删除 {cursor.label}
                  </Button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Oscilloscope
