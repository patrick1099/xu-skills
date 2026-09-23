# 图：按类型选画法

| 图的类型 | 画法 | 源文件 | 为什么 |
|---|---|---|---|
| 分层、网格、步骤、字节格、比例时间轴、对比 | HTML/CSS（`sf-*` 类） | 直接写在页面里 | 布局自动、配色一致、改字不用重排，最省 |
| 连线多的：状态机、调用关系、数据流、模块依赖 | D2 | `diagrams/<名>.d2` | 自动布局，线不乱穿；主题配色自动套 |
| 时序图：几个参与者之间一来一回 | D2 `shape: sequence_diagram`，或 mermaid `sequenceDiagram` | `.d2` 或页内代码块 | 只写“谁发给谁什么” |
| 位域、波形、寄存器时序 | WaveDrom | `diagrams/<名>.wavedrom.json` | 专门画位和时序 |
| 用户要亲手拖着调的图 | draw.io | `diagrams/<名>.drawio.svg` | 同一个文件既是图片也是 draw.io 源文件 |
| 很简单的流程示意 | mermaid 代码块 | 页内 | 最便宜 |

渲染：`sf.py diagrams <deck>`，结果在 `public/diagrams/<名>.svg`，页面里用 `<Diagram src="<名>" />` 引用。

## 尺寸先想好

- 图的形状要和留给它的位置一致。**横向的图放整页宽；竖向的图才放进 `split` 的一栏**。窄高的图塞进宽矮的位置会被缩到看不清。
- D2 用 `direction: right` 画横向、`direction: down` 画竖向。
- 一张图节点别超过十几个；再多就拆成总览图 + 细节图两页。

## D2

`sf.py diagrams` 渲染时会自动在每个 `.d2` 前面拼上主题配色（`diagrams/_theme.d2`）和放大字号的规则，**源文件里不用写引入**。以 `_` 开头的 `.d2` 不单独渲染，可以放公共片段，用 `...@_片段名` 引入。

```d2
direction: right

浏览器: 浏览器 {shape: rectangle}
网关: API 网关
服务: 订单服务
库: 数据库 {shape: cylinder}

浏览器 -> 网关: HTTPS
网关 -> 服务: 转发
服务 -> 库: 读写
服务 -> 网关: 事件回调 {style.stroke-dash: 3}

流程: 下单流程 {
  校验 -> 扣库存 -> 生成订单
}
```

- 容器（大括号）用来分组；`style.stroke-dash: 3` 画虚线；`{shape: cylinder}` 存储、`{shape: queue}` 队列、`{shape: diamond}` 判断。
- 强调某个节点：`节点.style.stroke-width: 3`，或 `节点.class: hot` 配合 `classes: {hot: {style.fill: "#F4E6BE"}}`（颜色取主题里 accent-soft 的值）。
- 布局引擎默认 elk；某张图想换就在文件前三百个字符内写一行注释 `# sf: layout=dagre`。
- 渲染报错的行号比源文件多几行（前面拼了前言），错误里的 `note` 会写多几行。

### 时序图

```d2
shape: sequence_diagram
客户端; 网关; 服务
客户端 -> 网关: 登录请求
网关 -> 客户端: 令牌
客户端 -> 服务: 查询订单
服务 -> 客户端: 订单列表
客户端 -> 服务: 提交修改
服务 -> 客户端: 完成
```

## WaveDrom

位域（寄存器、控制码）：

```json
{ "reg": [
  { "bits": 5, "name": "功能码" },
  { "bits": 1, "name": "保留" },
  { "bits": 1, "name": "后续帧" },
  { "bits": 1, "name": "方向", "type": 4 }
], "config": { "hspace": 700 } }
```

波形（串口、时序）：

```json
{ "signal": [
  { "name": "PWR", "wave": "01....0" },
  { "name": "TX",  "wave": "x.=.=.x", "data": ["AT", "发帧"] }
] }
```

## draw.io

- AI 可以直接写 `.drawio.svg`，但坐标要自己算，成本高；只在用户要亲手调的图上用。
- 更省的办法：先写 mermaid，让用户在 draw.io 里用“排列 → 插入 → 高级 → Mermaid”导入成可编辑图形，调好后存成 `diagrams/<名>.drawio.svg`。
- 用户改过的 `.drawio.svg` 只读不改，除非用户要求。
