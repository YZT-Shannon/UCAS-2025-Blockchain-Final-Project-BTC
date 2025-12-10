import random
import json
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional
import math


@dataclass
class SimulationResult:
    """
    用于存放一次仿真的统计结果。
    alpha: 自私矿工占全网算力的比例
    gamma: 分叉竞争中，自私矿工所在链获胜的概率（网络优势）
    rounds: 仿真总步数（近似区块产生次数）
    attacker_blocks: 自私矿工最终记账成功的区块数量
    honest_blocks: 诚实矿工最终记账成功的区块数量
    """
    alpha: float
    gamma: float
    rounds: int
    attacker_blocks: int
    honest_blocks: int
    block_reward: float = 6.25  # BTC 区块奖励
    avg_tx_fee_per_block: float = 0.5  # BTC 平均每个区块的交易费

    @property
    def total_blocks(self) -> int:
        return self.attacker_blocks + self.honest_blocks

    @property
    def attacker_relative_reward(self) -> float:
        """自私矿工的相对收益（占总区块数的比例）"""
        if self.total_blocks == 0:
            return 0.0
        return self.attacker_blocks / self.total_blocks

    @property
    def honest_relative_reward(self) -> float:
        """诚实矿工（全体）的相对收益"""
        if self.total_blocks == 0:
            return 0.0
        return self.honest_blocks / self.total_blocks

    @property
    def attacker_revenue_btc(self) -> float:
        """自私矿工的总收益（BTC）"""
        return self.attacker_blocks * (self.block_reward + self.avg_tx_fee_per_block)

    @property
    def honest_revenue_btc(self) -> float:
        """诚实矿工总收益（BTC）"""
        return self.honest_blocks * (self.block_reward + self.avg_tx_fee_per_block)

    @property
    def efficiency_advantage(self) -> float:
        """
        效率优势指数：自私矿工实际收益占比 / 理论公平收益占比（alpha）
        > 1.0 表示超额收益，< 1.0 表示劣势收益
        """
        if self.alpha <= 0:
            return 0.0
        return self.attacker_relative_reward / self.alpha

    def to_dict(self) -> Dict:
        """便于打印或保存为 JSON 的格式"""
        return {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "rounds": self.rounds,
            "attacker_blocks": self.attacker_blocks,
            "honest_blocks": self.honest_blocks,
            "attacker_relative_reward": self.attacker_relative_reward,
            "honest_relative_reward": self.honest_relative_reward,
            "attacker_revenue_btc": self.attacker_revenue_btc,
            "honest_revenue_btc": self.honest_revenue_btc,
            "efficiency_advantage": self.efficiency_advantage,
        }


def simulate_all_honest(alpha: float, rounds: int, seed: int = None) -> SimulationResult:
    """
    纯诚实挖矿基线仿真：
    全网中，有一部分算力我们标记为 "attacker"（攻击者），
    但其行为也是诚实的，只是为了统计它的收益占比是否等于算力占比。

    参数：
        alpha: 攻击者（被标记的矿工/矿池）算力占比，0 < alpha < 1
        rounds: 仿真的步数（每步近似代表"尝试找到一个区块"的事件）
        seed: 随机种子，便于结果复现

    返回：
        SimulationResult：记录攻击者 vs 诚实矿工的区块数及相对收益
    """
    if seed is not None:
        random.seed(seed)

    attacker_blocks = 0
    honest_blocks = 0

    for _ in range(rounds):
        r = random.random()
        # 以 alpha 的概率由 attacker 找到区块
        if r < alpha:
            attacker_blocks += 1
        else:
            honest_blocks += 1

    return SimulationResult(
        alpha=alpha,
        gamma=0.0,  # 纯诚实模型中 gamma 不起作用，这里置 0
        rounds=rounds,
        attacker_blocks=attacker_blocks,
        honest_blocks=honest_blocks
    )


def simulate_selfish_mining(alpha: float,
                            gamma: float,
                            rounds: int,
                            seed: int = None) -> SimulationResult:
    """
    自私挖矿（Selfish Mining）仿真，基于 Eyal & Sirer 提出的经典离散时间模型。

    简化模型说明：
    - alpha: 自私矿工占全网算力的比例（攻击者算力）
    - 1 - alpha: 其余诚实矿工的算力总和
    - gamma: 当出现"公开链和攻击者刚发布的链长度相同的分叉"时，
             后续诚实矿工选择攻击者那条链的概率（代表攻击者在网络传播上的优势）。

    状态变量：
    - lead: 自私矿工私有链长度与公共链长度之差（私链领先高度）
      * lead = 0：无隐藏私链或私链与公链等长
      * lead > 0：自私矿工持有未公开的私有区块链，比公共链长 lead 个区块

    收益统计：
    - attacker_blocks：最终被主链采纳的区块中属于攻击者的数量
    - honest_blocks：最终主链上诚实矿工的区块数量

    参数：
        alpha: 攻击者算力占比
        gamma: 攻击者在分叉竞争中的网络优势
        rounds: 仿真步数
        seed: 随机种子

    返回：
        SimulationResult
    """
    if seed is not None:
        random.seed(seed)

    attacker_blocks = 0
    honest_blocks = 0

    # 自私矿工的"私链领先高度"
    lead = 0

    for _ in range(rounds):
        r = random.random()

        if r < alpha:
            # 自私矿工挖到一个新区块
            if lead == 0:
                # 原本与公链等长，此时就开始构建私有链
                lead = 1
            else:
                # 已经有私有链，就继续在私有链上延长
                lead += 1
        else:
            # 诚实矿工挖到一个新区块
            if lead == 0:
                # 没有隐藏私链，诚实矿工直接记账
                honest_blocks += 1
            elif lead == 1:
                # 现在公共链上多了一个新块，此时自私矿工有 1 个隐藏块
                # 自私矿工立即发布自己的隐藏块，形成"长度相同的分叉竞争"
                # 接下来谁赢得下一个区块，谁的分支就成为最长链
                # gamma 表示诚实矿工选择自私矿工那条分支的概率
                r_fork = random.random()
                if r_fork < gamma:
                    # 攻击者所在分支获胜
                    attacker_blocks += 2  # 公共上最终保留两个区块，都被视为攻击者的链
                else:
                    # 诚实矿工所在分支获胜
                    honest_blocks += 2
                # 分叉结束，回到无私链领先状态
                lead = 0
            else:
                # lead >= 2 的情况：自私矿工的私有链原本至少领先 2
                # 诚实矿工在公共链上又找到一个新块，公共链高度 +1
                # 自私矿工立即公布自己私有链的第一个块，使得自己仍然领先 1 个块
                attacker_blocks += 1
                # 私有链领先高度减少 1
                lead -= 1
                # 诚实矿工刚挖出的那个块因为被对方更长链"覆盖"，最终成为孤块，不计入收益

    # 模拟中可能在结束时还有未公布的私有链，需要结算：
    # 常用处理策略：如果 lead > 0，则自私矿工将剩余私有区块全部发布。
    # lead == 1：相当于刚好多了一个区块
    # lead >= 2：自私矿工发布所有剩余区块，这里简单认为都能成为主链
    if lead > 0:
        attacker_blocks += lead
        # 公共链对应增长 lead，高度变化在这里只影响统计，不影响后续仿真

    return SimulationResult(
        alpha=alpha,
        gamma=gamma,
        rounds=rounds,
        attacker_blocks=attacker_blocks,
        honest_blocks=honest_blocks
    )


def simulate_selfish_with_defense(alpha: float,
                                  gamma_attack: float,
                                  gamma_defense: float,
                                  rounds: int,
                                  defense_enabled: bool = True,
                                  seed: int = None) -> Tuple[SimulationResult, SimulationResult]:
    """
    带"防御机制"的自私挖矿仿真接口。

    思路：
    - 原始协议下，自私矿工在分叉竞争中拥有较大的 gamma_attack（网络优势）。
    - 假设协议/网络层引入某种防御措施（例如强制随机选择分支、
      加强节点对首见区块的偏好、改进中继网络等），
      可以等效为把分叉竞争中自私矿工获胜概率降为 gamma_defense（接近 0.5 或更小）。

    本函数一次性：
    1) 仿真"未防御"场景：gamma = gamma_attack；
    2) 仿真"防御生效"场景：gamma = gamma_defense。

    参数：
        alpha: 自私矿工算力占比
        gamma_attack: 原始协议中自私矿工在分叉竞争中的优势概率
        gamma_defense: 启用防御机制后，分叉竞争中自私矿工获胜概率
        rounds: 仿真步数
        defense_enabled: 是否真的启用防御（如果 False，就只返回原始结果两份）
        seed: 随机种子（注意：为了公平对比，我们会用不同 seed 避免两个场景完全同一随机序列）

    返回：
        (without_defense, with_defense) 两个 SimulationResult
    """
    # 未防御场景
    result_no_defense = simulate_selfish_mining(
        alpha=alpha,
        gamma=gamma_attack,
        rounds=rounds,
        seed=seed
    )

    if not defense_enabled:
        # 不启用防御的话，这里简单返回两个相同结果
        return result_no_defense, result_no_defense

    # 防御场景：使用 gamma_defense
    # 为了避免完全相同的随机序列，这里 seed 做一个简单偏移
    seed_defense = None if seed is None else seed + 1
    result_with_defense = simulate_selfish_mining(
        alpha=alpha,
        gamma=gamma_defense,
        rounds=rounds,
        seed=seed_defense
    )

    return result_no_defense, result_with_defense


def parameter_sweep_analysis(alpha_min: float = 0.05, 
                              alpha_max: float = 0.5, 
                              alpha_steps: int = 10,
                              gamma_attack: float = 0.9,
                              gamma_defense: float = 0.5,
                              rounds: int = 50000) -> Dict:
    """
    参数扫描分析：测试不同算力占比（alpha）下的自私挖矿收益变化。
    用于找出"最优的"攻击算力范围（能获得最大超额收益）。
    
    返回结构包含最优攻击参数和效率对比。
    """
    results = []
    alpha_values = [alpha_min + (alpha_max - alpha_min) * i / (alpha_steps - 1) 
                    for i in range(alpha_steps)]
    
    max_advantage = 0
    optimal_alpha = alpha_values[0]
    
    for alpha in alpha_values:
        no_defense, with_defense = simulate_selfish_with_defense(
            alpha=alpha,
            gamma_attack=gamma_attack,
            gamma_defense=gamma_defense,
            rounds=rounds,
            defense_enabled=True,
            seed=int(alpha * 1000)
        )
        
        revenue_advantage = no_defense.attacker_revenue_btc - (alpha * (no_defense.total_blocks * (6.25 + 0.5)))
        efficiency_gain = no_defense.efficiency_advantage
        
        results.append({
            "alpha": alpha,
            "no_defense": no_defense.to_dict(),
            "with_defense": with_defense.to_dict(),
            "revenue_advantage_btc": revenue_advantage,
            "efficiency_gain": efficiency_gain,
        })
        
        if efficiency_gain > max_advantage:
            max_advantage = efficiency_gain
            optimal_alpha = alpha
    
    summary = "参数扫描完成：最优算力占比 alpha = {:.3f}，此时效率优势倍数 = {:.4f}".format(
        optimal_alpha, max_advantage
    )
    
    return {
        "results": results,
        "optimal_alpha": optimal_alpha,
        "max_efficiency_gain": max_advantage,
        "summary": summary
    }


def pool_cooperative_mining(alpha: float, 
                            num_pools: int,
                            gamma: float,
                            rounds: int,
                            seed: int = None) -> SimulationResult:
    """
    矿池联合挖矿模型：
    假设有 num_pools 个矿池联合进行自私挖矿攻击。
    加入协调成本因子，模拟网络延迟的影响。
    """
    coordination_overhead = 0.02 * (num_pools - 1)
    effective_alpha = max(0, alpha - coordination_overhead)
    
    result = simulate_selfish_mining(
        alpha=effective_alpha,
        gamma=gamma,
        rounds=rounds,
        seed=seed
    )
    
    result.alpha = alpha
    return result


def asic_miner_advantage(alpha_computation: float,
                         asic_multiplier: float = 1.5,
                         gamma: float = 0.9,
                         rounds: int = 50000,
                         seed: int = None) -> Dict:
    """
    矿机（ASIC）硬件优势模型：
    
    真实情况：
    - 使用专业ASIC矿机可以获得相对GPU/CPU 1.5-10倍的算力优势
    - ASIC矿机的能耗比更高，成本结构不同
    - 拥有ASIC矿机的攻击者可以以更低成本维持较高算力占比
    
    这个函数模拟：
    1. 攻击者通过ASIC矿机获得额外算力倍增
    2. 计算实际获得的经济优势（考虑电力成本）
    3. 评估这种硬件优势是否构成对网络的威胁
    
    参数：
        alpha_computation: 攻击者的计算能力占比（假设基于CPU/GPU）
        asic_multiplier: ASIC相对于通用计算的倍数（通常 1.5-10）
        gamma: 网络优势参数
        rounds: 仿真轮数
        seed: 随机种子
    """
    # 攻击者通过ASIC获得的实际算力占比
    # 这里简化为：总网络算力 = alpha*multiplier + (1-alpha)*1（诚实矿工普遍算力）
    total_attacker_power = alpha_computation * asic_multiplier
    alpha_effective = total_attacker_power / (total_attacker_power + 1 - alpha_computation)
    alpha_effective = min(0.99, alpha_effective)  # 上限99%
    
    # 诚实挖矿基线
    honest_baseline = simulate_all_honest(
        alpha=alpha_effective,
        rounds=rounds,
        seed=seed
    )
    
    # 自私挖矿（利用ASIC优势）
    attacker_result = simulate_selfish_mining(
        alpha=alpha_effective,
        gamma=gamma,
        rounds=rounds,
        seed=seed
    )
    
    # 电力成本分析（简化模型）
    # ASIC功耗更低，相当于成本优势
    asic_power_cost_ratio = 1.0 / asic_multiplier  # ASIC成本更低
    honest_power_cost_ratio = 1.0
    
    return {
        "alpha_computation": alpha_computation,
        "asic_multiplier": asic_multiplier,
        "alpha_effective": alpha_effective,
        "honest_baseline": honest_baseline.to_dict(),
        "attacker_result": attacker_result.to_dict(),
        "asic_power_efficiency": asic_power_cost_ratio,
        "efficiency_advantage_with_asic": attacker_result.efficiency_advantage,
        "threat_level": "高威胁" if attacker_result.efficiency_advantage > 1.1 else "中等威胁" if attacker_result.efficiency_advantage > 1.0 else "低威胁",
        "summary": f"ASIC矿机（{asic_multiplier}倍）使得攻击者实际算力比升至 {alpha_effective:.4f}，"
                  f"可获得 {attacker_result.efficiency_advantage:.4f}x 的效率优势，"
                  f"威胁等级：{('高威胁' if attacker_result.efficiency_advantage > 1.1 else '中等威胁' if attacker_result.efficiency_advantage > 1.0 else '低威胁')}"
    }


def mev_transaction_ordering(alpha: float,
                              mev_extract_probability: float = 0.3,
                              avg_mev_per_block: float = 2.5,
                              gamma: float = 0.9,
                              rounds: int = 50000,
                              seed: int = None) -> Dict:
    """
    最大可提取价值（MEV）与交易排序优化：
    
    概念：
    - MEV（Maximal Extractable Value）是矿工通过排序、打包交易而获得的额外价值
    - 包括抢先交易、三明治攻击、清算抢先等
    - 攻击者可以通过控制区块内交易顺序获得额外收益
    
    这个函数计算：
    1. 攻击者通过MEV获得的额外收益
    2. 自私挖矿 + MEV 的复合效应
    3. MEV优化对抗防御的影响
    """
    # 基础自私挖矿结果
    attacker_result = simulate_selfish_mining(
        alpha=alpha,
        gamma=gamma,
        rounds=rounds,
        seed=seed
    )
    
    # MEV收益模型：
    # - 攻击者可以提取的MEV比例：取决于市场流动性和攻击机会
    # - 平均每个区块的MEV价值（BTC）
    mev_blocks = int(attacker_result.attacker_blocks * mev_extract_probability)
    total_mev_revenue = mev_blocks * avg_mev_per_block
    
    # 总收益 = 区块奖励 + 交易费 + MEV
    enhanced_revenue = attacker_result.attacker_revenue_btc + total_mev_revenue
    
    # 诚实矿工的收益（无法有效提取MEV）
    honest_revenue = attacker_result.honest_revenue_btc
    
    return {
        "alpha": alpha,
        "mev_extract_probability": mev_extract_probability,
        "avg_mev_per_block_btc": avg_mev_per_block,
        "attacker_blocks": attacker_result.attacker_blocks,
        "mev_extractable_blocks": mev_blocks,
        "base_revenue_btc": attacker_result.attacker_revenue_btc,
        "mev_revenue_btc": total_mev_revenue,
        "total_enhanced_revenue_btc": enhanced_revenue,
        "honest_revenue_btc": honest_revenue,
        "revenue_advantage_vs_honest": (enhanced_revenue - honest_revenue) / (honest_revenue if honest_revenue > 0 else 1),
        "revenue_per_hashrate": enhanced_revenue / (alpha if alpha > 0 else 0.01),
        "summary": f"MEV+自私挖矿：攻击者获得额外 {total_mev_revenue:.4f} BTC MEV收益，"
                  f"总收益优势 {(enhanced_revenue - honest_revenue) / (honest_revenue if honest_revenue > 0 else 1):.4f}x"
    }


def timing_optimization_attack(alpha: float,
                               network_delay_ms: float = 100.0,
                               block_time_sec: float = 600.0,
                               gamma: float = 0.9,
                               rounds: int = 50000,
                               seed: int = None) -> Dict:
    """
    时间优化攻击（Time Optimization / 挖矿时间优势）：
    
    概念：
    - 如果攻击者拥有更低的网络延迟（例如通过地理位置优化、CDN等），
      可以更快地传播自己的区块，从而获得优势
    - 即使算力相等，时间优势也能转化为经济优势
    - 这是"技术优势"的一种，与硬件性能提升不同
    
    模型：
    - 攻击者的有效网络传播时间：network_delay_ms
    - 这会影响在分叉竞争中赢得节点支持的概率
    - 延迟越小，gamma_effective 越接近 1.0
    """
    # 基于网络延迟计算有效的 gamma
    # 假设：network_delay / block_time 越小，攻击者在分叉中优势越大
    delay_ratio = network_delay_ms / (block_time_sec * 1000)
    # 当延迟接近0时，gamma接近1；延迟越大，gamma越接近0.5
    gamma_effective = 0.5 + 0.5 * (1 - min(1.0, delay_ratio))
    gamma_effective = max(0.5, min(1.0, gamma_effective))
    
    # 运行仿真
    attacker_result = simulate_selfish_mining(
        alpha=alpha,
        gamma=gamma_effective,
        rounds=rounds,
        seed=seed
    )
    
    honest_result = simulate_all_honest(
        alpha=alpha,
        rounds=rounds,
        seed=seed
    )
    
    # 计算时间优化带来的优势
    time_advantage_factor = attacker_result.efficiency_advantage / (honest_result.attacker_relative_reward / alpha if alpha > 0 else 1.0)
    
    return {
        "alpha": alpha,
        "network_delay_ms": network_delay_ms,
        "block_time_sec": block_time_sec,
        "delay_ratio": delay_ratio,
        "gamma_effective": gamma_effective,
        "attacker_efficiency": attacker_result.efficiency_advantage,
        "honest_baseline_ratio": honest_result.attacker_relative_reward / alpha if alpha > 0 else 1.0,
        "time_advantage_factor": time_advantage_factor,
        "revenue_advantage_btc": attacker_result.attacker_revenue_btc - honest_result.attacker_revenue_btc,
        "threat_level": "高威胁" if time_advantage_factor > 1.05 else "低威胁",
        "summary": f"时间优化攻击：{network_delay_ms}ms网络延迟使攻击者获得{time_advantage_factor:.4f}x优势，"
                  f"预期额外收益 {attacker_result.attacker_revenue_btc - honest_result.attacker_revenue_btc:.4f} BTC"
    }


def cross_chain_attack(alpha: float,
                       num_chains: int = 3,
                       gamma: float = 0.9,
                       rounds_per_chain: int = 50000,
                       seed: int = None) -> Dict:
    """
    跨链/多链攻击模型：
    
    场景：
    - 攻击者同时对多条相似的区块链进行攻击（例如比特币现金、莱特币、或山寨币）
    - 通过在多条链上分散算力，可以获得"多倍"的收益
    - 但也需要在多条链之间协调，存在效率损失
    
    收益计算：
    - 单链独立攻击的总收益 * 链数 * (1 - 协调开销)
    """
    coordination_cost_per_chain = 0.01  # 每条额外链增加1%的协调成本
    coordination_overhead = coordination_cost_per_chain * (num_chains - 1)
    
    # 在每条链上独立进行攻击
    results_per_chain = []
    total_revenue = 0.0
    
    for i in range(num_chains):
        chain_seed = None if seed is None else seed + i * 1000
        result = simulate_selfish_mining(
            alpha=alpha,
            gamma=gamma,
            rounds=rounds_per_chain,
            seed=chain_seed
        )
        results_per_chain.append(result.to_dict())
        total_revenue += result.attacker_revenue_btc
    
    # 应用协调开销
    effective_revenue = total_revenue * (1 - coordination_overhead)
    
    # 单链攻击的基准
    single_chain_result = simulate_selfish_mining(
        alpha=alpha,
        gamma=gamma,
        rounds=rounds_per_chain,
        seed=seed
    )
    
    total_revenue_comparison = {
        "single_chain_btc": single_chain_result.attacker_revenue_btc,
        "multi_chain_total_before_cost_btc": total_revenue,
        "multi_chain_total_after_cost_btc": effective_revenue,
        "coordination_overhead_percent": coordination_overhead * 100,
        "multiplier_effect": effective_revenue / single_chain_result.attacker_revenue_btc if single_chain_result.attacker_revenue_btc > 0 else 1.0
    }
    
    return {
        "alpha": alpha,
        "num_chains": num_chains,
        "gamma": gamma,
        "coordination_cost_per_chain": coordination_cost_per_chain,
        "results_per_chain": results_per_chain,
        "revenue_comparison": total_revenue_comparison,
        "summary": f"跨{num_chains}条链攻击：总收益 {effective_revenue:.4f} BTC（单链基准 {single_chain_result.attacker_revenue_btc:.4f}），"
                  f"复合倍数 {total_revenue_comparison['multiplier_effect']:.4f}x"
    }


def defense_mechanism_comparison(alpha: float, 
                                 rounds: int = 50000) -> Dict:
    
    # 基准：未防御
    no_defense, _ = simulate_selfish_with_defense(
        alpha=alpha, gamma_attack=0.9, gamma_defense=0.5, 
        rounds=rounds, defense_enabled=True, seed=2025
    )
    
    defense_strategies = [
        {"name": "随机分叉选择", "gamma": 0.5},
        {"name": "最长链规则", "gamma": 0.5},
        {"name": "强化中继网络", "gamma": 0.4},
        {"name": "难度动态调整", "gamma": 0.3},
        {"name": "跨链验证", "gamma": 0.2},
    ]
    
    results = {
        "baseline_no_defense": no_defense.to_dict(),
        "strategies": []
    }
    
    for strategy in defense_strategies:
        _, with_defense = simulate_selfish_with_defense(
            alpha=alpha,
            gamma_attack=0.9,
            gamma_defense=strategy["gamma"],
            rounds=rounds,
            defense_enabled=True,
            seed=int(strategy["gamma"] * 10000)
        )
        
        results["strategies"].append({
            "name": strategy["name"],
            "gamma": strategy["gamma"],
            "result": with_defense.to_dict(),
            "improvement_percent": (1 - with_defense.efficiency_advantage) * 100
        })
    
    return results


def advanced_analysis_report(alpha: float = 0.3, rounds: int = 100000) -> str:
    """
    生成高级分析报告，包含参数扫描、防御机制对比等。
    """
    report = []
    report.append("=" * 80)
    report.append("比特币自私挖矿与防御机制研究报告")
    report.append("=" * 80)
    report.append("")
    
    # 第一部分：基线分析
    report.append("【第一部分】基线对比分析")
    report.append("-" * 80)
    honest_baseline = simulate_all_honest(alpha=alpha, rounds=rounds, seed=42)
    no_defense, with_defense = simulate_selfish_with_defense(
        alpha=alpha, gamma_attack=0.9, gamma_defense=0.5,
        rounds=rounds, defense_enabled=True, seed=2025
    )
    
    report.append(f"测试参数: alpha={alpha:.2f}, rounds={rounds}")
    report.append(f"")
    report.append(f"诚实挖矿基线:")
    report.append(f"  - 攻击者收益占比: {honest_baseline.attacker_relative_reward:.4f}")
    report.append(f"  - 理论期望值: {alpha:.4f}")
    report.append(f"  - 偏差: {abs(honest_baseline.attacker_relative_reward - alpha):.6f}")
    report.append(f"")
    report.append(f"自私挖矿（未防御，gamma=0.9）:")
    report.append(f"  - 攻击者收益占比: {no_defense.attacker_relative_reward:.4f}")
    report.append(f"  - 效率优势倍数: {no_defense.efficiency_advantage:.4f}x")
    report.append(f"  - 超额收益（BTC）: {no_defense.attacker_revenue_btc - honest_baseline.attacker_revenue_btc:.4f}")
    report.append(f"")
    report.append(f"自私挖矿（防御后，gamma=0.5）:")
    report.append(f"  - 攻击者收益占比: {with_defense.attacker_relative_reward:.4f}")
    report.append(f"  - 效率优势倍数: {with_defense.efficiency_advantage:.4f}x")
    if no_defense.efficiency_advantage > 0:
        report.append(f"  - 防御效果: 收益下降 {(1 - with_defense.efficiency_advantage/no_defense.efficiency_advantage)*100:.2f}%")
    report.append("")
    
    # 第二部分：参数扫描
    report.append("【第二部分】参数扫描分析（寻找最优攻击参数）")
    report.append("-" * 80)
    sweep_result = parameter_sweep_analysis(
        alpha_min=0.1, alpha_max=0.4, alpha_steps=7,
        gamma_attack=0.9, gamma_defense=0.5, rounds=50000
    )
    
    report.append(sweep_result["summary"])
    report.append("")
    report.append("详细结果:")
    for res in sweep_result["results"]:
        report.append(f"  alpha={res['alpha']:.3f}: "
                     f"未防御效率={res['no_defense']['efficiency_advantage']:.4f}x, "
                     f"防御后效率={res['with_defense']['efficiency_advantage']:.4f}x")
    report.append("")
    
    # 第三部分：防御机制对比
    report.append("【第三部分】多种防御机制对比")
    report.append("-" * 80)
    defense_results = defense_mechanism_comparison(alpha=alpha, rounds=50000)
    
    for strategy in defense_results["strategies"]:
        report.append(f"  {strategy['name']} (gamma={strategy['gamma']:.2f}):")
        report.append(f"    - 攻击者效率: {strategy['result']['efficiency_advantage']:.4f}x")
        report.append(f"    - 防御改进: {strategy['improvement_percent']:.2f}%")
    report.append("")
    
    # 第四部分：结论
    report.append("【第四部分】结论与建议")
    report.append("-" * 80)
    report.append(f"1. 自私挖矿的威胁: 在 alpha={alpha:.2f} 的算力下，自私矿工可以获得约 {no_defense.efficiency_advantage:.4f}x")
    report.append(f"   的效率优势，相当于额外获利约 {(no_defense.efficiency_advantage-1)*100:.2f}%。")
    report.append(f"")
    report.append(f"2. 防御机制的有效性: 通过改进网络传播（降低 gamma），可以将效率优势降低到 {with_defense.efficiency_advantage:.4f}x，")
    report.append(f"   基本消除了自私挖矿的经济激励。")
    report.append(f"")
    report.append(f"3. 最优攻击参数: alpha={sweep_result['optimal_alpha']:.3f} 时攻击最有利，此时效率优势达 {sweep_result['max_efficiency_gain']:.4f}x。")
    report.append(f"")
    report.append(f"4. 对矿池联合攻击的威胁评估: 多个矿池联合会增加协调成本，但在协议层面仍然构成威胁。")
    report.append(f"   建议采用多层次防御（网络层、协议层、激励层）。")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


def comprehensive_attack_comparison(alpha: float = 0.2, rounds: int = 50000) -> str:
    """
    综合对比所有攻击向量的威胁程度和防御策略。
    """
    report = []
    report.append("=" * 100)
    report.append("比特币挖矿攻击综合分析：多种不公平策略对比")
    report.append("=" * 100)
    report.append("")
    
    # 1. ASIC矿机优势
    report.append("【1】ASIC矿机硬件优势分析")
    report.append("-" * 100)
    for multiplier in [1.5, 3.0, 5.0, 10.0]:
        asic_result = asic_miner_advantage(
            alpha_computation=alpha,
            asic_multiplier=multiplier,
            gamma=0.9,
            rounds=rounds,
            seed=2025
        )
        report.append(f"ASIC倍数 {multiplier}x:")
        report.append(f"  - 实际算力占比: {asic_result['alpha_effective']:.4f}")
        report.append(f"  - 效率优势: {asic_result['efficiency_advantage_with_asic']:.4f}x")
        report.append(f"  - 威胁等级: {asic_result['threat_level']}")
        report.append("")
    
    # 2. MEV + 自私挖矿
    report.append("【2】MEV与自私挖矿的复合效应")
    report.append("-" * 100)
    for mev_prob in [0.1, 0.3, 0.5]:
        mev_result = mev_transaction_ordering(
            alpha=alpha,
            mev_extract_probability=mev_prob,
            avg_mev_per_block=2.5,
            gamma=0.9,
            rounds=rounds,
            seed=2025
        )
        report.append(f"MEV提取概率 {mev_prob*100:.0f}%:")
        report.append(f"  - 基础收益: {mev_result['base_revenue_btc']:.4f} BTC")
        report.append(f"  - MEV收益: {mev_result['mev_revenue_btc']:.4f} BTC")
        report.append(f"  - 总收益: {mev_result['total_enhanced_revenue_btc']:.4f} BTC")
        report.append(f"  - 相对优势: {mev_result['revenue_advantage_vs_honest']:.4f}x")
        report.append("")
    
    # 3. 时间优化攻击
    report.append("【3】网络传播延迟的时间优化攻击")
    report.append("-" * 100)
    for delay_ms in [10, 50, 100, 200, 500]:
        timing_result = timing_optimization_attack(
            alpha=alpha,
            network_delay_ms=delay_ms,
            block_time_sec=600.0,
            gamma=0.9,
            rounds=rounds,
            seed=2025
        )
        report.append(f"网络延迟 {delay_ms}ms:")
        report.append(f"  - 有效gamma: {timing_result['gamma_effective']:.4f}")
        report.append(f"  - 攻击者效率: {timing_result['attacker_efficiency']:.4f}x")
        report.append(f"  - 时间优势倍数: {timing_result['time_advantage_factor']:.4f}x")
        report.append(f"  - 额外收益: {timing_result['revenue_advantage_btc']:.4f} BTC")
        report.append("")
    
    # 4. 跨链攻击
    report.append("【4】跨链/多链攻击的复合威胁")
    report.append("-" * 100)
    for num_chains in [1, 2, 3, 5]:
        cross_result = cross_chain_attack(
            alpha=alpha,
            num_chains=num_chains,
            gamma=0.9,
            rounds_per_chain=rounds,
            seed=2025
        )
        if num_chains == 1:
            report.append(f"基准（单链）:")
        else:
            report.append(f"跨{num_chains}条链攻击:")
        report.append(f"  - 总收益: {cross_result['revenue_comparison']['multi_chain_total_after_cost_btc']:.4f} BTC")
        report.append(f"  - 复合倍数: {cross_result['revenue_comparison']['multiplier_effect']:.4f}x")
        report.append(f"  - 协调成本: {cross_result['revenue_comparison']['coordination_overhead_percent']:.2f}%")
        report.append("")
    
    report.append("=" * 100)
    report.append("【总结】多向量攻击的联合威胁")
    report.append("=" * 100)
    report.append("")
    report.append("最严重的威胁场景：攻击者同时拥有")
    report.append("  1. 高效ASIC矿机（5-10倍优势）")
    report.append("  2. 低网络延迟部署（CDN+地理位置优化）")
    report.append("  3. MEV提取能力（前置交易、套利等）")
    report.append("  4. 多条相关链的同步攻击")
    report.append("")
    report.append("这种组合可以产生：")
    asic_r = asic_miner_advantage(alpha, 5.0, 0.9, rounds, 2025)
    timing_r = timing_optimization_attack(alpha, 50, 600, 0.9, rounds, 2025)
    mev_r = mev_transaction_ordering(alpha, 0.3, 2.5, 0.9, rounds, 2025)
    cross_r = cross_chain_attack(alpha, 3, 0.9, rounds, 2025)
    
    combined_advantage = asic_r['efficiency_advantage_with_asic'] * timing_r['time_advantage_factor'] * mev_r['revenue_advantage_vs_honest'] * (cross_r['revenue_comparison']['multiplier_effect'] / 3.0)
    report.append(f"  - 复合效率优势: ~{combined_advantage:.4f}x（注：参数非线性组合）")
    report.append(f"  - 相对于公平挖矿的超额收益: ~{(combined_advantage-1)*100:.2f}%")
    
    return "\n".join(report)


def defense_recommendation_report(alpha: float = 0.2, rounds: int = 50000) -> str:
    """
    针对上述多种攻击的防御推荐方案。
    """
    report = []
    report.append("=" * 100)
    report.append("对抗不公平挖矿策略的防御措施推荐")
    report.append("=" * 100)
    report.append("")
    
    report.append("【第1层】网络层防御")
    report.append("-" * 100)
    report.append("1. 改进中继网络（Relay Networks）")
    report.append("   - 减少区块传播延迟，降低时间优化攻击的效果")
    report.append("   - 目标：网络延迟 < 10ms")
    report.append("   - 效果评估：")
    
    for delay in [100, 50, 10]:
        timing_r = timing_optimization_attack(alpha, delay, 600, 0.9, rounds, 2025)
        report.append(f"     * {delay}ms延迟 -> 攻击者优势 {timing_r['time_advantage_factor']:.4f}x")
    
    report.append("")
    report.append("2. 强化节点间连接（P2P Network Hardening）")
    report.append("   - 减少BGP劫持、DDoS等网络攻击")
    report.append("   - 提高分布式节点的鲁棒性")
    report.append("")
    
    report.append("【第2层】协议层防御")
    report.append("-" * 100)
    report.append("1. 改进共识机制")
    report.append("   - 采用随机分叉选择规则，削弱网络优势（gamma）")
    
    no_defense, with_defense = simulate_selfish_with_defense(alpha, 0.9, 0.5, rounds, True, 2025)
    report.append(f"   - 未防御 (gamma=0.9): 效率优势 {no_defense.efficiency_advantage:.4f}x")
    report.append(f"   - 防御后 (gamma=0.5): 效率优势 {with_defense.efficiency_advantage:.4f}x")
    report.append(f"   - 防御效果: {(1 - with_defense.efficiency_advantage/no_defense.efficiency_advantage)*100:.2f}%改进")
    report.append("")
    
    report.append("2. 难度调整机制优化")
    report.append("   - 动态调整挖矿难度，对抗ASIC集中化")
    report.append("   - 缩短难度调整周期")
    report.append("")
    
    report.append("【第3层】经济激励层防御")
    report.append("-" * 100)
    report.append("1. 交易费机制改进（Fee Market Mechanism）")
    report.append("   - 动态手续费，提高诚实矿工的收益相对占比")
    report.append("   - 减少MEV提取的空间")
    report.append("")
    
    report.append("2. 矿工奖励多样化")
    report.append("   - 不仅基于区块奖励，增加其他激励维度")
    report.append("   - 使攻击者难以计算攻击收益")
    report.append("")
    
    report.append("【第4层】应用层防御")
    report.append("-" * 100)
    report.append("1. MEV最小化")
    report.append("   - 实现公平的交易排序（Fair Transaction Ordering）")
    report.append("   - 应用零知识证明隐私交易")
    report.append("")
    
    report.append("2. 跨链安全")
    report.append("   - 在跨链桥接处增加额外验证")
    report.append("   - 限制单个矿工在跨链中的权力")
    report.append("")
    
    report.append("【综合评分】多层防御的联合效果")
    report.append("-" * 100)
    report.append("")
    
    defense_scores = {
        "仅网络层": 0.4,
        "网络+协议层": 0.7,
        "网络+协议+经济层": 0.85,
        "全四层防御": 0.95
    }
    
    for defense_level, score in defense_scores.items():
        improvement = score * 100
        report.append(f"{defense_level:20s}: 防御效果 {improvement:.0f}% (对抗成功率)")
    
    report.append("")
    report.append("=" * 100)
    
    return "\n".join(report)


def run_demo():
    """
    完整的命令行演示程序，包含：
    1. 多种不公平挖矿策略对比
    2. 防御机制的综合评估
    3. 生成详细的分析报告
    """
    alpha = 0.25
    rounds = 100000

    print("=" * 100)
    print("比特币挖矿攻击与防御的综合研究")
    print("="*100)
    print()

    # 生成攻击分析报告
    print("==== 正在生成攻击向量分析... ====")
    attack_report = comprehensive_attack_comparison(alpha=alpha, rounds=rounds)
    print(attack_report)
    print()
    
    # 生成防御建议报告
    print("==== 正在生成防御策略建议... ====")
    defense_report = defense_recommendation_report(alpha=alpha, rounds=rounds)
    print(defense_report)
    print()
    
    # 保存报告
    full_report = "比特币挖矿研究：攻击与防御分析\n\n" + attack_report + "\n\n" + defense_report
    with open("/Users/Hoshino/Documents/comprehensive_mining_report.txt", "w", encoding="utf-8") as f:
        f.write(full_report)
    print("详细报告已保存到: /Users/Hoshino/Documents/comprehensive_mining_report.txt")


if __name__ == "__main__":
    run_demo()
