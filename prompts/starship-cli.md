你正在为一个 Node.js CLI 项目开发一个精致的 2D 终端动画。

目标：
- 动画主题：Starship 从发射、级间分离，到最后助推器被塔架"筷子"回收
- 平台：macOS、Linux、Windows PowerShell
- 技术要求：Node.js、ANSI 终端渲染、逐帧动画、可降级
- 风格要求：精致、细节丰富、颜色层次明显、尾焰和烟雾必须动态
- 兼容要求：PowerShell 必须支持；窗口过小要提示；Ctrl+C 要恢复光标

工程要求：
1. 先搭建渲染引擎，再做场景
2. 采用 src/engine、src/scene、src/entity 分层
3. 不要把绘制逻辑写死在入口文件
4. 所有魔法数字提取到配置文件
5. 每完成一个阶段都运行并自测
6. 优先保证 launch / separation / catch 三个高潮段落
7. 优先使用简单稳定字符，不依赖复杂 Unicode
8. 所有对齐必须考虑 ANSI 宽度问题
9. 为 Windows PowerShell 增加 compat 降级模式
10. 输出清晰的 README 和运行命令

请按以下顺序工作：
- 第一步：创建目录结构与基础文件
- 第二步：实现 screen buffer、renderer、loop
- 第三步：实现 launchpad 和 liftoff
- 第四步：实现 separation
- 第五步：实现 return 与 chopsticks catch
- 第六步：补齐 CLI 参数、兼容检测、清理逻辑
- 第七步：自测并修复闪烁、对齐、颜色降级问题

代码要求：
- 使用 ES modules
- 保持函数小而清晰
- 给核心模块加注释
- 不要引入不必要的大型依赖
- 所有平台相关逻辑集中在 util/tty.js 和 engine/colors.js
