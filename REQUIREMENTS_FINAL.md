# 车载控制器测试数据分析与测试报告编写系统
## 最终需求规格说明书

**项目名称:** vehicle-controller-test-analysis
**版本:** v3.0 (最终确认版)
**创建日期:** 2026-03-17
**负责人:** 垒 & 追求卓越

---

## 1. 项目定位

### 1.1 核心价值

这是一个**本地化、文件驱动的测试数据分析平台**，专注于：
- 测试完成后快速导入数据并自动分析
- 生成符合车企要求的双报告（标准报告+溯源报告）
- 支持离线分析，不依赖外网
- Web界面 + 本地应用程序双端支持

### 1.2 部署方式

**关键约束：**
- ✅ 本地部署（不出本地网络）
- ✅ 无云端依赖
- ✅ 数据安全（无泄露风险）
- ✅ 支持离线运行

---

## 2. 数据格式全景

### 2.1 测试阶段与数据格式

| 测试阶段 | 主要数据格式 | 典型文件扩展名 | 采样频率 | 分析重点 |
|---------|------------|--------------|---------|---------|
| **MIL (模型在环)** | Simulink日志 | `.mat`, `.csv` | 1kHz-10kHz | 逻辑正确性、算法验证 |
| **HIL (硬件在环)** | 实时采集数据 | `.mat`, `.log`, `.csv`, `.blf`, `.asc` | 1kHz-20kHz | 实时性、精度、边界条件 |
| **DVP (设计验证)** | 台架测试数据 | `.csv`, `.xlsx`, `.dat` | 10Hz-1kHz | 性能指标、耐久性 |
| **整车测试** | 实车CAN日志 | `.log`, `.asc`, `.blf`, `.csv` | 10Hz-1kHz | 功能完整性、用户体验 |
| **手动测试** | 手工记录表 | `.xlsx`, `.csv` | - | 用例执行、定性评价 |
| **自动测试** | 自动化脚本输出 | `.xml`, `.json`, `.csv` | - | 回归测试、覆盖率 |

### 2.2 详细数据格式

#### 2.2.1 MATLAB/Simulink 数据
```
格式：
- .mat (MATLAB v7.3, v6): Simulink日志
- .csv: 导出的时序数据

典型工具：
- Simulink Test
- Simulink Verification and Validation

字段示例：
- 时间戳 (time)
- 仿真模型信号 (model_output_*, plant_output_*)
- 控制器信号 (controller_*)
- 状态机状态 (state_*)
- 参数 (params.*)
```

#### 2.2.2 HIL 测试数据
```
格式：
- .mat: Vector CANoe/Vector Test Data
- .log: Vector CANoe/CANalyzer 日志
- .blf: Vector Binary Log Format
- .asc: Vector ASCII Log Format
- .csv: 导出的时序数据
- .xlsx: 测试用例执行记录

典型工具：
- Vector CANoe/CANalyzer
- dSPACE ControlDesk
- National Instruments VeriStand
- ETAS LabCar
- light HIL

数据类型：
- CAN总线数据（与DBC一致）
- 模拟量数据（与DBC不一致，有说明文件）
- 数字量数据（与DBC不一致，有说明文件）
- PWM信号
- 故障注入数据
```

#### 2.2.3 CAN 总线数据
```
格式：
- .blf: Vector Binary Log
- .log: Vector ASCII Log
- .asc: Vector ASCII Log；周立功canfd log
- .csv: 转换后的表格数据
- .mdf: Measurement Data Format (ASAM standard)

典型工具：
- Vector CANoe/CANalyzer
- PCAN Viewer
- Intrepid Control Systems Vehicle Spy

关键特性：
- ✅ CAN数据信号名与DBC一致
- ✅ 需要通过DBC解析报文为信号
```

#### 2.2.4 DVP 台架测试数据
```
格式：
- .csv: 标准时序数据
- .xlsx: Excel表格
- .dat: 自定义格式（台架专用）
- 说明文件：信号映射关系

典型工具：
- AVL TestSuite
- Horiba STARS
- 台架厂商专用软件

关键特性：
- ⚠️ 非CAN数据与DBC不一致
- ✅ 有说明文件定义信号映射关系
- ✅ 需要建立信号映射机制
```

#### 2.2.5 整车测试数据
```
格式：
- .log: 车载日志
- .blf/.asc: CAN总线数据
- .csv: 导出数据
- .kml: GPS轨迹

典型工具：
- 车载诊断工具
- Vector CANoe

字段示例：
- 时间戳
- 车速、转向角、档位
- 加速踏板、制动踏板
- GPS坐标
- 车辆状态
```

#### 2.2.6 手动测试数据
```
格式：
- .xlsx: 测试用例执行表
- .csv: 导入格式
- .txt: 手动日志
- .log: 手动日志

典型内容：
- 测试用例编号 (TC_ID)
- 测试用例名称 (TC_Name)
- 测试步骤 (Test_Steps)
- 测试预期 (Test_Expect)
- 测试结果 (Pass/Fail/Blocked)
- 缺陷编号 (Defect_ID)
- 测试人员 (Tester)
- 测试时间 (Test_Date)
- 测试数据 (Test_Data)
- 备注 (Comments)

导入方式：
- Excel导入
- 模板标准化
```

#### 2.2.7 自动测试数据
```
格式：
- .xml: JUnit/CTest测试结果
- .json: JSON格式测试报告
- .csv: 测试数据导出
- .html: 测试报告网页

典型内容：
- 测试套件 (Test_Suite)
- 测试用例 (Test_Case)
- 执行时间 (Duration)
- 结果 (Pass/Fail/Skip)
- 错误堆栈 (Error_StackTrace)
```

### 2.3 数据规模与处理策略

| 数据类型 | 文件大小 | 处理策略 | 说明 |
|---------|---------|---------|------|
| 小型测试 | 2KB ~ 1MB | 内存直接处理 | 手动测试结果、简短日志 |
| 中型测试 | 1MB ~ 50MB | 内存+缓存 | 标准HIL测试、功能测试 |
| 大型测试 | 50MB ~ 200MB | 流式处理 | 长时域测试、耐久测试 |
| 超大型测试 | 200MB ~ 500MB | 分块+流式 | 整车测试路采、故障复现 |

### 2.4 多数据源时间同步

#### 同步挑战

一次测试可能产生多种数据：
1. CAN总线数据（100Hz，基于CANoe时间）
2. 模拟量采集数据（1kHz，基于DAQ硬件时间）
3. 数字量记录（10kHz，基于FPGA时间）
4. 故障注入日志（事件驱动）

#### 同步解决方案

**方案：公共时间基准 + 后处理对齐**

```python
# 数据同步核心流程
1. 识别各数据源的时间戳格式和基准
2. 提取公共事件（如触发信号、重启事件）
3. 计算各数据源之间的时间偏移
4. 选择目标采样率（最高频率的公倍数）
5. 对每个数据源进行重采样
6. 应用插值方法处理频率不一致
   - 线性插值（默认）
   - 样条插值（可选）
   - 阶梯插值（数字量）
7. 生成对齐后的时间序列
8. 记录同步元数据（偏移、插值方法、质量评分）
```

---

## 3. DBC与通信矩阵管理

### 3.1 DBC管理策略

| 特性 | 策略 | 说明 |
|------|------|------|
| 来源 | 从项目获取 | 每个项目有独立DBC |
| 更新频率 | 低（约1月/次） | 项目开发期间会更新 |
| 发布后 | 不再变更 | 项目发布后DBC冻结 |
| 版本管理 | 不需要 | 即时分析，不追溯历史版本 |
| 跨项目 | 不同 | 每个项目独立的DBC |

### 3.2 DBC文件格式

```
支持格式：
- .dbc: Vector DBC Format
- .arxml: AUTOSAR XML
- .xml: 通用XML格式

关键信息：
- Message (报文定义)
  - Message ID
  - Message Name
  - Cycle Time
  - DLC (Data Length Code)
  - Sender Node

- Signal (信号定义)
  - Signal Name
  - Start Bit
  - Signal Length
  - Byte Order (Intel/Motorola)
  - Factor (分辨率)
  - Offset (偏移量)
  - Min/Max (范围)
  - Unit (单位)
  - Value Table (值表)

- Node (节点定义)
  - Node Name
  - Node Type

- Value Tables (值表)
  - Enum Values
  - Display Names
```

### 3.3 信号映射与别名系统

#### 3.3.1 映射场景

**场景1: CAN数据（直接匹配）**
```
DBC中: Vehicle_Speed
数据中: Vehicle_Speed
→ 直接匹配，无需映射
```

**场景2: 非CAN数据（说明文件映射）**
```
DBC中: Motor_Speed
数据中: RPM_Sensor_01
→ 需要映射: RPM_Sensor_01 → Motor_Speed
```

**场景3: 车企归一化（别名系统）**
```
车企A的信号名: Motor_Speed_RPM
车企B的信号名: MotorSpeed_rpm
→ 统一别名: motor_speed
测试用例使用别名: motor_speed
```

#### 3.3.2 映射配置格式

```json
{
  "project_id": "PROJ_001",
  "dbc_file": "project_x.dbc",
  "signal_mappings": [
    {
      "signal_alias": "motor_speed",
      "dbc_signal": "Motor_Speed",
      "data_source": "RPM_Sensor_01",
      "unit_conversion": {
        "from_unit": "counts",
        "to_unit": "rpm",
        "formula": "value * 0.1"
      },
      "description": "电机转速信号"
    },
    {
      "signal_alias": "battery_voltage",
      "dbc_signal": "Battery_Voltage",
      "data_source": "HV_Bus_V",
      "unit_conversion": null
    }
  ],
  "custom_signals": [
    {
      "signal_alias": "motor_power",
      "calculation": "motor_torque * motor_speed / 9550",
      "unit": "kW",
      "description": "电机功率计算"
    }
  ]
}
```

#### 3.3.3 映射管理界面

```
功能：
1. DBC文件导入
2. 信号列表展示
3. 映射关系配置
4. 别名设置
5. 自定义信号公式编辑
6. 映射测试和验证
7. 导出映射配置
```

### 3.4 自定义信号计算

#### 支持的计算类型

```python
# 1. 基本算术运算
signal_new = signal_a + signal_b
signal_new = signal_a * 10

# 2. 单位转换
signal_C = (signal_F - 32) * 5 / 9

# 3. 条件逻辑
signal_state = "ON" if signal_value > 0.5 else "OFF"

# 4. 时间窗口计算
avg_power = avg(motor_power, window=10s)
max_temp = max(battery_temp, window=60s)

# 5. 统计计算
std_dev = std(signal_value, window=10s)
rate_of_change = diff(signal_value) / dt

# 6. 复杂计算
efficiency = (output_power / input_power) * 100
```

#### 计算配置

```json
{
  "custom_signal_id": "SIG_001",
  "signal_alias": "motor_efficiency",
  "calculation": {
    "formula": "(motor_torque * motor_speed * 2 * 3.14159 / 60) / (battery_voltage * motor_current) * 100",
    "input_signals": ["motor_torque", "motor_speed", "battery_voltage", "motor_current"],
    "unit": "%",
    "description": "电机效率计算"
  }
}
```

---

## 4. 测试用例管理

### 4.1 测试用例导入

| 特性 | 策略 | 说明 |
|------|------|------|
| 来源 | Excel文件 | 从其他系统导出 |
| 格式 | 标准Excel模板 | 统一模板规范 |
| 版本管理 | 不需要 | 每次导入覆盖 |
| 系统集成 | 不需要 | 独立管理 |

### 4.2 测试用例Excel格式

```excel
| TC_ID     | TC_Name           | Test_Phase | Pre_Condition | Test_Steps | Expected_Result | Priority |
|-----------|-------------------|------------|----------------|------------|-----------------|----------|
| TC_001    | 电机启动测试       | HIL        | 系统上电       | 1.发送启动指令<br>2.检查状态 | 电机转速>0 | High     |
| TC_002    | 电压边界测试       | HIL        | 系统正常       | 1.降低电压<br>2.检查欠压 | 触发欠压故障 | High     |
```

### 4.3 测试结果管理

| 特性 | 策略 | 说明 |
|------|------|------|
| 结果来源 | 数据分析自动生成 | 基于测试数据和规则 |
| 结果回填 | 导出Excel | 供其他系统导入 |
| 执行跟踪 | 不需要 | 不在本系统 |
| 任务调度 | 不需要 | 不在本系统 |

### 4.4 结果导出格式

```excel
| TC_ID     | TC_Name        | Test_Date   | Result | Signal_Name  | Measured_Value | Expected_Range | Pass/Fail | Notes |
|-----------|----------------|-------------|--------|--------------|----------------|----------------|-----------|-------|
| TC_001    | 电机启动测试    | 2026-03-17  | PASS   | motor_speed  | 2500           | >0             | PASS      | -     |
| TC_002    | 电压边界测试    | 2026-03-17  | PASS   | hv_bus_volt  | 280            | <300           | PASS      | 欠压故障触发 |
```

---

## 5. 报告系统

### 5.1 双报告机制

```
报告A: 标准模板报告（对外）
├─ 目的：正式交付、存档、对外发布
├─ 受众：管理层、客户、质量部门
├─ 内容：精简、专业、格式规范
├─ 格式：PDF / Word
└─ 特点：数据经过处理，只展示关键信息

报告B: 数据溯源报告（内部审核）
├─ 目的：工程师深度审核、问题追溯
├─ 受众：测试工程师、研发工程师
├─ 内容：完整、详细、数据来源标注
├─ 格式：PDF / Word
└─ 特点：每个数据点都有原始出处
```

### 5.2 报告模板策略

| 模板类型 | 更新频率 | 用途 |
|---------|---------|------|
| 最全集模板 | 1月/以上 | 包含所有可能的报告内容和结构 |
| 车企模板A | 根据车企需求 | 从最全集适配 |
| 车企模板B | 根据车企需求 | 从最全集适配 |

### 5.3 模板适配流程

```
1. 从最全集模板开始
   ↓
2. 根据车企需求，选择需要的章节
   ↓
3. 配置章节内容（字段、图表、表格）
   ↓
4. 设置格式（字体、颜色、布局）
   ↓
5. 预览和调整
   ↓
6. 保存为车企专用模板
   ↓
7. 评审和确认（不在本系统）
```

### 5.4 最全集报告结构

```
1. 封面
   - 项目名称
   - 报告编号
   - 报告日期
   - 版本号
   - 编制人/审核人/批准人
   - 车企Logo

2. 目录

3. 测试概述
   - 测试目的
   - 测试范围
   - 测试环境
   - 测试版本
   - 执行摘要（通过/不通过/条件通过）

4. 测试配置
   - DBC版本
   - 信号映射配置
   - 测试用例清单

5. 数据元信息
   - 导入文件清单
   - 时间同步说明
   - 数据质量评估

6. 测试结果汇总
   - 用例总数/通过/失败/阻塞
   - 通过率
   - 关键指标汇总表
   - 异常事件摘要

7. 详细测试结果
   - 按测试用例分组
   - 每个用例的详细结果
   - 信号值对比
   - 图表展示

8. 性能分析
   - 关键性能指标对比
   - 趋势分析图表
   - 基准对比
   - 统计分析

9. 功能测试分析
   - 信号范围检查
   - 信号逻辑检查
   - 值表检查
   - 时序检查

10. 问题列表
    - 问题描述
    - 严重程度
    - 相关信号
    - 发生时间

11. 附录
    - 缩略语
    - 参考资料
    - 完整信号列表
    - DBC定义摘要
```

### 5.5 报告生成流程

```
┌─────────────────────────────────┐
│  1. 导入数据和配置                │
│    - 测试数据文件                │
│    - DBC文件                     │
│    - 信号映射配置                │
│    - 测试用例Excel               │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  2. 执行数据分析和计算            │
│    - 时间同步                    │
│    - 信号提取                    │
│    - 自定义信号计算              │
│    - 指标计算                    │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  3. 生成报告A（标准模板）          │
│    - 应用选定模板                │
│    - 提取关键信息                │
│    - 格式化输出                  │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  4. 生成报告B（数据溯源）          │
│    - 记录完整数据路径            │
│    - 标注数据出处                │
│    - 保留原始数据引用            │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│  5. 打包输出                     │
│    - PDF格式                     │
│    - Word格式                    │
│    - 可选导出                   │
└─────────────────────────────────┘
```

### 5.6 数据溯源报告特性

#### 每个数据点的溯源信息

```json
{
  "signal_alias": "motor_speed",
  "display_value": 3000.0,
  "display_unit": "rpm",
  "timestamp": "2026-03-17T10:23:45.123Z",
  "provenance": {
    "original_signal": "RPM_Sensor_01",
    "original_value": 30000,
    "original_unit": "counts",
    "conversion_formula": "value * 0.1",
    "source_file": "hil_test_001.mat",
    "source_type": "HIL_DAQ",
    "file_offset": 1048576,
    "sampling_rate": 1000,
    "data_quality": "valid",
    "interpolated": false,
    "time_aligned": true,
    "sync_offset": 0.023
  }
}
```

#### 信号溯源表

```
| 信号ID | 信号名称 | 原始信号名 | 原始文件 | 单位转换 | 采样率 | 数据质量 | 备注 |
|--------|---------|-----------|---------|---------|--------|---------|------|
| SIG_001|motor_speed|RPM_Sensor_01|test_001.mat|*0.1|1000Hz|valid| - |
| SIG_002|hv_voltage|HV_Bus_V|test_001.mat|1|100Hz|valid| - |
| SIG_003|calc_power| - | - |自定义|100Hz|valid|计算信号|
```

---

## 6. 核心分析指标体系

### 6.1 指标来源

```
来源1: 测试用例描述 (Test Case Description)
来源2: DBC 文件 (Signal Definitions)
来源3: 通信矩阵 (Communication Matrix)
来源4: 控制需求文档 (Control Requirements)
来源5: 性能规范 (Performance Specifications)
```

### 6.2 指标分类

#### 6.2.1 功能测试指标

**信号范围检查**
```json
{
  "indicator_id": "IND_001",
  "indicator_name": "信号范围检查",
  "signal_alias": "battery_voltage",
  "dbc_signal": "Battery_Voltage",
  "check_type": "range",
  "min_value": 300,
  "max_value": 450,
  "unit": "V",
  "threshold": {
    "pass": "within_range",
    "fail": "out_of_range"
  }
}
```

**信号逻辑检查**
```json
{
  "indicator_id": "IND_002",
  "indicator_name": "信号逻辑检查",
  "check_type": "logic",
  "logic": {
    "if": "gear_state == 'P'",
    "then": "vehicle_speed < 1"
  },
  "description": "档位P时车速应接近0"
}
```

**值表检查**
```json
{
  "indicator_id": "IND_003",
  "indicator_name": "值表检查",
  "signal_alias": "gear_state",
  "value_table": ["P", "R", "N", "D"],
  "check_type": "in_table"
}
```

**时序检查**
```json
{
  "indicator_id": "IND_004",
  "indicator_name": "时序检查",
  "check_type": "sequence",
  "events": [
    {"signal": "shutdown_cmd", "condition": "true"},
    {"signal": "motor_speed", "condition": "< 1", "max_delay": 2.0}
  ],
  "description": "收到关机指令后，电机转速应在2s内降为0"
}
```

**抖动检查**
```json
{
  "indicator_id": "IND_005",
  "indicator_name": "稳态抖动检查",
  "signal_alias": "vehicle_speed",
  "check_type": "jitter",
  "condition": "cruise_target_speed == 100",
  "jitter_threshold": 1.0,
  "window": 10,
  "unit": "km/h",
  "description": "巡航100km/h时，车速抖动应小于1km/h"
}
```

#### 6.2.2 性能测试指标

**阶跃响应时间**
```json
{
  "indicator_id": "PERF_001",
  "indicator_name": "阶跃响应时间",
  "indicator_type": "performance",
  "trigger_signal": "target_speed",
  "trigger_condition": "abs(change) > 10",
  "response_signal": "actual_speed",
  "response_condition": "abs(actual - target) < 1",
  "threshold": {
    "pass": "<= 3.0",
    "warning": "(3.0, 4.0]",
    "fail": "> 4.0"
  },
  "unit": "s"
}
```

**超调量和调节时间**
```json
{
  "indicator_id": "PERF_002",
  "indicator_name": "超调量和调节时间",
  "calculation": {
    "overshoot": "(max_value - target_value) / target_value * 100",
    "settling_time": "time_to_stay_within(tolerance)",
    "tolerance": 0.02
  },
  "threshold": {
    "overshoot_pass": "<= 5",
    "settling_pass": "<= 3.0"
  },
  "unit": {"overshoot": "%", "settling": "s"}
}
```

**稳态误差**
```json
{
  "indicator_id": "PERF_003",
  "indicator_name": "稳态误差",
  "calculation": {
    "steady_state_error": "avg(abs(actual - target))",
    "window": "steady_state_period"
  },
  "threshold": {
    "pass": "<= 2.0"
  },
  "unit": "%"
}
```

**效率指标**
```json
{
  "indicator_id": "PERF_004",
  "indicator_name": "系统效率",
  "custom_signal": "system_efficiency",
  "calculation": "(output_power / input_power) * 100",
  "threshold": {
    "pass": ">= 90",
    "warning": "[85, 90)",
    "fail": "< 85"
  },
  "unit": "%"
}
```

### 6.3 自定义分析规则

#### 调试阶段：Python脚本支持

```python
# 自定义分析脚本示例
def custom_analysis(data):
    """
    自定义分析函数
    data: 包含所有信号的字典
    return: 分析结果字典
    """
    results = {}

    # 示例1: 计算功率积分
    power = data['motor_power']
    energy = np.trapz(power, data['time']) / 3600  # kWh
    results['total_energy'] = energy

    # 示例2: 检测异常模式
    temp = data['motor_temp']
    if np.max(temp) > 100:
        results['temp_anomaly'] = {
            'detected': True,
            'max_temp': np.max(temp),
            'time_of_max': data['time'][np.argmax(temp)]
        }

    return results
```

#### 成熟阶段：规则配置化

```json
{
  "rule_id": "RULE_001",
  "rule_name": "温度异常检测",
  "condition": "motor_temp > 100",
  "actions": [
    {"type": "alert", "message": "电机温度超过100°C"},
    {"type": "mark_event", "label": "temp_overload"}
  ],
  "severity": "high"
}
```

---

## 7. 用户界面与交互

### 7.1 支持的平台

```
✅ Web界面（浏览器访问）
   - Chrome, Firefox, Edge
   - 响应式设计

✅ 本地应用程序
   - Windows桌面应用
   - Electron或Tauri框架

✅ 离线分析支持
   - 不依赖外网
   - 本地计算
```

### 7.2 主要界面模块

```
1. 项目管理
   - 创建项目
   - 导入DBC
   - 配置信号映射
   - 管理测试用例

2. 数据导入
   - 上传测试数据文件
   - 上传测试用例Excel
   - 数据预览
   - 时间同步配置

3. 数据分析
   - 选择分析类型
   - 配置分析规则
   - 执行分析
   - 查看结果

4. 报告生成
   - 选择报告模板
   - 预览报告
   - 生成报告A和报告B
   - 导出PDF/Word

5. 报告模板管理
   - 基于最全集适配
   - 编辑模板
   - 保存模板
```

---

## 8. 技术架构

### 8.1 本地部署架构

```
┌─────────────────────────────────────────────┐
│           用户访问层                         │
│  - Web浏览器 (Chrome/Firefox/Edge)          │
│  - 本地应用程序 (Electron/Tauri)             │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│           Web服务器                          │
│  - 开发环境: Vite Dev Server                │
│  - 生产环境: Nginx/Apache                   │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│           应用服务器                          │
│  ┌─────────────────────────────────────┐   │
│  │  Web前端 (React + TypeScript)        │   │
│  │  - Ant Design                       │   │
│  │  - ECharts / Recharts              │   │
│  │  - Zustand (状态管理)               │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  后端API (FastAPI + Python)         │   │
│  │  - 数据导入和解析                   │   │
│  │  - 数据分析和计算                   │   │
│  │  - 报告生成引擎                     │   │
│  │  - Python脚本执行（调试阶段）       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│           数据存储层                         │
│  ┌─────────────────────────────────────┐   │
│  │  SQLite / PostgreSQL               │   │
│  │  - 项目配置                         │   │
│  │  - 信号映射                         │   │
│  │  - 测试用例                         │   │
│  │  - 报告模板                         │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  文件系统                            │   │
│  │  - 测试数据文件                     │   │
│  │  - DBC文件                          │   │
│  │  - 生成的报告                       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 8.2 技术栈

| 层次 | 技术选型 | 说明 |
|------|---------|------|
| 前端框架 | React 18 + TypeScript | 成熟稳定 |
| UI组件 | Ant Design 5 | B端应用首选 |
| 图表库 | ECharts 5 | 大数据量优化 |
| 状态管理 | Zustand | 轻量高效 |
| 构建工具 | Vite 5 | 快速开发 |
| 后端框架 | FastAPI | 异步高性能 |
| 数据处理 | Pandas, NumPy | 数据分析核心 |
| 文件解析 | python-can, h5py | CAN和MATLAB支持 |
| 报告生成 | ReportLab, python-docx | PDF和Word |
| 数据库 | SQLite（小规模）/ PostgreSQL（大规模） | 轻量/可选 |
| 桌面应用 | Electron / Tauri | 跨平台 |

### 8.3 关键技术点

#### 数据解析

```python
# CAN数据解析
import can

def parse_can_log(file_path):
    """解析Vector CAN log文件"""
    log = can.LogReader(file_path)
    messages = []
    for msg in log:
        messages.append({
            'timestamp': msg.timestamp,
            'arbitration_id': msg.arbitration_id,
            'data': msg.data,
            'dlc': msg.dlc
        })
    return messages

# 通过DBC解码信号
import cantools

def decode_signals(db, messages):
    """通过DBC解码CAN报文为信号"""
    decoded = []
    for msg in messages:
        message = db.get_message_by_frame_id(msg['arbitration_id'])
        decoded_message = message.decode(msg['data'])
        decoded.append({
            'timestamp': msg['timestamp'],
            'message_name': message.name,
            'signals': decoded_message
        })
    return decoded
```

#### MATLAB .mat文件解析

```python
import h5py
import scipy.io

def parse_matlab_v73(file_path):
    """解析MATLAB v7.3格式文件"""
    with h5py.File(file_path, 'r') as f:
        data = {}
        for key in f.keys():
            data[key] = f[key][()]
    return data

def parse_matlab_v6(file_path):
    """解析MATLAB v6格式文件"""
    data = scipy.io.loadmat(file_path)
    return data
```

#### 报告生成

```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def generate_pdf_report(report_data, output_path):
    """生成PDF报告"""
    c = canvas.Canvas(output_path, pagesize=A4)

    # 封面
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 800, report_data['project_name'])
    c.setFont("Helvetica", 14)
    c.drawString(100, 750, f"报告编号: {report_data['report_id']}")

    # 目录、正文等...
    c.save()
```

---

## 9. 项目里程碑

### Phase 1: 核心功能开发（0.5周）

**目标：** 完成MVP，支持基本的数据导入、分析和报告生成

**Week 1: 项目脚手架和数据模型**
- [ ] 搭建前后端项目架构
- [ ] 设计和实现数据库表结构
- [ ] 实现基础API框架
- [ ] 实现文件上传功能

**Week 2: 数据导入和解析**
- [ ] 实现CSV/Excel数据导入
- [ ] 实现MATLAB .mat文件解析
- [ ] 实现Vector CAN log文件解析
- [ ] 实现DBC文件导入和信号解码
- [ ] 实现信号映射配置

**Week 3: 数据分析和指标计算**
- [ ] 实现基础功能指标（范围、逻辑、值表检查）
- [ ] 实现基础性能指标（响应时间、超调量）
- [ ] 实现自定义信号计算
- [ ] 实现Python脚本执行环境（调试）
- [ ] 实现异常检测

**Week 4: 报告生成**
- [ ] 设计最全集报告模板
- [ ] 实现报告A（标准报告）生成
- [ ] 实现报告B（溯源报告）生成
- [ ] 支持PDF和Word导出
- [ ] MVP集成测试

### Phase 2: 功能完善（0.5周）

**目标：** 补充完整功能，提升易用性

**Week 5: 时间同步和数据对齐**
- [ ] 实现多数据源时间同步
- [ ] 实现数据重采样和插值
- [ ] 实现同步质量评估
- [ ] 实现同步元数据记录

**Week 6: 测试用例管理**
- [ ] 实现测试用例Excel导入
- [ ] 实现测试用例和信号关联
- [ ] 实现测试结果自动判定
- [ ] 实现测试结果Excel导出

**Week 7: 报告模板适配**
- [ ] 实现模板适配界面
- [ ] 实现基于最全集的模板定制
- [ ] 实现模板预览和保存
- [ ] 实现模板版本管理

**Week 8: 本地应用程序**
- [ ] 使用Electron/Tauri打包Web应用
- [ ] 实现本地安装包
- [ ] 优化本地性能
- [ ] 完善离线支持

### Phase 3: 优化和发布（0.2周）

**目标：** 性能优化、Bug修复、准备发布

**Week 9-10: 优化和发布**
- [ ] 性能优化（大数据处理）
- [ ] 用户体验优化
- [ ] Bug修复和稳定性测试
- [ ] 编写用户文档
- [ ] 准备发布版本

---

## 10. 风险与应对

### 10.1 技术风险

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| 数据格式多样，解析复杂 | 高 | 高 | 建立插件化解析器，优先支持常见格式 |
| 大文件（500MB）处理性能 | 中 | 高 | 流式处理、分块加载、内存优化 |
| 时间同步准确度 | 中 | 中 | 提供多种同步方法，支持手动调整 |
| 报告生成复杂度高 | 中 | 中 | 模板化设计，渐进式实现 |

### 10.2 业务风险

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| 信号映射配置复杂 | 中 | 中 | 提供可视化映射界面，导入导出功能 |
| 车企报告模板差异大 | 中 | 中 | 最全集+适配策略，灵活配置 |
| Python脚本维护成本 | 低 | 低 | 调试阶段支持，成熟阶段规则配置化 |

---

## 11. 非功能性需求

### 11.1 性能要求

- 数据导入：支持100MB/s
- 数据分析：100MB数据 < 30秒
- 报告生成： < 10秒
- 界面响应： < 2秒
- 支持最大文件：500MB

### 11.2 可用性要求

- 系统可用性：99%
- 离线运行：支持
- 零培训上手：操作直观

### 11.3 安全性要求

- 本地部署：不出内网
- 数据加密：文件加密存储
- 访问控制：基础用户管理

### 11.4 可维护性要求

- 模块化设计
- 清晰的代码结构
- 完善的文档
- 易于扩展

---

## 12. 交付物

### 12.1 软件交付

- [ ] Web应用安装包
- [ ] 本地应用程序安装包（Windows）
- [ ] Docker部署包（可选）
- [ ] 源代码

### 12.2 文档交付

- [ ] 用户手册
- [ ] 部署指南
- [ ] API文档
- [ ] 数据格式规范
- [ ] 报告模板使用指南

### 12.3 示例交付

- [ ] 示例测试数据
- [ ] 示例DBC文件
- [ ] 示例测试用例
- [ ] 示例报告模板

---

**文档版本:** v3.0 (最终确认版)
**最后更新:** 2026-03-17
**状态:** 需求确认完成，待开始开发
