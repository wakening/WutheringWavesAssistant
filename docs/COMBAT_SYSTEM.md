# 战斗系统总览

## 1. 概述

WWA 的战斗系统（Combat System）是核心模块，负责在自动刷 BOSS 过程中控制角色执行连招。系统通过截图分析游戏画面中的技能图标颜色，实时判断技能状态，动态选择最优连招路线。

## 2. 核心类

### 2.1 CombatSystem (`combat_system.py`)

战斗系统的总调度器，职责包括：

- **编队管理** - 根据角色中文名映射到对应的 Resonator 实例
- **角色排序** - 按 Support → DPS → Healer 优先级排序出战顺序
- **战斗循环** - 在 `run()` 方法中循环切人并执行连招
- **暂停/恢复** - 通过 `threading.Event` 控制战斗状态

```python
class CombatSystem:
    def set_resonators(resonator_names_zh: list[str])  # 设置编队
    def run(event: threading.Event)                     # 战斗主循环
    def start(delay_seconds: float)                     # 启动战斗
    def pause()                                         # 暂停战斗
```

**角色映射表 (`resonator_map`)**：

已注册定制连招的角色：

| 枚举名 | 中文名 | 连招类 |
|--------|--------|--------|
| jinhsi | 今汐 | Jinhsi |
| changli | 长离 | Changli |
| shorekeeper | 守岸人 | Shorekeeper |
| encore | 安可 | Encore |
| verina | 维里奈 | Verina |
| camellya | 椿 | Camellya |
| sanhua | 散华 | Sanhua |
| cartethyia | 卡提希娅 | Cartethyia |
| ciaccona | 夏空 | Ciaccona |
| phrolova | 弗洛洛 | Phrolova |
| lynae | 琳奈 | Lynae |

> **注意**：Phoebe（菲比）和 Mornye（莫宁）虽有类定义但尚未注册到 `resonator_map`。菲比的 `combo()` 方法为空实现（`pass`），莫宁的 `energy_count()` 已在 v3.1.0 中修复实现。

未注册定制连招的角色将使用 `GenericResonator` 通用连招。

### 2.2 BaseResonator (`combat_core.py`)

所有角色的基类，定义核心接口：

```python
class BaseResonator:
    def resonator_name() -> ResonatorNameEnum  # 角色标识
    def char_class() -> list[CharClassEnum]     # 角色定位
    def combo()                                 # 连招主逻辑 (子类必须实现)
    def combo_action(seq, is_interruptible)     # 执行动作序列
    def boss_hp(img) -> float                   # BOSS 血量检测
```

**角色定位枚举 (`CharClassEnum`)**：

| 枚举值 | 含义 | 出战优先级 |
|--------|------|----------|
| `MainDPS` | 主输出 | 2 |
| `SubDPS` | 副输出 | 2 |
| `Support` | 辅助 | 1 (最先) |
| `Healer` | 治疗 | 3 (最后) |

### 2.3 ColorChecker (`combat_core.py`)

像素颜色检测器，战斗系统的"眼睛"：

```python
class ColorChecker:
    def __init__(points, colors, tolerance=30, logic=LogicEnum.OR)
    def check(img: np.ndarray) -> bool
```

**参数说明**：
- `points` - 屏幕坐标点列表（基于 1280×720 分辨率）
- `colors` - 目标颜色列表（BGR 格式）
- `tolerance` - 颜色容差，默认 30
- `logic` - 多点匹配逻辑：
  - `OR` - 任一点匹配即返回 True（默认，适用于简单的就绪/冷却判断）
  - `AND` - 所有点都匹配才返回 True（适用于有多种状态变化的技能）

**预设协奏能量检测器**：

```python
ColorChecker.concerto_fusion()    # 红圈 - 熔融属性
ColorChecker.concerto_spectro()   # 黄圈 - 衍射属性
ColorChecker.concerto_glacio()    # 蓝圈 - 冷凝属性
ColorChecker.concerto_aero()      # 绿圈 - 气动属性
ColorChecker.concerto_havoc()     # 紫圈 - 湮灭属性
```

## 3. 连招执行引擎

### 3.1 动作序列格式

每个动作为三元组 `[key, press_duration, wait_duration]`：

```python
["a", 0.05, 0.30]  # 普攻：按下0.05秒，等待0.30秒
["E", 0.05, 1.25]  # E技能：按下0.05秒，等待1.25秒
["z", 3.50, 0.41]  # 重击：长按3.50秒，等待0.41秒
["R", 0.05, 2.63]  # 大招：按下0.05秒，等待2.63秒
```

### 3.2 按键映射

| 键值 | 游戏操作 | 说明 |
|------|----------|------|
| `a` | 鼠标左键 | 普攻 |
| `z` | 鼠标左键(长按) | 重击（按下时长>0.5秒） |
| `E` | 技能键 | 共鸣技能 |
| `R` | 大招键 | 共鸣解放 |
| `Q` | 声骸键 | 声骸技能 |
| `j` | 空格 | 跳跃 |
| `d` | 闪避键 | 闪避 |
| `w` | 前进键 | 前进（常用于等待间隔） |
| `G` | 瞄准键 | 枪系角色瞄准 |
| `A` | 鼠标左键(特殊) | 特殊普攻 |
| `W_down` / `W_up` | W键按下/松开 | 持续前进控制 |

### 3.3 连招拆分策略

为应对实战中帧率波动和被打断的情况，连招序列采用"拆分"策略：

```python
# 原始时间轴（训练场精确值）
["a", 0.05, 0.90]  # 第三段普攻等待0.90秒

# 拆分后（实战版本）
["a", 0.05, 0.30],  # 拆成多段，每段更短
["a", 0.05, 0.30],  # 中间穿插额外输入
["a", 0.05, 0.30],  # 提高容错性
```

**拆分的好处**：
- 被打断后能更快恢复
- 减少长时间"发呆"的风险
- 多余的按键输入会被游戏自动忽略

## 4. 战斗循环详解

### 4.1 角色排序规则

```python
def _sort_resonators(resonators):
    # 排序优先级: Support > DPS > Healer > None
    sorted = support + dps + healer + none
```

辅助角色先出手放 Buff，然后输出角色打伤害，最后治疗角色恢复血量。

### 4.2 切人逻辑

```
while True:
    1. 检查暂停状态
    2. 获取下一个角色
    3. 尝试切人 (toggle)
       ├─ 成功 → 执行连招
       ├─ 失败（大招期间无法切人）→ 跳到下一个
       └─ None（角色为空）→ 跳到下一个
    4. 防止同一角色连续站场两次
    5. 执行 resonator.combo()
    6. 释放鼠标按键（安全清理）
```

### 4.3 move_prepare 机制

在战斗结束后移动前，需要处理特殊角色状态：

- **椿 (Camellya)** - 调用 `quit_blossom()` 退出盛绽状态，可能需要后闪复位
- **弗洛洛 (Phrolova)** - 调用 `quit_R()` 退出大招状态

## 5. 角色连招设计模式

每个定制连招角色都遵循以下设计模式：

### 5.1 Base 类 + 实现类

```python
class BaseXxx(BaseResonator):
    """定义技能状态检测方法"""
    def is_resonance_skill_ready(img) -> bool
    def is_echo_skill_ready(img) -> bool
    def is_resonance_liberation_ready(img) -> bool

class Xxx(BaseXxx):
    """定义连招片段和决策逻辑"""
    COMBO_SEQ = [...]           # 训练场完整连段（参考用）
    def a4(): return [...]       # 连招片段：4段普攻
    def E(): return [...]        # 连招片段：E技能
    def combo():                 # 连招决策主逻辑
        img = screenshot()
        if is_R_ready: ...
        elif is_E_ready: ...
        else: 兜底普攻
```

### 5.2 决策优先级

大多数角色遵循的决策优先级：

1. **共鸣解放 (R)** - 最高优先，有大开大
2. **特殊状态处理** - 如椿的一日花、安可的暴走状态
3. **共鸣技能 (E)** - 核心技能循环
4. **声骸技能 (Q)** - 通常最后释放用于合轴
5. **普攻连段** - 兜底选项

### 5.3 COMBO_SEQ 约定

每个角色类中的 `COMBO_SEQ` 为训练场单人静态完整连段，用于开发参考。实战中的 `combo()` 方法会根据技能状态动态选择连招片段。

---

*最后更新: 2026-02-06*
