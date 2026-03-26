你现在需要帮我从工业生产（吉利车辆制造企业）和AI工作流结合的角度分析并且提供最佳实践，实现一个skill-build的平台，我们希望可以通过用户日志（外部或者自发收集），然后为用户推荐和集成skill。 目前已有一些默认的skill，我们希望我们的系统可以从已有的对话中（SKILL调用），提供几个新能力来赋能:
- 编排已有skill提供新的skill
- 创建新skill
- 增强已有skill

## Instruction
All code and comment must be in English!但是你在对话框和我沟通时，使用中文

## 后端设计
后端python+langchain实现AI chat能力（集成skill）；
### 基础能力
- 有聊天记录存储能力，先用本地的redis存储，用langchain现有的redis checkpointer；
- 实现agent时候，去查一下langchain官网，使用已有的skill框架。默认集成我的skill库在mini_agent/skills文件夹下。
- 支持前端对skill的改写
- 设计时候需要考虑后续扩展，我们后续会提供industry knowledge embedding提供范例和上下文参考（TODO，现在没有）
- 实现编排/新增/增强skill的能力，使用LLM总结对话记录（后续会有领域知识上下文）。增强skill的出发点需要考虑：1.是否有类似功能 2. 现存的有什么局限 3. 新增的如何解决原有的卡点
- 提供task类别管理能力，用户可以在后台新增task类别以及对应默认选中的skills

## 前端要求
UI科技感，简洁，可以参照chatgpt之类的；React实现
### 路由
1. 聊天页面
然后我的前端需要skills选择的功能，可以plug到我的agent里增强其能力；UI方面需要有一个对话框和聊天记录展示（用户/AI/SKILL）；需要侧边栏有task纬度来管理对话（新建对话能力，后端可以存，可以切换）。新建task时，需要填写名称，描述，类别，可以上传描述文档，可以选择需要的skills（可以多选），这些都要在后台存着。
2. skill library
需要展示built-in skill，以及平台增强/新增/集成的skill（需要在不同tab下）。允许用户在线更新skill。支持用户绑定skill到task类别，可以以task类别纬度展示已经绑定的skill；
3. skill lab
可视化选择task记录（可多选，可勾选industry knowledge），调用后端能力分析skill使用情况并且展示新增/编排/增强后的skill。


你需要提供一些测试数据来展示前后端，并且根据案例实现一些mock skill。
你实现前需要阅读项目仓库架构，参照README.md来启动。（conda activate skill-build）
密钥相关在config里面。你先了解仓库架构再进行开发






