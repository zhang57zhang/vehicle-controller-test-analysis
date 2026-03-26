import ReactECharts from 'echarts-for-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useState } from 'react'

interface TimeSeriesChartProps {
  data: {
    time: number[]
    [key: string]: number[]
  }
  title?: string
  height?: number
  selectedSignals?: string[]
  onSignalSelect?: (signals: string[]) => void
}

export function TimeSeriesChart({
  data,
  title = '时间序列图',
  height = 400,
  selectedSignals,
  onSignalSelect
}: TimeSeriesChartProps) {
  const signals = Object.keys(data).filter(key => key !== 'time')
  const [currentSignals, setCurrentSignals] = useState<string[]>(
    selectedSignals || signals.slice(0, 3)
  )

  const handleSignalChange = (value: string) => {
    const newSignals = currentSignals.includes(value)
      ? currentSignals.filter(s => s !== value)
      : [...currentSignals, value]
    
    setCurrentSignals(newSignals.slice(0, 5))
    onSignalSelect?.(newSignals.slice(0, 5))
  }

  const colors = ['#1890ff', '#52c41a', '#faad14', '#eb2f96', '#722ed1']

  const series = currentSignals.map((signal, index) => ({
    name: signal,
    type: 'line' as const,
    data: data.time.map((t, i) => [t, data[signal]?.[i]]),
    showSymbol: false,
    lineStyle: {
      width: 1.5
    },
    itemStyle: {
      color: colors[index % colors.length]
    }
  }))

  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        const time = params[0].data[0]
        let html = `<div style="font-weight:bold">时间: ${time.toFixed(3)}s</div>`
        params.forEach((item: any) => {
          html += `<div><span style="color:${item.color}">●</span> ${item.seriesName}: ${item.data[1]?.toFixed(4) || 'N/A'}</div>`
        })
        return html
      }
    },
    legend: {
      data: currentSignals,
      top: 30,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 80,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '时间',
      nameLocation: 'middle',
      nameGap: 30,
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    yAxis: {
      type: 'value',
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 20,
        bottom: 10
      }
    ],
    series
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            <CardDescription>显示 {currentSignals.length} 个信号</CardDescription>
          </div>
          <Select value={currentSignals[0] || ''} onValueChange={handleSignalChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="选择信号" />
            </SelectTrigger>
            <SelectContent>
              {signals.map(signal => (
                <SelectItem key={signal} value={signal}>
                  {signal}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <ReactECharts
          option={option}
          style={{ height: `${height}px` }}
          opts={{ renderer: 'canvas' }}
        />
      </CardContent>
    </Card>
  )
}

interface HistogramChartProps {
  data: number[]
  title?: string
  xLabel?: string
  bins?: number
  height?: number
}

export function HistogramChart({
  data,
  title = '直方图',
  xLabel = '值',
  bins = 20,
  height = 300
}: HistogramChartProps) {
  const validData = data.filter(v => !isNaN(v) && isFinite(v))
  
  const min = Math.min(...validData)
  const max = Math.max(...validData)
  const binWidth = (max - min) / bins
  
  const histogram: number[] = new Array(bins).fill(0)
  validData.forEach(v => {
    const binIndex = Math.min(Math.floor((v - min) / binWidth), bins - 1)
    histogram[binIndex]++
  })

  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 50,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      name: xLabel,
      nameLocation: 'middle',
      nameGap: 30,
      data: Array.from({ length: bins }, (_, i) => (min + i * binWidth).toFixed(2)),
      axisLabel: {
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      name: '频次'
    },
    series: [{
      type: 'bar',
      data: histogram,
      itemStyle: {
        color: '#1890ff'
      }
    }]
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px` }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

interface BoxPlotChartProps {
  data: {
    name: string
    min: number
    q1: number
    median: number
    q3: number
    max: number
  }[]
  title?: string
  height?: number
}

export function BoxPlotChart({
  data,
  title = '箱线图',
  height = 400
}: BoxPlotChartProps) {
  const boxData = data.map(d => [d.min, d.q1, d.median, d.q3, d.max])

  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const d = data[params.dataIndex]
        return `
          <div style="font-weight:bold">${d.name}</div>
          <div>最大值: ${d.max.toFixed(4)}</div>
          <div>上四分位: ${d.q3.toFixed(4)}</div>
          <div>中位数: ${d.median.toFixed(4)}</div>
          <div>下四分位: ${d.q1.toFixed(4)}</div>
          <div>最小值: ${d.min.toFixed(4)}</div>
        `
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: 50
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: {
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      name: '值'
    },
    series: [{
      name: 'boxplot',
      type: 'boxplot',
      data: boxData,
      itemStyle: {
        color: '#1890ff',
        borderColor: '#096dd9'
      }
    }]
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px` }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

interface ScatterChartProps {
  data: { x: number; y: number }[]
  title?: string
  xLabel?: string
  yLabel?: string
  height?: number
}

export function ScatterChart({
  data,
  title = '散点图',
  xLabel = 'X',
  yLabel = 'Y',
  height = 400
}: ScatterChartProps) {
  const chartData = data
    .filter(d => !isNaN(d.x) && !isNaN(d.y))
    .map(d => [d.x, d.y])

  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${xLabel}: ${params.data[0].toFixed(4)}<br/>${yLabel}: ${params.data[1].toFixed(4)}`
      }
    },
    grid: {
      left: '3%',
      right: '7%',
      bottom: '3%',
      top: 50,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: xLabel,
      nameLocation: 'middle',
      nameGap: 30,
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: yLabel,
      nameLocation: 'middle',
      nameGap: 40,
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    dataZoom: [
      {
        type: 'inside'
      }
    ],
    series: [{
      type: 'scatter',
      data: chartData,
      symbolSize: 5,
      itemStyle: {
        color: '#1890ff',
        opacity: 0.6
      }
    }]
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px` }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

interface CorrelationHeatmapProps {
  data: {
    signals: string[]
    matrix: number[][]
  }
  title?: string
  height?: number
}

export function CorrelationHeatmap({
  data,
  title = '相关性热力图',
  height = 500
}: CorrelationHeatmapProps) {
  const { signals, matrix } = data
  
  const heatmapData: [number, number, number][] = []
  matrix.forEach((row, i) => {
    row.forEach((value, j) => {
      heatmapData.push([i, j, value])
    })
  })

  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const [i, j, value] = params.data
        return `${signals[i]} vs ${signals[j]}<br/>相关系数: ${value.toFixed(4)}`
      }
    },
    grid: {
      left: '15%',
      right: '10%',
      bottom: '15%',
      top: 50
    },
    xAxis: {
      type: 'category',
      data: signals,
      splitArea: {
        show: true
      },
      axisLabel: {
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'category',
      data: signals,
      splitArea: {
        show: true
      },
      axisLabel: {
        fontSize: 10
      }
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8',
                '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
      }
    },
    series: [{
      name: '相关性',
      type: 'heatmap',
      data: heatmapData,
      label: {
        show: signals.length <= 10,
        fontSize: 8,
        formatter: (params: any) => params.data[2].toFixed(2)
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px` }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

interface GaugeChartProps {
  value: number
  min?: number
  max?: number
  title?: string
  unit?: string
  thresholds?: { value: number; color: string }[]
  height?: number
}

export function GaugeChart({
  value,
  min = 0,
  max = 100,
  title = '',
  unit = '%',
  thresholds = [
    { value: 60, color: '#52c41a' },
    { value: 80, color: '#faad14' },
    { value: 100, color: '#ff4d4f' }
  ],
  height = 200
}: GaugeChartProps) {
  const option = {
    series: [{
      type: 'gauge',
      min,
      max,
      splitNumber: 10,
      radius: '90%',
      axisLine: {
        lineStyle: {
          width: 15,
          color: thresholds.map((t, i) => {
            const prevValue = i > 0 ? thresholds[i - 1].value : min
            return [t.value / max, t.color]
          })
        }
      },
      pointer: {
        itemStyle: {
          color: 'auto'
        }
      },
      axisTick: {
        distance: -15,
        length: 5,
        lineStyle: {
          color: '#999',
          width: 1
        }
      },
      splitLine: {
        distance: -20,
        length: 10,
        lineStyle: {
          color: '#999',
          width: 2
        }
      },
      axisLabel: {
        distance: -25,
        color: '#999',
        fontSize: 10
      },
      detail: {
        valueAnimation: true,
        formatter: `{value}${unit}`,
        color: 'auto',
        fontSize: 16
      },
      title: {
        offsetCenter: [0, '70%'],
        fontSize: 12
      },
      data: [{
        value: value.toFixed(1),
        name: title
      }]
    }]
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px` }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

interface AnalysisResultChartProps {
  results: {
    indicator_id: string
    result_status: string
    result_value: any
  }[]
  height?: number
}

export function AnalysisResultChart({
  results,
  height = 300
}: AnalysisResultChartProps) {
  const statusCounts = {
    pass: results.filter(r => r.result_status === 'pass').length,
    warning: results.filter(r => r.result_status === 'warning').length,
    fail: results.filter(r => r.result_status === 'fail').length,
    error: results.filter(r => r.result_status === 'error').length
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center'
    },
    series: [{
      name: '分析结果',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {c}'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      data: [
        { value: statusCounts.pass, name: '通过', itemStyle: { color: '#52c41a' } },
        { value: statusCounts.warning, name: '警告', itemStyle: { color: '#faad14' } },
        { value: statusCounts.fail, name: '失败', itemStyle: { color: '#ff4d4f' } },
        { value: statusCounts.error, name: '错误', itemStyle: { color: '#8c8c8c' } }
      ].filter(d => d.value > 0)
    }]
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px` }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

export {
  TimeSeriesChart,
  HistogramChart,
  BoxPlotChart,
  ScatterChart,
  CorrelationHeatmap,
  GaugeChart,
  AnalysisResultChart
}
