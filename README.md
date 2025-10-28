# S3 Finder - macOS风格S3客户端

一个基于Flask和Bootstrap的macOS风格S3客户端，提供类似Finder的用户界面，支持多个S3服务器管理。

## 功能特性

### 🎨 macOS Finder风格界面
- 仿macOS Finder的现代化UI设计
- 支持网格视图和列表视图切换
- 直观的侧边栏导航
- 路径栏导航显示当前位置

### 🌐 多服务器支持
- 支持配置多个S3服务器（阿里云OSS、腾讯云COS、AWS S3等）
- 服务器配置本地存储，安全可靠
- 快速切换不同S3服务器

### 📁 文件管理
- **浏览**: 列出存储桶和文件，支持文件夹导航
- **上传**: 拖拽上传或点击选择文件上传
- **下载**: 单个或批量下载文件
- **删除**: 删除文件和文件夹
- **新建文件夹**: 在S3中创建文件夹

### 🎯 用户体验
- 右键菜单快捷操作
- 键盘快捷键支持（Ctrl+A全选，Delete删除等）
- 文件选择和批量操作
- 实时状态显示
- 响应式设计，支持移动端

## 快速开始

### 1. 环境要求
- Python 3.7+
- pip

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行应用
```bash
python app.py
```

### 4. 访问应用
打开浏览器访问: http://localhost:5000

## 首次使用

1. **启动应用后**，点击右上角的"设置"按钮
2. **添加S3服务器**：
   - 服务器名称：自定义名称（如：阿里云OSS）
   - Access Key ID：您的S3访问密钥ID
   - Access Key Secret：您的S3访问密钥Secret
   - Endpoint URL：S3服务端点（如：https://oss-cn-beijing.aliyuncs.com）
   - 区域：服务器区域（如：oss-cn-beijing）

3. **开始使用**：
   - 从左侧选择服务器
   - 选择存储桶
   - 开始浏览和管理文件

## 支持的S3服务

本项目基于AWS S3协议，支持所有兼容S3 API的云存储服务：

- ✅ 阿里云对象存储OSS
- ✅ 腾讯云对象存储COS
- ✅ 七牛云对象存储Kodo
- ✅ AWS S3
- ✅ MinIO
- ✅ 其他S3兼容服务

## 配置示例

### 阿里云OSS
```
服务器名称: 阿里云OSS北京
Access Key ID: LTAI4GCH1vX6DKqJWxd6****
Access Key Secret: 8vE6wQv3QY8r6tPd4nLj7kM5nT7bY****
Endpoint URL: https://oss-cn-beijing.aliyuncs.com
区域: oss-cn-beijing
```

### 腾讯云COS
```
服务器名称: 腾讯云COS广州
Access Key ID: AKIDz8l5p9q3m6k1j4w7e2r5t6y8u0i****
Access Key Secret: 9k7m5j3h1g8f6d4s2a0q1w3e5r7t9y****
Endpoint URL: https://cos.ap-guangzhou.myqcloud.com
区域: ap-guangzhou
```

### AWS S3
```
服务器名称: AWS S3美东
Access Key ID: AKIAIOSFODNN7EXAMPLE
Access Key Secret: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Endpoint URL: https://s3.us-east-1.amazonaws.com
区域: us-east-1
```

## 项目结构

```
S3/
├── app.py                 # Flask主应用
├── config.py             # 配置管理模块
├── s3_client.py          # S3客户端封装
├── requirements.txt      # Python依赖
├── README.md            # 项目说明文档
├── static/              # 静态文件
│   ├── css/
│   │   └── finder.css   # macOS风格样式
│   └── js/
├── templates/           # HTML模板
│   ├── base.html       # 基础模板
│   └── index.html      # 主页面模板
├── uploads/            # 临时上传目录
├── flask_session/      # Flask会话存储
└── s3_config.json      # S3服务器配置文件（自动生成）
```

## API接口

### 服务器管理
- `GET /api/servers` - 获取所有服务器配置
- `POST /api/servers` - 添加新服务器
- `DELETE /api/servers/{id}` - 删除服务器

### 存储桶操作
- `GET /api/servers/{id}/buckets` - 列出存储桶

### 文件操作
- `GET /api/servers/{id}/objects` - 列出文件对象
- `POST /api/servers/{id}/upload` - 上传文件
- `GET /api/servers/{id}/download` - 下载文件
- `DELETE /api/servers/{id}/delete` - 删除文件
- `POST /api/servers/{id}/folders` - 创建文件夹

## 安全说明

- 🔒 所有S3配置信息存储在本地文件`s3_config.json`中
- 🔒 配置文件包含敏感信息，请妥善保管
- 🔒 建议在生产环境中使用HTTPS
- 🔒 访问密钥仅在内存中使用，不会记录到日志

## 常见问题

### Q: 如何添加多个S3服务器？
A: 点击"设置"按钮，可以添加多个不同厂商的S3服务器配置。

### Q: 支持大文件上传吗？
A: 支持最大100MB的单文件上传，可通过修改`MAX_CONTENT_LENGTH`调整。

### Q: 如何批量操作文件？
A: 点击文件可以选中，支持Ctrl+A全选，选中后可以批量下载或删除。

### Q: 配置文件在哪里？
A: 配置文件保存在项目目录下的`s3_config.json`中。

## 开发说明

### 技术栈
- **后端**: Flask + boto3
- **前端**: Bootstrap 5 + Bootstrap Icons
- **样式**: 自定义CSS，模仿macOS Finder
- **存储**: 本地JSON文件存储配置

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python app.py

# 开发模式运行（自动重载）
export FLASK_ENV=development
python app.py
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

---

**注意**: 这是一个本地工具，请确保您的S3访问密钥安全，不要将配置文件分享给他人。