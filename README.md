# xu-skills

通用(非项目专用)的 Claude Code skill 集,打包成一个插件。

## 包含的 skill

### learning-skill
基于 Benjamin Bloom 的 2-Sigma 与掌握学习法的一对一个性化学习工作流:生成课程、判断掌握度、补充讲解、维护学习进度。

### learning-skill-plus
learning-skill 的加强版:在掌握学习之上加入**间隔重复、主动回忆、苏格拉底提问**,以及复习路由、错题/遗漏追踪、复习计划、"多久没学"查询。

### vibe-scripts
写**独立 Python 小工具/脚本**(自动化、数据处理、抓包分析、批量转换、串口调试等)的架构模板与分级规范。生成脚本前先加载它。

## 安装(Claude Code)

```
/plugin marketplace add patrick1099/xu-skills
/plugin install xu-skills@xu-skills
```

安装后这三个 skill 即按各自触发条件自动生效。
