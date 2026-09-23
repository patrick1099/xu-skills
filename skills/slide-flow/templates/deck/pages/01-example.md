---
layout: section
num: "01"
---

# 示例章节

<p class="sf-sub">这一节演示模板自带的版式和组件，正式写作时整份替换</p>

---

# 一件事分三步走完，中间那步最慢

<div class="sf-flow">
  <div class="sf-step"><b>准备</b><span>上电自检，约 3 秒</span></div>
  <div class="sf-step hot"><b>建立连接</b><span>最长 240 秒，失败重试一次</span></div>
  <div class="sf-step"><b>收发数据</b><span>一问一答，直到收到结束帧</span></div>
</div>

<div class="sf-timeline mt-10">
  <div class="sf-seg" style="--w:3">准备</div>
  <div class="sf-seg hot" style="--w:24">建立连接</div>
  <div class="sf-seg" style="--w:10">收发</div>
</div>

<!--
讲稿：强调时间主要耗在建立连接上。
-->

---

# 三类角色各管一段，互不越界

<div class="sf-grid-3">
  <div class="sf-card"><h3>入口</h3><p>决定要不要开始、什么时候开始</p><span class="sf-ref">entry.c:42</span></div>
  <div class="sf-card hot"><h3>流程</h3><p>按状态一步步推进，每步有超时</p><span class="sf-ref">flow.c:120</span></div>
  <div class="sf-card"><h3>内容</h3><p>每一帧里装什么、怎么校验</p><span class="sf-ref">codec.c:300</span></div>
</div>

---
layout: split
heading: 状态机每 10ms 推进一格
ratio: "5/7"
---

- 每个状态只做一件事
- 超时计数在公共入口里递减
- 出错统一走关连接

::right::

```c {3|5-7|all}
void Process(void)
{
    comm_cycle();
    switch (State) {
        case E_Start:     start();      break;
        case E_WaitConn:  wait_conn();  break;
        case E_End:       end();        break;
        default:          fault();      break;
    }
}
```

---

# 横向的图放整页宽，竖向的图才放进分栏

<Diagram src="example" h="300" caption="源文件 diagrams/example.d2 · 渲染 public/diagrams/example.svg" />

<div class="sf-note">图的形状要和留给它的位置一致：窄高的图塞进宽矮的位置会被缩得很小，字就看不清了。</div>

---
layout: statement
---

# 结论写在标题里，不写“总结”两个字

<p class="sf-sub">一页一个观点；观点说不成一句话，就还没想清楚</p>
