# 系统架构文档

## 1. 系统概览

### 1.1 项目定位

**WutheringWavesAssistant (WWA)** 是一款鸣潮（Wuthering Waves）自动化助手，基于 OCR 文字识别和 YOLO 目标检测实现纯图像识别的游戏辅助工具。主要功能包括：

- **自动刷 BOSS** - 自动导航、战斗、拾取声骸
- **智能连招** - 根据角色技能状态自动执行最优连招
- **声骸锁定** - 自动识别并锁定优质声骸
- **自动剧情** - 自动跳过对话和过场动画
- **日常活动** - 自动完成日常任务

### 1.2 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.10 ~ 3.12 |
| GUI 框架 | PySide6 + PySide6-FluentWidgets |
| OCR 引擎 | RapidOCR / PaddleOCR |
| 目标检测 | YOLO (ONNX Runtime) |
| 图像处理 | OpenCV, NumPy, Pillow |
| 截图 | MSS, DXCam |
| 键鼠模拟 | pynput, pydirectinput |
| 依赖注入 | dependency-injector |
| 配置管理 | OmegaConf (YAML) |
| 包管理 | Poetry |

### 1.3 设计理念

1. **纯图像识别** - 不修改游戏内存，不注入 DLL，通过截图分析实现所有功能
2. **智能决策** - 基于屏幕像素颜色检测技能状态，动态选择最优连招
3. **模块化设计** - 每个角色的连招逻辑独立封装，便于维护和扩展
4. **容错机制** - 多重冗余操作防止因帧率波动或被打断导致的连招失败

## 2. 项目结构

```
WutheringWavesAssistant/
├── main.py                    # 程序入口
├── config.yaml                # 用户配置文件
├── pyproject.toml             # 项目依赖与构建配置
├── WWA.exe                    # Windows 启动器
├── WWA_updater.exe            # 更新器
│
├── src/                       # 源代码根目录
│   ├── __init__.py            # 版本号定义
│   ├── application.py         # 应用启动与组装
│   │
│   ├── config/                # 配置层
│   │   ├── app_config.py      # 应用配置解析
│   │   ├── config.py          # 配置基类
│   │   ├── echo_config.py     # 声骸锁定配置
│   │   ├── gui_config.py      # GUI 配置
│   │   ├── keyboard_mapping_config.py  # 按键映射
│   │   └── logging_config.py  # 日志配置
│   │
│   ├── controller/            # 控制器层
│   │   ├── base_controller.py # 控制器基类
│   │   └── main_controller.py # 主控制器，任务调度
│   │
│   ├── core/                  # 核心业务逻辑
│   │   ├── boss.py            # BOSS 数据定义
│   │   ├── combat/            # 战斗系统 ⭐️
│   │   │   ├── combat_core.py # 战斗核心（BaseResonator, ColorChecker）
│   │   │   ├── combat_system.py # 战斗系统（编队管理、连招调度）
│   │   │   └── resonator/     # 角色连招实现
│   │   │       ├── generic.py      # 通用角色
│   │   │       ├── camellya.py     # 椿
│   │   │       ├── cartethyia.py   # 卡提希娅
│   │   │       ├── changli.py      # 长离
│   │   │       ├── ciaccona.py     # 夏空
│   │   │       ├── encore.py       # 安可
│   │   │       ├── jinhsi.py       # 今汐
│   │   │       ├── lynae.py        # 琳奈
│   │   │       ├── mornye.py       # 莫宁
│   │   │       ├── phoebe.py       # 菲比
│   │   │       ├── phrolova.py     # 弗洛洛
│   │   │       ├── rover.py        # 漂泊者
│   │   │       ├── sanhua.py       # 散华
│   │   │       ├── shorekeeper.py  # 守岸人
│   │   │       └── verina.py       # 维里奈
│   │   │
│   │   ├── contexts.py        # 上下文管理
│   │   ├── environs.py        # 环境变量
│   │   ├── exceptions.py      # 自定义异常
│   │   ├── injector.py        # 依赖注入容器
│   │   ├── interface.py       # 服务接口定义
│   │   ├── languages.py       # 语言支持
│   │   ├── pages.py           # 页面定义
│   │   ├── regions.py         # 区域定义
│   │   └── tasks.py           # 任务定义
│   │
│   ├── service/               # 服务层
│   │   ├── auto_boss_service.py      # BOSS 自动刷取
│   │   ├── auto_pickup_service.py    # 自动拾取
│   │   ├── auto_story_service.py     # 自动剧情
│   │   ├── boss_info_service.py      # BOSS 信息
│   │   ├── control_service.py        # 键鼠控制
│   │   ├── daily_activity_service.py # 日常活动
│   │   ├── echo_lock_service.py      # 声骸锁定
│   │   ├── img_service.py            # 截图服务
│   │   ├── ocr_service.py            # OCR 识别
│   │   ├── od_service.py             # 目标检测
│   │   ├── page_event_service.py     # 页面事件
│   │   └── window_service.py         # 窗口管理
│   │
│   ├── gui/                   # GUI 层
│   │   ├── gui.py             # GUI 启动入口
│   │   ├── common/            # 公共组件
│   │   ├── components/        # UI 组件
│   │   ├── resource/          # 资源文件（图标、图片）
│   │   └── view/              # 页面视图
│   │
│   ├── util/                  # 工具层
│   │   ├── audio_util.py      # 音频工具
│   │   ├── dxcam_util.py      # DXCam 截图
│   │   ├── file_util.py       # 文件工具
│   │   ├── hwnd_util.py       # 窗口句柄
│   │   ├── img_util.py        # 图像处理
│   │   ├── keymouse_util.py   # 键鼠模拟
│   │   ├── mss_util.py        # MSS 截图
│   │   ├── onnx_util.py       # ONNX 推理
│   │   ├── paddleocr_util.py  # PaddleOCR
│   │   ├── rapidocr_util.py   # RapidOCR
│   │   ├── screenshot_util.py # 截图工具
│   │   ├── windows_util.py    # Windows 系统工具
│   │   ├── winreg_util.py     # 注册表
│   │   ├── wrap_util.py       # 装饰器
│   │   └── yolo_util.py       # YOLO 检测
│   │
│   └── c/                     # C 语言扩展
│       ├── launcher/          # 启动器
│       └── updater/           # 更新器
│
├── assets/                    # 资源文件
│   ├── model/                 # YOLO/ONNX 模型
│   ├── screenshot/            # 测试截图
│   ├── static/                # 静态资源
│   └── template/              # 模板
│
├── tests/                     # 测试
│   ├── conftest.py            # 测试配置
│   ├── pytest.ini             # pytest 配置
│   ├── config/                # 配置测试
│   ├── core/                  # 核心逻辑测试
│   ├── service/               # 服务测试
│   └── util/                  # 工具测试
│
├── scripts/                   # 脚本
│   └── rebuild_conda_env.ps1  # Conda 环境重建
│
└── docs/                      # 文档
    ├── README.md              # 文档索引
    ├── ARCH.md                # 系统架构
    ├── CONFIG.md              # 配置说明
    ├── COMBAT_SYSTEM.md       # 战斗系统
    ├── CONTRIBUTING_COMBO.md   # 连招开发指南
    └── resonators/            # 角色连招文档
```

## 3. 架构分层

WWA 采用四层架构设计：

```
┌──────────────────────────────────────┐
│             GUI 层 (PySide6)          │  用户交互、参数配置、日志显示
├──────────────────────────────────────┤
│           Controller 层               │  任务调度、信号绑定、流程控制
├──────────────────────────────────────┤
│            Service 层                 │  截图、OCR、YOLO、键鼠控制
├──────────────────────────────────────┤
│             Core 层                   │  战斗逻辑、BOSS管理、角色连招
└──────────────────────────────────────┘
```

### 3.1 GUI 层

- 基于 PySide6 和 FluentWidgets 构建的现代化界面
- 提供任务启停、参数配置、日志实时显示
- 通过 Qt 信号机制与后端 Controller 通信

### 3.2 Controller 层

- `MainController` 接收 GUI 信号，调度各 Service 执行任务
- 管理任务生命周期（启动、暂停、停止）
- 动态配置切换（配置文件路径）

### 3.3 Service 层

- **ControlService** - 封装键鼠操作（普攻、技能、闪避、跳跃等）
- **ImgService** - 截图服务，获取游戏画面
- **OcrService** - OCR 文字识别（RapidOCR / PaddleOCR）
- **OdService** - YOLO 目标检测（声骸识别）
- **AutoBossService** - BOSS 自动刷取流程控制
- **EchoLockService** - 声骸属性识别与锁定

### 3.4 Core 层

- **CombatSystem** - 战斗系统核心，管理编队、调度角色连招
- **BaseResonator** - 角色基类，定义连招接口和通用方法
- **ColorChecker** - 像素颜色检测器，用于识别技能就绪状态
- 各角色实现类 - 封装特定角色的连招逻辑

## 4. 核心数据流

### 4.1 应用启动流程

```
main.py
  ├─ environs.load_env()          # 加载环境变量
  ├─ logging_config.setup_logging() # 配置日志
  └─ application.run()
       ├─ before()                 # 管理员权限检查
       ├─ MainController()         # 初始化后端
       ├─ 绑定 GUI 信号            # 连接前后端
       └─ wwa()                    # 启动 Qt 主循环
```

### 4.2 战斗流程

```
用户点击开始
  ├─ MainController.execute()
  │    └─ AutoBossService.start()
  │         ├─ 传送至 BOSS 位置
  │         ├─ 等待 BOSS 出现
  │         ├─ CombatSystem.start()
  │         │    └─ CombatSystem.run()        # 战斗主循环
  │         │         ├─ 检查暂停/超时状态
  │         │         ├─ 角色排序（辅助→输出→治疗）
  │         │         ├─ toggle() 切换角色
  │         │         └─ resonator.combo()    # 执行角色连招
  │         │              ├─ 截图检测技能状态
  │         │              ├─ 智能选择连招路线
  │         │              └─ combo_action() 执行动作序列
  │         ├─ 等待战斗结束
  │         ├─ 搜索并拾取声骸
  │         └─ 循环下一个 BOSS
```

### 4.3 智能连招决策流

```
resonator.combo()
  ├─ img_service.screenshot()      # 截取游戏画面
  ├─ ColorChecker.check()          # 检测各技能图标像素颜色
  │    ├─ 共鸣技能 (E) 是否就绪
  │    ├─ 共鸣解放 (R) 是否就绪
  │    ├─ 声骸技能 (Q) 是否就绪
  │    ├─ 能量条检测
  │    └─ 特殊状态检测
  ├─ 基于状态决策连招路线          # if-else 条件分支
  └─ combo_action(action_seq)      # 执行动作序列
       ├─ [按键, 按下时长, 等待时长]
       └─ 循环执行每个动作
```

## 5. 并发模型

### 5.1 线程模型

```
主线程 (Qt GUI)
  │
  ├─ 战斗线程 (CombatSystem._thread)
  │    └─ 循环执行角色连招
  │
  └─ 后台任务线程
       ├─ AutoBossService
       ├─ AutoPickupService
       └─ WindowService (游戏窗口监控)
```

### 5.2 暂停/恢复机制

- 使用 `threading.Event` 控制战斗暂停与恢复
- `event.set()` 恢复战斗，`event.clear()` 暂停战斗
- 支持超时自动暂停（`_delay_time`）
- 角色连招中通过 `StopError` 异常快速跳出连招序列

## 6. 关键技术

### 6.1 像素级技能检测 (ColorChecker)

通过检测屏幕特定坐标点的像素颜色来判断技能是否就绪：

- 技能就绪时图标为白色 `(255, 255, 255)`
- 技能冷却中图标为灰色或其他颜色
- 支持 OR/AND 逻辑组合多个检测点
- 支持颜色容差匹配

### 6.2 分辨率适配 (DynamicPointTransformer)

- 基准分辨率为 1280×720
- 支持 16:9 标准比例等比缩放
- 支持 16:10 / 21:9 等非标准比例的对齐映射
- 自动根据截图尺寸计算坐标变换

### 6.3 连招动作序列

每个动作为三元组 `[按键, 按下时长, 等待时长]`：

- `按键`: `"a"`(普攻), `"E"`(技能), `"R"`(大招), `"Q"`(声骸), `"z"`(重击), `"j"`(跳跃), `"d"`(闪避), `"w"`(前进) 等
- `按下时长`: 按键按下持续时间（秒），用于区分轻按和长按
- `等待时长`: 释放按键后的等待时间（秒），用于等待动画播放

---

*最后更新: 2026-02-06*
