# Edition 2 显示问题修复总结

## 问题描述
用户报告在 Edition 2 中：
- DeepSeek 出现了 2 次
- Qwen 没有正常显示（显示为 DeepSeek 的标题）
- Qwen 有开仓记录，但标题显示错误

## 问题诊断

### 1. 配置验证 ✅
运行 `test_model_config.py` 确认：
- QWEN3 MAX 配置正确
- DEEPSEEK V3.2 配置正确
- 图标映射正确

### 2. 已修复的问题

#### 修复 1: 前端模型名称不一致
**位置**: `static/js/app.js` (行 944-968)
**问题**: `getStrategy()` 和 `getDesc()` 函数中使用旧的模型名称 `'DEEPSEEK CHAT V3.1'`
**修复**: 更新为 `'DEEPSEEK V3.2'` 并保留向后兼容

```javascript
// 修复前
'DEEPSEEK CHAT V3.1': '平衡型',

// 修复后
'DEEPSEEK V3.2': '平衡型',
'DEEPSEEK CHAT V3.1': '平衡型',  // 兼容旧名称
```

#### 修复 2: 强制刷新前端缓存
**位置**: `templates/edition2.html` (行 178)
**修复**: 更新 JavaScript 版本号从 `v=20251026001` 到 `v=20251027002`

```html
<script src="/static/js/app.js?v=20251027002"></script>
```

## 解决方案

### 用户操作步骤

1. **清除浏览器缓存** (推荐)
   - Chrome/Edge: `Ctrl+Shift+Delete` (Mac: `Cmd+Shift+Delete`)
   - 选择"缓存的图片和文件"
   - 时间范围选择"全部时间"
   - 点击"清除数据"

2. **硬刷新页面** (快速方法)
   - Windows: `Ctrl+F5` 或 `Ctrl+Shift+R`
   - Mac: `Cmd+Shift+R`

3. **重启应用服务** (如果上述方法无效)
   ```bash
   # 停止当前服务
   # 重新启动
   python app_dual_edition.py
   ```

### 技术细节

#### 前端图标显示逻辑
```javascript
getAILogoSmall(name) {
    if (name && name.toUpperCase().includes('QWEN')) {
        return '<img src="/static/img/ai/qwen.png?v=2" ...>';
    } else if (name && name.toUpperCase().includes('DEEPSEEK')) {
        return '<img src="/static/img/ai/deepseek.jpg" ...>';
    }
    return '';
}
```

#### 后端模型初始化
```python
# config.py
AI_MODELS = [
    {
        'id': 1,
        'name': 'QWEN3 MAX',
        'model': 'qwen/qwen3-vl-32b-instruct',
        'strategy': 'aggressive'
    },
    {
        'id': 2,
        'name': 'DEEPSEEK V3.2',
        'model': 'deepseek/deepseek-v3.2-exp',
        'strategy': 'balanced'
    }
]
```

#### API调用路由
- Edition 1: `/api/edition1/`
- Edition 2: `/api/edition2/`

确保前端正确使用对应的API前缀。

## 验证步骤

1. 访问 `http://localhost:5001/edition2`
2. 检查页面上是否显示两个不同的AI模型卡片：
   - ✅ QWEN3 MAX (紫色，qwen图标)
   - ✅ DEEPSEEK V3.2 (蓝色，deepseek图标)
3. 查看"模型对话"标签页，确认两个模型都有各自的对话记录
4. 查看"每一笔交易"标签页，确认交易记录显示正确的模型名称

## 可能的其他问题

如果问题仍然存在，可能是以下原因：

### 1. WebSocket连接问题
检查浏览器控制台是否有WebSocket错误。

### 2. 模型初始化顺序
检查服务器日志，确认两个模型都成功初始化：
```
✓ QWEN3 MAX (qwen/qwen3-vl-32b-instruct)
✓ DEEPSEEK V3.2 (deepseek/deepseek-v3.2-exp)
```

### 3. 聊天历史混淆
检查 `trader.chat_history` 是否正确关联到各自的模型。

## 调试工具

### 测试配置
```bash
python test_model_config.py
```

### 查看实时日志
服务器端会打印详细的AI决策日志：
```
🤖 [E2] 开始AI决策（含新闻）...
  → QWEN3 MAX 开始获取账户...
  → DEEPSEEK V3.2 开始获取账户...
```

### 浏览器控制台调试
打开浏览器开发者工具 (F12)，在 Console 标签页输入：
```javascript
// 查看当前加载的模型数据
console.log(app.allChats);  // 查看聊天记录
console.log(app.allTrades);  // 查看交易记录
```

## 总结

本次修复主要解决了：
1. ✅ 前端模型名称映射不一致
2. ✅ 强制刷新前端缓存

预期结果：
- Edition 2 应该显示两个独立的AI模型
- 每个模型有自己的名称、图标和对话记录
- 交易记录正确归属到对应的模型

如果问题仍然存在，请查看服务器日志并提供详细的错误信息。

