# 群组场地报名系统

一个基于 Flask + MySQL 的场地预订管理系统，专为群组成员场地报名和管理设计。

## 功能特点

### 用户功能
- **用户注册**：支持一群/二群选择，注册后需管理员审核
- **用户登录**：群名称和密码登录验证
- **场地报名**：填写场地信息、上传截图、支持多场地和+1报名
- **个人管理**：查看自己提交的场地信息

### 管理员功能
- **用户审核**：批准或拒绝用户注册申请
- **场地管理**：查看所有场地信息，删除不当场地
- **数据汇总**：按时间段汇总场地信息
- **截图查看**：在线查看场地截图

## 技术栈

- **后端**：Python Flask 2.3.3
- **数据库**：MySQL 8.0 (云端数据库)
- **前端**：HTML5 + CSS3 + JavaScript + Bootstrap 5
- **文件上传**：支持 PNG/JPG/JPEG/GIF 格式
- **安全**：密码加密存储，会话管理

## 项目结构

```
mmyq/
├── app.py                 # Flask主应用
├── config.py             # 配置文件
├── requirements.txt      # 依赖包列表
├── README.md            # 项目说明
├── mysql.txt            # 数据库连接信息
├── models/              # 数据模型
│   ├── __init__.py
│   ├── user.py          # 用户模型
│   ├── venue.py         # 场地模型
│   └── admin.py         # 管理员模型
├── utils/               # 工具函数
│   ├── __init__.py
│   ├── database.py      # 数据库连接工具
│   └── helpers.py       # 辅助函数
├── templates/           # HTML模板
│   ├── base.html        # 基础模板
│   ├── index.html       # 首页
│   ├── login.html       # 登录页面
│   ├── register.html    # 注册页面
│   ├── venue_form.html  # 场地表单
│   ├── my_venues.html   # 我的场地
│   └── admin/           # 管理员模板
│       ├── login.html   # 管理员登录
│       ├── dashboard.html # 管理面板
│       └── venues_summary.html # 场地汇总
└── static/              # 静态资源
    ├── css/
    │   └── style.css    # 样式文件
    ├── js/
    │   └── main.js      # JavaScript文件
    └── uploads/         # 上传文件目录
```

## 数据库设计

### 用户表 (users)
- `id` - 主键
- `group_type` - 群组类型 (一群/二群)
- `group_name` - 群名称 (唯一)
- `password_hash` - 加密密码
- `status` - 状态 (pending/approved/rejected)
- `created_at` - 创建时间

### 场地表 (venues)
- `id` - 主键
- `user_id` - 用户ID (外键)
- `venue_number` - 场地号码
- `venue_time` - 场地时间
- `venue_screenshot` - 截图文件名
- `has_multiple_venues` - 是否多场地
- `registration_name` - 报名名称
- `plus_one_name` - +1名称
- `upload_time` - 上传时间
- `status` - 状态 (active/deleted)

### 管理员表 (admins)
- `id` - 主键
- `username` - 用户名
- `password_hash` - 加密密码
- `created_at` - 创建时间

## 安装和运行

### 1. 环境要求
- Python 3.8+
- MySQL 8.0+
- pip

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 数据库配置
系统使用云端MySQL数据库，配置信息已在 `config.py` 中设定：
- 主机：hkg1.clusters.zeabur.com
- 端口：32360
- 数据库：zeabur
- 用户名：root

### 4. 运行应用
```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

### 5. 默认管理员账户
- 用户名：`admin`
- 密码：`admin123`

## 使用说明

### 用户注册和登录
1. 访问首页，点击"注册账户"
2. 选择群组类型，输入群名称和密码
3. 等待管理员审核通过
4. 使用群名称和密码登录

### 场地报名
1. 登录后进入"场地报名"页面
2. 填写场地号码和时间
3. 上传场地截图（可选）
4. 填写报名名称和+1名称
5. 提交报名信息

### 管理员操作
1. 使用管理员账户登录
2. 在管理面板中审核用户注册
3. 查看和管理场地信息
4. 通过"场地汇总"查看时间段统计

## 功能特色

- **响应式设计**：支持手机、平板、桌面设备
- **图片上传**：支持场地截图上传和在线查看
- **数据验证**：前后端数据验证确保数据安全
- **用户友好**：直观的界面设计，操作简单
- **管理便捷**：管理员可高效管理用户和场地信息

## 安全特性

- 密码使用 Werkzeug 加密存储
- 文件上传类型和大小限制
- SQL 注入防护
- 会话管理和权限控制
- 输入数据验证和过滤

## 开发说明

### 添加新功能
1. 在 `models/` 中添加数据模型
2. 在 `app.py` 中添加路由处理
3. 在 `templates/` 中添加HTML模板
4. 更新CSS和JavaScript文件

### 数据库迁移
如需修改数据库结构，编辑 `utils/database.py` 中的 `init_db()` 函数。

### 配置修改
在 `config.py` 中修改应用配置，支持开发和生产环境。

## 版本信息

- **版本**：v1.0.0
- **作者**：mmyq项目组
- **创建时间**：2024年8月
- **技术支持**：Flask + MySQL + Bootstrap

## 许可证

本项目仅供学习和内部使用，请勿用于商业目的。

---

**联系方式**：如有问题请联系项目管理员。# mmyq
