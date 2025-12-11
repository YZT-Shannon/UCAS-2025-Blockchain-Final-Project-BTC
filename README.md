# UCAS-2025-Blockchain-Final-Project-BTC
---

本仓库包含一个用于研究 **比特币挖矿中的不公平策略（Selfish Mining、MEV、ASIC集中化、跨链攻击等）** 及 **多层防御机制** 的完整仿真平台。

---

## 目录

* [项目结构总览](#项目结构总览)
* [快速开始](#快速开始)
* [文件导航地图](#文件导航地图)
* [包含的攻击模型](#包含的攻击模型)
* [包含的防御模型](#包含的防御模型)
* [核心功能示例](#核心功能示例)
* [许可证](#许可证)

---

## 项目结构总览

```
bitcoin-mining-research/
│
├─ quant.py                      # 主仿真程序（核心代码）
├─ quickstart.md                 # 快速入门指南
├─ SUMMARY.md                    # 项目核心发现总结
├─ advanced_defense_strategies.md# 防御体系完整设计
├─ improvement_analysis.md       # 可改进方向分析
├─ api_documentation.md          # 模块 API 文档
├─ comprehensive_mining_report.txt # 自动生成的详细报告
└─ README.md                     # 当前文档
```

---

## 快速开始

### 运行仿真

```bash
python quant.py
```

运行后将自动生成：

```
comprehensive_mining_report.txt
```

其中包含：

* 自私挖矿与防御机制对比
* ASIC 优势分析
* MEV 收益影响
* 网络延迟攻击效果
* 跨链攻击分析

---

## 文件导航地图

```
📁 bitcoin-mining-research/
│
├─ 🚀 quickstart.md           
│
├─ 💻 quant.py                → 仿真引擎（核心代码）
│     ├─ simulate_selfish_mining()
│     ├─ asic_miner_advantage()
│     ├─ mev_transaction_ordering()
│     ├─ timing_optimization_attack()
│     └─ cross_chain_attack()
│
├─ 📊 分析报告
│     └─ comprehensive_mining_report.txt
│
├─ 📖 核心文档
│     ├─ SUMMARY.md
│     ├─ advanced_defense_strategies.md
│     └─ improvement_analysis.md
│
└─ 📘 API 文档
      └─ api_documentation.md
```

---

## 包含的攻击模型

本项目实现了五类主要攻击向量，每种都有可量化的模拟环境。

### 1. 自私挖矿（Selfish Mining）

* 经典 SM 模型（Eyal & Sirer）
* 支持 γ（传播优势）参数
* 支持私链发布策略

### 2. ASIC 矿机优势模型

* 计算 ASIC 相对 GPU/CPU 的算力倍增
* 计算实际算力占比 α_eff
* 分析收益倍数与威胁等级

### 3. MEV 排序攻击

* 模拟矿工的 MEV 可提取性
* 复合收益：区块奖励 + 手续费 + MEV

### 4. 网络延迟攻击（Time Optimization）

* 基于传播延迟计算 γ_eff
* 分析 CDN/地理优化对挖矿收益的增强作用

### 5. 跨链攻击（Cross-Chain）

* 支持 N 条链同步攻击
* 计算协调开销、收益倍数与扩展影响

---

## 包含的防御模型

本项目构建了一个 4 层的整体防御体系：

### 第一层：网络层

* 改进中继网络（如 FIBRE）
* 降低区块传播延迟
* 提升拓扑鲁棒性

### 第二层：协议层

* γ 抑制机制（随机分叉选择）
* 难度调整机制优化

### 第三层：经济层

* 手续费市场优化
* 降低 MEV 可提取空间

### 第四层：应用层

* 公平交易排序（FTO）
* 跨链验证机制

所有防御方法均附带量化效果。

---

## 核心功能示例

### 1. 评估自私挖矿的收益

```python
from quant import simulate_selfish_mining
result = simulate_selfish_mining(alpha=0.25, gamma=0.9, rounds=100000)
print(result.attacker_relative_reward)
```

### 2. 对比防御前后收益

```python
no_def, with_def = simulate_selfish_with_defense(0.25, 0.9, 0.5, 100000)
print(with_def.efficiency_advantage)
```

### 3. 参数扫描分析

```python
sweep = parameter_sweep_analysis(0.1, 0.4, 7)
print(sweep["optimal_alpha"])
```

## 许可证

本项目可在 MIT 协议下自由使用、修改和分发。

---
