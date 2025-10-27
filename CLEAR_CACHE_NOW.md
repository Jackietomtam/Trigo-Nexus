# 🔴 紧急：清除浏览器缓存说明

## 问题确认

**后台数据完全正确** ✅
- API返回：QWEN3 MAX 和 DEEPSEEK V3.2
- 服务器运行正常
- 代码已修复

**问题根源：浏览器缓存了旧的JavaScript文件**

---

## 💡 立即清除缓存的方法

### 方法1：硬刷新（最快）⚡

打开 http://localhost:5001/edition2 后：

- **Mac**: 按 `Cmd + Shift + R`
- **Windows**: 按 `Ctrl + F5` 或 `Ctrl + Shift + R`

### 方法2：开发者工具清除（推荐）🔧

1. 打开 http://localhost:5001/edition2
2. 按 `F12` 打开开发者工具
3. **右键点击刷新按钮**（地址栏左边的圆圈）
4. 选择 **"清空缓存并硬性重新加载"**

### 方法3：完全清除缓存（彻底）🧹

**Chrome / Edge:**
1. 按 `Cmd+Shift+Delete` (Windows: `Ctrl+Shift+Delete`)
2. 选择 **"缓存的图片和文件"**
3. 时间范围：**"全部时间"**
4. 点击 **"清除数据"**
5. 重新打开浏览器访问页面

**Safari:**
1. 按 `Cmd+Option+E` 清空缓存
2. 或：Safari > 清除历史记录 > 选择"所有历史记录"
3. 勾选"缓存"
4. 点击"清除历史记录"

**Firefox:**
1. 按 `Cmd+Shift+Delete` (Windows: `Ctrl+Shift+Delete`)
2. 选择 **"缓存"**
3. 时间范围：**"全部"**
4. 点击 **"立即清除"**

---

## 🔍 验证方法

清除缓存后，打开开发者工具（F12），在Console标签页输入：

```javascript
// 检查JavaScript版本
document.querySelector('script[src*="app.js"]').src

// 应该显示：/static/js/app.js?v=20251027002
```

然后刷新页面，你应该看到：
- 🟣 **QWEN3 MAX** (紫色卡片，Qwen图标)
- 🔵 **DEEPSEEK V3.2** (蓝色卡片，DeepSeek图标)

---

## 🎯 如果还是看到2个DeepSeek

### 检查步骤：

1. **打开开发者工具** (F12)
2. 切换到 **Network** 标签
3. **刷新页面**
4. 找到 `app.js` 文件
5. 查看 **Status** 列：
   - 如果是 `200` - 表示从服务器加载 ✅
   - 如果是 `(disk cache)` 或 `304` - 表示还在用缓存 ❌

### 解决方案：

#### 禁用缓存测试（临时）
1. 开发者工具保持打开
2. 切换到 **Network** 标签
3. **勾选** "Disable cache" 选项
4. 刷新页面

#### 无痕模式测试
1. 打开**无痕/隐私浏览模式**
   - Chrome: `Cmd+Shift+N` (Windows: `Ctrl+Shift+N`)
   - Safari: `Cmd+Shift+N`
   - Firefox: `Cmd+Shift+P` (Windows: `Ctrl+Shift+P`)
2. 访问 http://localhost:5001/edition2
3. 应该看到正确的两个模型

---

## 📱 手机/平板清除缓存

### iPhone/iPad (Safari)
1. 设置 > Safari
2. 清除历史记录与网站数据
3. 确认

### Android (Chrome)
1. Chrome > 设置 > 隐私和安全
2. 清除浏览数据
3. 选择"缓存的图片和文件"
4. 清除

---

## 🆘 终极解决方案

如果以上方法都不行，尝试：

### 方案1：更改版本号更大
编辑 `templates/edition2.html` 第178行：

```html
<!-- 改成更大的版本号 -->
<script src="/static/js/app.js?v=99999999"></script>
```

然后重启服务。

### 方案2：使用时间戳
在地址栏访问：
```
http://localhost:5001/edition2?t=1234567890
```

每次更改 `t=` 后面的数字。

---

## ✅ 成功标志

清除缓存成功后，你会看到：

### Edition 2 页面
```
┌─────────────────────┬─────────────────────┐
│   🟣 QWEN3 MAX      │  🔵 DEEPSEEK V3.2   │
│   $100,000.00       │  $100,000.00        │
│   +$0.00            │  +$0.00             │
└─────────────────────┴─────────────────────┘
```

### 模型对话标签
- QWEN3 MAX 的对话 ✅
- DEEPSEEK V3.2 的对话 ✅

### 交易记录
- 交易记录正确显示模型名称 ✅

---

## 📞 还有问题？

1. 截图发给我
2. 在开发者工具Console中运行：
```javascript
fetch('/api/edition2/leaderboard')
  .then(r => r.json())
  .then(d => console.log(d))
```
3. 把输出发给我

**记住：后台数据100%正确，只是浏览器缓存问题！**

