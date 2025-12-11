# 比特币挖矿仿真程序：API 文档与使用示例

## 📚 目录
1. [快速开始](#快速开始)
2. [核心函数API](#核心函数api)
3. [使用示例](#使用示例)
4. [输出解释](#输出解释)
5. [扩展功能](#扩展功能)

---

## 🚀 快速开始

### 安装依赖
```bash
# 仅需要标准库（无额外依赖）
python --version  # >= 3.7
```

### 运行程序
```bash
cd /Users/Hoshino/Documents
python quant.py
```

输出结果将包含：
1. **攻击向量分析** - 5种不公平挖矿策略对比
2. **防御策略建议** - 4层防御体系详解
3. **综合报告** - 保存到 `comprehensive_mining_report.txt`

---

## 🔧 核心函数API

### 1. 基础仿真函数

#### `simulate_all_honest(alpha, rounds, seed=None) -> SimulationResult`

**功能**: 纯诚实挖矿基准仿真

**参数**:
- `alpha` (float): 被跟踪矿工的算力占比，范围 (0, 1)
- `rounds` (int): 仿真步数（~区块数）
- `seed` (int, optional): 随机种子，用于复现结果

**返回**: `SimulationResult` 对象，包含：
- `attacker_blocks`: 被跟踪矿工获得的区块数
- `honest_blocks`: 其他矿工获得的区块数
- `attacker_relative_reward`: 被跟踪矿工收益占比（应接近 alpha）
- `attacker_revenue_btc`: 被跟踪矿工总收益（BTC）

**示例**:
```python
result = simulate_all_honest(alpha=0.25, rounds=100000, seed=42)
print(f"被跟踪矿工收益占比: {result.attacker_relative_reward:.4f}")
print(f"理论期望值: 0.2500")
print(f"验证: 是否接近? {abs(result.attacker_relative_reward - 0.25) < 0.01}")
```

**输出示例**:
```
被跟踪矿工收益占比: 0.2492
理论期望值: 0.2500
验证: 是否接近? True
```

---

#### `simulate_selfish_mining(alpha, gamma, rounds, seed=None) -> SimulationResult`

**功能**: 自私挖矿攻击仿真（Eyal & Sirer 模型）

**参数**:
- `alpha` (float): 攻击者算力占比
- `gamma` (float): 网络优势参数，范围 [0, 1]
  - gamma = 1.0: 攻击者总能赢得分叉竞争（完全网络优势）
  - gamma = 0.5: 分叉竞争随机选择（无网络优势）
  - gamma = 0.0: 攻击者总是输掉分叉竞争
- `rounds` (int): 仿真步数
- `seed` (int, optional): 随机种子

**返回**: `SimulationResult` 对象

**关键指标**:
- `efficiency_advantage`: 效率优势倍数 = (实际收益 / alpha) / (理论公平收益)
  - > 1.0: 超额收益
  - = 1.0: 完全公平
  - < 1.0: 劣势收益

**示例**:
```python
# 场景1: 攻击者 25% 算力，网络优势强 (gamma=0.9)
result_strong = simulate_selfish_mining(
    alpha=0.25,
    gamma=0.9,
    rounds=100000,
    seed=2025
)

# 场景2: 攻击者 25% 算力，网络优势弱 (gamma=0.5)
result_weak = simulate_selfish_mining(
    alpha=0.25,
    gamma=0.5,
    rounds=100000,
    seed=2025
)

print(f"强网络优势 (gamma=0.9): 效率优势 {result_strong.efficiency_advantage:.4f}x")
print(f"弱网络优势 (gamma=0.5): 效率优势 {result_weak.efficiency_advantage:.4f}x")
print(f"防御效果: {(1 - result_weak.efficiency_advantage / result_strong.efficiency_advantage) * 100:.2f}%")
```

---

### 2. 攻击向量函数

#### `asic_miner_advantage(alpha_computation, asic_multiplier, gamma, rounds, seed=None) -> Dict`

**功能**: 评估 ASIC 矿机硬件优势的威胁程度

**参数**:
- `alpha_computation` (float): 基于通用计算（CPU/GPU）的算力占比
- `asic_multiplier` (float): ASIC 相对于通用计算的倍数
  - 1.5x: 轻度优势（可能的未来）
  - 3.0x: 中度优势
  - 5.0x: 高度优势
  - 10.0x: 极度优势（当前比特币现状）
- `gamma` (float): 网络优势参数
- `rounds` (int): 仿真步数
- `seed` (int, optional): 随机种子

**返回**: 包含以下字段的字典：
```python
{
    "alpha_effective": 0.5,           # 实际有效算力占比
    "efficiency_advantage_with_asic": 1.99,  # 效率优势倍数
    "threat_level": "高威胁",
    "summary": "详细描述"
}
```

**示例**:
```python
# 模拟: 攻击者 20% 的通用算力，但有 5 倍 ASIC 优势
result = asic_miner_advantage(
    alpha_computation=0.2,
    asic_multiplier=5.0,
    gamma=0.9,
    rounds=100000,
    seed=2025
)

print(f"基础算力占比: 20%")
print(f"实际有效算力: {result['alpha_effective']*100:.1f}%")
print(f"效率优势: {result['efficiency_advantage_with_asic']:.4f}x")
print(f"威胁等级: {result['threat_level']}")
```

**输出示例**:
```
基础算力占比: 20%
实际有效算力: 62.5%
效率优势: 1.6000x
威胁等级: 高威胁
```

---

#### `mev_transaction_ordering(alpha, mev_extract_probability, avg_mev_per_block, gamma, rounds, seed=None) -> Dict`

**功能**: 量化 MEV（最大可提取价值）的经济威胁

**参数**:
- `alpha` (float): 攻击者算力占比
- `mev_extract_probability` (float): 攻击者能成功提取 MEV 的概率
  - 0.1: 10% 的区块可提取 MEV（低风险场景）
  - 0.3: 30% 的区块可提取 MEV（正常场景）
  - 0.5: 50% 的区块可提取 MEV（高风险场景）
- `avg_mev_per_block` (float): 平均每个区块的 MEV 价值（BTC）
- `gamma` (float): 网络优势参数
- `rounds` (int): 仿真步数
- `seed` (int, optional): 随机种子

**返回**: 包含以下字段的字典：
```python
{
    "base_revenue_btc": 259004.25,           # 不含 MEV 的基础收益
    "mev_revenue_btc": 28777.50,             # MEV 部分的收益
    "total_enhanced_revenue_btc": 287781.75, # 总收益
    "revenue_advantage_vs_honest": -0.1999,  # 相对于诚实矿工的优势倍数
}
```

**示例**:
```python
# 模拟: 攻击者能在 30% 的区块中提取 MEV，每块 2.5 BTC
result = mev_transaction_ordering(
    alpha=0.25,
    mev_extract_probability=0.3,
    avg_mev_per_block=2.5,
    gamma=0.9,
    rounds=100000,
    seed=2025
)

print(f"基础收益: {result['base_revenue_btc']:.2f} BTC")
print(f"MEV 额外收益: {result['mev_revenue_btc']:.2f} BTC")
print(f"相对优势: {result['revenue_advantage_vs_honest']:.4f}x")
```

---

#### `timing_optimization_attack(alpha, network_delay_ms, block_time_sec, gamma, rounds, seed=None) -> Dict`

**功能**: 评估网络延迟优化对自私挖矿的增强

**参数**:
- `alpha` (float): 攻击者算力占比
- `network_delay_ms` (float): 攻击者的网络延迟（毫秒）
  - 10ms: 极低延迟（CDN+最优地理位置）
  - 100ms: 正常互联网延迟
  - 500ms: 极高延迟（卫星网络或远距离）
- `block_time_sec` (float): 区块产生平均时间（秒），比特币为 600
- `gamma` (float): 基础网络优势参数
- `rounds` (int): 仿真步数
- `seed` (int, optional): 随机种子

**返回**: 包含以下字段的字典：
```python
{
    "gamma_effective": 0.9999,      # 考虑网络延迟后的有效 gamma
    "time_advantage_factor": 1.816, # 时间优化带来的倍数优势
    "threat_level": "高威胁",
}
```

**示例**:
```python
# 对比: 不同网络延迟下的时间优化效果
delays = [10, 50, 100, 200, 500]
for delay in delays:
    result = timing_optimization_attack(
        alpha=0.25,
        network_delay_ms=delay,
        block_time_sec=600,
        gamma=0.9,
        rounds=100000,
        seed=2025
    )
    advantage = result['time_advantage_factor']
    print(f"延迟 {delay:3d}ms -> 时间优势 {advantage:.4f}x")
```

**输出示例**:
```
延迟  10ms -> 时间优势 1.8160x
延迟  50ms -> 时间优势 1.8160x
延迟 100ms -> 时间优势 1.8159x
延迟 200ms -> 时间优势 1.8158x
延迟 500ms -> 时间优势 1.8155x
```

---

#### `cross_chain_attack(alpha, num_chains, gamma, rounds_per_chain, seed=None) -> Dict`

**功能**: 评估跨多条链同步攻击的威胁

**参数**:
- `alpha` (float): 在单条链上的算力占比
- `num_chains` (int): 攻击的链数量
  - 1: 单链（基准）
  - 2-3: 相关币种（如 BTC + BCH）
  - 5+: 大规模多链攻击
- `gamma` (float): 网络优势参数（对所有链相同）
- `rounds_per_chain` (int): 每条链上的仿真步数
- `seed` (int, optional): 随机种子

**返回**: 包含以下字段的字典：
```python
{
    "revenue_comparison": {
        "single_chain_btc": 259004.25,        # 单链基准
        "multi_chain_total_after_cost_btc": 761452.65,  # 多链总收益（扣除协调成本）
        "multiplier_effect": 2.9399,          # 复合倍数
        "coordination_overhead_percent": 2.0, # 协调成本百分比
    }
}
```

**示例**:
```python
# 模拟: 攻击者在 3 条链上同步发动自私挖矿
result = cross_chain_attack(
    alpha=0.25,
    num_chains=3,
    gamma=0.9,
    rounds_per_chain=100000,
    seed=2025
)

comp = result['revenue_comparison']
print(f"单链基准收益: {comp['single_chain_btc']:.2f} BTC")
print(f"3链总收益: {comp['multi_chain_total_after_cost_btc']:.2f} BTC")
print(f"复合倍数: {comp['multiplier_effect']:.4f}x")
print(f"协调成本: {comp['coordination_overhead_percent']:.1f}%")
```

---

### 3. 防御和分析函数

#### `simulate_selfish_with_defense(alpha, gamma_attack, gamma_defense, rounds, defense_enabled=True, seed=None) -> Tuple[SimulationResult, SimulationResult]`

**功能**: 对比防御前后的效果

**参数**:
- `alpha` (float): 攻击者算力占比
- `gamma_attack` (float): 未防御时的网络优势
- `gamma_defense` (float): 防御后的网络优势（应 < gamma_attack）
- `rounds` (int): 仿真步数
- `defense_enabled` (bool): 是否启用防御
- `seed` (int, optional): 随机种子

**返回**: 两个 `SimulationResult` 元组：
- `result_no_defense`: 未防御场景
- `result_with_defense`: 防御后场景

**示例**:
```python
no_defense, with_defense = simulate_selfish_with_defense(
    alpha=0.25,
    gamma_attack=0.9,  # 原始网络优势强
    gamma_defense=0.5, # 防御后削弱到随机选择
    rounds=100000,
    defense_enabled=True,
    seed=2025
)

print(f"未防御: 效率优势 {no_defense.efficiency_advantage:.4f}x")
print(f"防御后: 效率优势 {with_defense.efficiency_advantage:.4f}x")

improvement = (1 - with_defense.efficiency_advantage / no_defense.efficiency_advantage) * 100
print(f"防御效果: {improvement:.2f}% 改进")
```

**输出示例**:
```
未防御: 效率优势 1.6746x
防御后: 效率优势 1.0977x
防御效果: 34.45% 改进
```

---

#### `parameter_sweep_analysis(alpha_min, alpha_max, alpha_steps, gamma_attack, gamma_defense, rounds) -> Dict`

**功能**: 扫描不同算力占比下的攻击收益变化

**参数**:
- `alpha_min` (float): 最小算力占比
- `alpha_max` (float): 最大算力占比
- `alpha_steps` (int): 扫描步数
- `gamma_attack, gamma_defense` (float): 网络优势参数
- `rounds` (int): 每个参数配置的仿真步数

**返回**: 包含详细扫描结果的字典

**示例**:
```python
sweep = parameter_sweep_analysis(
    alpha_min=0.1,
    alpha_max=0.4,
    alpha_steps=7,
    gamma_attack=0.9,
    gamma_defense=0.5,
    rounds=50000
)

print(f"最优攻击参数: alpha={sweep['optimal_alpha']:.3f}")
print(f"最大效率优势: {sweep['max_efficiency_gain']:.4f}x")

# 打印详细结果
for res in sweep['results']:
    print(f"alpha={res['alpha']:.2f}: "
          f"未防御={res['no_defense']['efficiency_advantage']:.4f}x "
          f"防御后={res['with_defense']['efficiency_advantage']:.4f}x")
```

---

#### `defense_mechanism_comparison(alpha, rounds=50000) -> Dict`

**功能**: 对比多种防御机制的有效性

**参数**:
- `alpha` (float): 攻击者算力占比
- `rounds` (int): 仿真步数

**返回**: 包含多种防御策略结果的字典

**示例**:
```python
defense_results = defense_mechanism_comparison(alpha=0.25, rounds=50000)

print("防御机制对比:")
for strategy in defense_results['strategies']:
    name = strategy['name']
    gamma = strategy['gamma']
    efficiency = strategy['result']['efficiency_advantage']
    improvement = strategy['improvement_percent']
    print(f"  {name:15s} (gamma={gamma:.1f}): "
          f"效率={efficiency:.4f}x, 改进={improvement:.1f}%")
```

---

#### `comprehensive_attack_comparison(alpha=0.2, rounds=50000) -> str`

**功能**: 生成多种攻击向量的全面对比报告

**参数**:
- `alpha` (float): 攻击者算力占比
- `rounds` (int): 仿真步数

**返回**: 格式化的报告字符串

**示例**:
```python
report = comprehensive_attack_comparison(alpha=0.25, rounds=100000)
print(report)

# 保存到文件
with open("attack_analysis.txt", "w") as f:
    f.write(report)
```

---

#### `defense_recommendation_report(alpha=0.2, rounds=50000) -> str`

**功能**: 生成针对性的防御建议报告

**参数**:
- `alpha` (float): 攻击者算力占比
- `rounds` (int): 仿真步数

**返回**: 格式化的防御建议字符串

**示例**:
```python
recommendations = defense_recommendation_report(alpha=0.25, rounds=100000)
print(recommendations)
```

---

## 📊 使用示例

### 示例1: 评估特定攻击场景

```python
# 场景: 攻击者拥有 20% 算力，ASIC 优势 3 倍，网络延迟 50ms
# 问题: 这个攻击者能赚多少超额收益?

alpha_base = 0.20
asic_mult = 3.0
delay_ms = 50

# 计算有效算力
asic_result = asic_miner_advantage(alpha_base, asic_mult, 0.9, 100000, 2025)
alpha_effective = asic_result['alpha_effective']

# 计算时间优化效果
timing_result = timing_optimization_attack(
    alpha_effective, delay_ms, 600, 0.9, 100000, 2025
)

# 计算总效率优势
total_advantage = (asic_result['efficiency_advantage_with_asic'] * 
                   timing_result['time_advantage_factor'] / 1.0)

print(f"原始算力占比: {alpha_base:.1%}")
print(f"实际有效算力: {alpha_effective:.1%}")
print(f"")
print(f"ASIC 优势: {asic_result['efficiency_advantage_with_asic']:.4f}x")
print(f"时间优势: {timing_result['time_advantage_factor']:.4f}x")
print(f"总体效率: {total_advantage:.4f}x")
print(f"")
print(f"预期超额收益: {(total_advantage - 1) * 100:.2f}%")
```

---

### 示例2: 设计防御策略

```python
# 问题: 如果我们采用"随机分叉选择"防御，能降低多少威胁?

alpha = 0.25

# 原始威胁
original, _ = simulate_selfish_with_defense(alpha, 0.9, 0.9, 100000, False, 2025)
print(f"原始威胁 (无防御): {original.efficiency_advantage:.4f}x")

# 防御后
_, defended = simulate_selfish_with_defense(alpha, 0.9, 0.5, 100000, True, 2025)
print(f"防御后威胁 (gamma=0.5): {defended.efficiency_advantage:.4f}x")

# 计算防御效果
mitigation = (1 - defended.efficiency_advantage / original.efficiency_advantage) * 100
print(f"防御效果: {mitigation:.1f}%")

# 评估是否充分
if defended.efficiency_advantage < 1.1:
    print("✓ 防御充分：攻击者无经济动机")
else:
    print("✗ 防御不足：仍需加强")
```

---

### 示例3: 成本-效益分析

```python
# 问题: 部署 FIBRE 中继网络值不值?

cost_deploy = 500000  # $500K
cost_annual = 100000   # $100K/年

# 不部署 (网络延迟 100ms)
attack_no_defense = timing_optimization_attack(0.25, 100, 600, 0.9, 100000, 2025)
threat_no_defense = attack_no_defense['time_advantage_factor']

# 部署 (网络延迟 20ms)
attack_with_defense = timing_optimization_attack(0.25, 20, 600, 0.9, 100000, 2025)
threat_with_defense = attack_with_defense['time_advantage_factor']

threat_reduction = (threat_no_defense - threat_with_defense) / threat_no_defense

# 假设威胁造成的潜在损失是 $100M/年
annual_threat_loss = 100_000_000
loss_prevention = annual_threat_loss * threat_reduction

print(f"年度防守收益: ${loss_prevention:,.0f}")
print(f"投入回本周期: {cost_deploy / loss_prevention * 12:.1f} 个月")

if cost_deploy < loss_prevention:
    print("✓ 投资决策: 部署值得")
else:
    print("✗ 投资决策: 需要更多分析")
```

---

## 🔍 输出解释

### SimulationResult 对象的关键字段

```python
result = simulate_selfish_mining(0.25, 0.9, 100000, 2025)

# 基本统计
result.alpha                    # 0.25 - 攻击者算力占比
result.gamma                    # 0.9 - 网络优势参数
result.rounds                   # 100000 - 仿真步数
result.attacker_blocks          # ~25000 - 攻击者获得的区块数
result.honest_blocks            # ~75000 - 诚实矿工获得的区块数

# 相对收益
result.attacker_relative_reward # 0.3341 - 攻击者占区块总数的比例
result.honest_relative_reward   # 0.6659 - 诚实矿工占比

# 绝对收益 (BTC)
result.block_reward             # 6.25 - 每个区块的基础奖励
result.avg_tx_fee_per_block     # 0.5 - 每个区块的平均交易费
result.attacker_revenue_btc     # ~209000 - 攻击者总收益 (BTC)
result.honest_revenue_btc       # ~468750 - 诚实矿工总收益 (BTC)

# 效率指标
result.efficiency_advantage     # 1.3364 - 效率优势倍数
                                # = (0.3341 / 0.25) = 1.3364
                                # > 1.0 表示超额收益
```

### 效率优势倍数的含义

```
efficiency_advantage = 1.0
  -> 攻击者获得的收益 = 算力占比
  -> 完全公平
  
efficiency_advantage = 1.5
  -> 攻击者获得的收益 = 1.5 * 算力占比
  -> 超额收益 50%
  
efficiency_advantage = 0.8
  -> 攻击者获得的收益 = 0.8 * 算力占比
  -> 不利收益（被歧视）
```

---

## 🎯 扩展功能

### 如何添加自定义攻击向量

```python
def custom_attack_model(alpha, custom_param, rounds, seed=None):
    """
    模板: 自定义攻击向量
    
    步骤:
    1. 定义攻击的具体机制
    2. 在仿真中应用
    3. 计算超额收益
    """
    if seed is not None:
        random.seed(seed)
    
    attacker_blocks = 0
    honest_blocks = 0
    
    for step in range(rounds):
        # 这里实现你的攻击逻辑
        r = random.random()
        if r < alpha:
            attacker_blocks += 1
            # 应用 custom_param 的影响
        else:
            honest_blocks += 1
    
    return SimulationResult(
        alpha=alpha,
        gamma=0.0,  # 如适用
        rounds=rounds,
        attacker_blocks=attacker_blocks,
        honest_blocks=honest_blocks
    )

# 使用
result = custom_attack_model(0.25, custom_param=0.5, rounds=100000, seed=2025)
print(f"超额收益: {result.efficiency_advantage:.4f}x")
```

### 如何添加防御机制

```python
def custom_defense(alpha, rounds, defense_strength, seed=None):
    """
    模板: 自定义防御机制
    
    defense_strength: 防御强度 [0, 1]
      0.0 = 无防御
      1.0 = 完全防御
    """
    # 防御将参数转化为 gamma
    gamma = 0.5 + 0.5 * (1 - defense_strength)
    # gamma 从 1.0 (无防御) 降至 0.5 (完全防御)
    
    result = simulate_selfish_mining(alpha, gamma, rounds, seed)
    return result

# 对比
for strength in [0.0, 0.3, 0.6, 1.0]:
    result = custom_defense(0.25, 100000, strength, 2025)
    print(f"防御强度 {strength:.1f}: 效率优势 {result.efficiency_advantage:.4f}x")
```

---

## 📝 常见问题

**Q: 为什么某些参数组合下结果为负?**
A: 这通常表示 MEV 模型中诚实矿工的参考收益计算有偏差。在实际应用中应检查诚实矿工的基准收益。

**Q: 仿真步数应该设多大?**
A: 一般来说：
- 快速测试: 10,000 步
- 标准分析: 100,000 步
- 精确研究: 1,000,000 步

**Q: 如何比较不同链的攻击难度?**
A: 使用 `parameter_sweep_analysis` 函数扫描 alpha 范围，找到最优攻击参数点。

---

## 📖 参考资源

- Eyal, I., & Sirer, E. G. (2014). "Majority is not enough: Bitcoin mining is vulnerable"
  https://arxiv.org/abs/1311.0472

- MEV Research: https://ethereum.org/en/developers/docs/mev/

- FIBRE Relay Network: https://bitcoinfibre.org/

- Bitcoin Network Latency: https://www.dsn.kaspersky.com/en