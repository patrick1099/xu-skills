# 写页面：模板里的版式、类和 Slidev 语法

只列本模板用得到的。Slidev 完整语法见官方 agent skill：https://github.com/slidevjs/slidev/tree/main/skills/slidev

## 文件组织

- `slides.md`：封面 + 按顺序引入各节：
  ```md
  ---
  src: ./pages/02-链路总览.md
  ---
  ```
- `pages/NN-名字.md`：一节一个文件，页与页之间用单独一行 `---` 分隔。每页可带 frontmatter：
  ```md
  ---
  layout: split
  heading: 标题写结论
  ratio: "5/7"
  ---
  ```

## 版式（`layout:`）

| 版式 | 用途 | 写法 |
|---|---|---|
| 默认（不写） | 标题 + 内容 | `# 标题` 然后内容 |
| `cover` | 封面 | 只在 slides.md 第一页 |
| `section` | 章节页 | `num: "02"`，`# 章节名` + `<p class="sf-sub">一句话</p>` |
| `split` | 左右分栏 | `heading:` 写标题（横跨两栏），`ratio: "5/7"`；左栏内容，`::right::` 之后是右栏。`valign: center` 让两栏垂直居中（默认顶部对齐） |
| `statement` | 一句大字观点 | `# 观点` + 可选 `<p class="sf-sub">` |

## 结构块（HTML + `sf-*` 类）

HTML 块和 Markdown 之间留空行。

```html
<!-- 横排步骤，自动加箭头；竖排加 vert -->
<div class="sf-flow">
  <div class="sf-step"><b>准备</b><span>一句说明</span></div>
  <div class="sf-step hot"><b>重点步</b><span>...</span></div>
</div>

<!-- 卡片网格：sf-grid-2 / 3 / 4 -->
<div class="sf-grid-3">
  <div class="sf-card"><h3>标题</h3><p>说明</p><span class="sf-ref">file.c:120</span></div>
</div>

<!-- 比例时间轴：--w 按数值分宽度 -->
<div class="sf-timeline">
  <div class="sf-seg" style="--w:3">开机<small>≤30s</small></div>
  <div class="sf-seg hot" style="--w:24">联网<small>≤240s</small></div>
</div>

<!-- 键值对 -->
<div class="sf-kv"><div><b>超时</b><span>600 s</span></div></div>

<!-- 字节格：帧格式、寄存器 -->
<div class="sf-bytes">
  <div class="sf-byte hot">68<small>起始</small></div>
  <div class="sf-byte wide">…<small>数据域</small></div>
</div>

<!-- 大数字 -->
<div class="sf-big">80%</div><div class="sf-label">时间耗在联网</div>

<div class="sf-note">提示框（浅底，无边条）</div>
<span class="sf-tag">标签</span> <span class="sf-tag hot">重点</span> <span class="sf-ref">path:line</span>
```

修饰：`.hot` 强调（整页只强调一处最好）、`.dim` 变淡、`.sf-muted`、`.sf-small`。UnoCSS 原子类（`mt-6`、`w-1/2`、`text-sm`、`grid grid-cols-2 gap-4`）可以直接用来微调间距。

## 图

```html
<Diagram src="文件名不带扩展名" h="360" caption="说明" />
```

对应 `public/diagrams/<src>.svg`，由 `sf.py diagrams` 从 `diagrams/` 渲染出来。选哪种画法见 `diagram-routing.md`。mermaid 可直接写 ```` ```mermaid ```` 代码块。

## 代码

````md
```c {2|4-6|all}
代码
```
````

- `{2|4-6|all}`：每次点击高亮下一组行，讲解时逐步推进。打印/截图显示最后一组。
- 行号：`{lines:true}` 放在高亮范围后面，如 ```` ```c {2|4-6}{lines:true} ````。
- 长代码只截关键段；需要保留上下文时加 `// ...` 表示省略。

## 逐步出现

```html
<v-clicks>

- 第一条
- 第二条

</v-clicks>

<div v-click>点一下才出现</div>
```

## 讲稿

每页末尾：

```md
<!--
这页要讲清：……
强调：……
-->
```
