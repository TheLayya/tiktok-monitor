# 贡献指南

感谢你对 TikTok Monitor 项目的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请通过 [GitHub Issues](https://github.com/your-username/tiktok-monitor/issues) 提交，并包含以下信息：

- Bug 的详细描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Docker 版本等）
- 相关日志或截图

### 提出新功能

如果你有新功能的想法，欢迎通过 Issues 提出，并说明：

- 功能的用途和价值
- 预期的实现方式
- 可能的替代方案

### 提交代码

1. **Fork 项目**

   点击页面右上角的 Fork 按钮，将项目 Fork 到你的账号下。

2. **克隆仓库**

   ```bash
   git clone https://github.com/your-username/tiktok-monitor.git
   cd tiktok-monitor
   ```

3. **创建分支**

   ```bash
   git checkout -b feature/your-feature-name
   ```

   分支命名规范：
   - `feature/xxx`：新功能
   - `fix/xxx`：Bug 修复
   - `docs/xxx`：文档更新
   - `refactor/xxx`：代码重构

4. **开发和测试**

   - 遵循项目的代码风格
   - 添加必要的注释
   - 确保代码可以正常运行
   - 更新相关文档

5. **提交更改**

   ```bash
   git add .
   git commit -m "feat: add some feature"
   ```

   提交信息规范：
   - `feat`: 新功能
   - `fix`: Bug 修复
   - `docs`: 文档更新
   - `style`: 代码格式调整
   - `refactor`: 代码重构
   - `test`: 测试相关
   - `chore`: 构建/工具相关

6. **推送分支**

   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**

   在 GitHub 上创建 Pull Request，并描述你的更改。

## 代码规范

### Python (后端)

- 遵循 PEP 8 规范
- 使用类型注解
- 添加文档字符串
- 函数和变量使用描述性命名

### JavaScript/Vue (前端)

- 使用 ES6+ 语法
- 组件使用 Composition API
- 遵循 Vue 3 风格指南
- 使用有意义的变量和函数名

### 提交前检查

- [ ] 代码可以正常运行
- [ ] 没有语法错误
- [ ] 遵循项目代码风格
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确

## 开发环境设置

### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 问题和讨论

如有任何问题，欢迎通过以下方式联系：

- GitHub Issues
- GitHub Discussions
- Email: your-email@example.com

再次感谢你的贡献！🎉
