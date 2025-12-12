# plot_experiments.py
# -------------------------------------------------
# Paper-grade experiment plotting script
# Figures: Fig. 5.1 – Fig. 5.10
# -------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt

from plot_style import set_paper_style, save_figure

# Enable paper-grade plotting style (ONCE)
set_paper_style(
    font_size=12,
    dpi=300,
    use_latex=False
)

from quant import (
    simulate_all_honest,
    simulate_selfish_mining,
    simulate_selfish_with_defense,
    parameter_sweep_analysis,
    asic_miner_advantage,
    mev_transaction_ordering,
    timing_optimization_attack,
    cross_chain_attack,
    defense_mechanism_comparison
)


# -------------------------------------------------
# Fig. 5.1 Honest mining baseline
# -------------------------------------------------
def plot_honest_baseline():
    alpha = 0.25
    res = simulate_all_honest(alpha, rounds=10000, seed=42)

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.bar(
        ["Attacker", "Honest"],
        [res.attacker_relative_reward, res.honest_relative_reward]
    )
    ax.axhline(alpha, linestyle="--", label="Theoretical α")

    ax.set_ylabel("Block Share")
    ax.set_title("Honest Mining Baseline")
    ax.legend()

    save_figure(fig, "fig_5_1_honest_baseline.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.2 Selfish mining block share
# -------------------------------------------------
def plot_selfish_block_share():
    res = simulate_selfish_mining(alpha=0.25, gamma=0.9, rounds=10000, seed=42)

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.bar(
        ["Selfish Miner", "Honest Miners"],
        [res.attacker_relative_reward, res.honest_relative_reward]
    )

    ax.set_ylabel("Block Share")
    ax.set_title("Selfish Mining Block Share (α=0.25, γ=0.9)")

    save_figure(fig, "fig_5_2_selfish_blocks.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.3 Revenue comparison
# -------------------------------------------------
def plot_selfish_revenue():
    honest = simulate_all_honest(0.25, rounds=10000, seed=42)
    selfish = simulate_selfish_mining(0.25, 0.9, rounds=10000, seed=42)

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.bar(
        ["Honest Mining", "Selfish Mining"],
        [honest.attacker_revenue_btc, selfish.attacker_revenue_btc]
    )

    ax.set_ylabel("Revenue (BTC)")
    ax.set_title("Revenue Comparison")

    save_figure(fig, "fig_5_3_selfish_revenue.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.4 Sensitivity to γ
# -------------------------------------------------
def plot_gamma_sensitivity():
    gammas = [0.9, 0.7, 0.5, 0.3]
    efficiencies = []

    for g in gammas:
        r = simulate_selfish_mining(0.25, g, rounds=10000, seed=42)
        efficiencies.append(r.efficiency_advantage)

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.plot(gammas, efficiencies, marker="o")
    ax.set_xlabel("γ (Network Advantage)")
    ax.set_ylabel("Efficiency Advantage")
    ax.set_title("Sensitivity to γ")

    save_figure(fig, "fig_5_4_gamma_sensitivity.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.5 α parameter sweep
# -------------------------------------------------
def plot_alpha_sweep():
    sweep = parameter_sweep_analysis(
        alpha_min=0.1,
        alpha_max=0.4,
        alpha_steps=7,
        gamma_attack=0.9,
        gamma_defense=0.5,
        rounds=10000
    )

    alphas = [r["alpha"] for r in sweep["results"]]
    effs = [r["efficiency_gain"] for r in sweep["results"]]

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.plot(alphas, effs, marker="o")
    ax.set_xlabel("α (Hash Power Share)")
    ax.set_ylabel("Efficiency Advantage")
    ax.set_title("Efficiency vs α")

    save_figure(fig, "fig_5_5_alpha_sweep.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.6 ASIC hardware advantage
# -------------------------------------------------
def plot_asic_advantage():
    multipliers = [1.0, 1.5, 3.0, 5.0]
    efficiencies = []

    for m in multipliers:
        r = asic_miner_advantage(0.25, asic_multiplier=m, rounds=10000, seed=42)
        efficiencies.append(r["efficiency_advantage_with_asic"])

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.plot(multipliers, efficiencies, marker="o")
    ax.set_xlabel("ASIC Multiplier")
    ax.set_ylabel("Efficiency Advantage")
    ax.set_title("ASIC Hardware Advantage")

    save_figure(fig, "fig_5_6_asic_advantage.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.7 MEV effect
# -------------------------------------------------
def plot_mev_effect():
    probs = [0.1, 0.3, 0.5]
    revenues = []

    for p in probs:
        r = mev_transaction_ordering(
            0.25,
            mev_extract_probability=p,
            rounds=10000,
            seed=42
        )
        revenues.append(r["total_enhanced_revenue_btc"])

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.plot(probs, revenues, marker="o")
    ax.set_xlabel("MEV Extraction Probability")
    ax.set_ylabel("Total Revenue (BTC)")
    ax.set_title("MEV Impact on Mining Revenue")

    save_figure(fig, "fig_5_7_mev_effect.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.8 Network delay optimization
# -------------------------------------------------
def plot_network_delay():
    delays = [10, 50, 100, 200, 500]
    efficiencies = []

    for d in delays:
        r = timing_optimization_attack(
            0.25,
            network_delay_ms=d,
            rounds=10000,
            seed=42
        )
        efficiencies.append(r["attacker_efficiency"])

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.plot(delays, efficiencies, marker="o")
    ax.set_xlabel("Network Delay (ms)")
    ax.set_ylabel("Efficiency Advantage")
    ax.set_title("Network Delay Optimization")

    save_figure(fig, "fig_5_8_network_delay.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.9 Cross-chain attack
# -------------------------------------------------
def plot_multichain_attack():
    chains = [1, 2, 3, 5]
    multipliers = []

    for c in chains:
        r = cross_chain_attack(
            0.25,
            num_chains=c,
            rounds_per_chain=10000,
            seed=42
        )
        multipliers.append(r["revenue_comparison"]["multiplier_effect"])

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.plot(chains, multipliers, marker="o")
    ax.set_xlabel("Number of Chains")
    ax.set_ylabel("Revenue Multiplier")
    ax.set_title("Cross-chain Attack Gain")

    save_figure(fig, "fig_5_9_multichain_attack.pdf")
    plt.close(fig)


# -------------------------------------------------
# Fig. 5.10 Defense mechanism comparison
# -------------------------------------------------
def plot_defense_comparison():
    res = defense_mechanism_comparison(0.25, rounds=10000)

    names = [s["name"] for s in res["strategies"]]
    effs = [s["result"]["efficiency_advantage"] for s in res["strategies"]]

    fig, ax = plt.subplots(figsize=(5, 3.5))

    ax.bar(names, effs)
    ax.set_ylabel("Efficiency Advantage")
    ax.set_title("Defense Strategy Comparison")
    ax.set_xticklabels(names, rotation=25)

    save_figure(fig, "fig_5_10_defense_comparison.pdf")
    plt.close(fig)


# -------------------------------------------------
# Run all plots
# -------------------------------------------------
def run_all_plots():
    plot_honest_baseline()
    plot_selfish_block_share()
    plot_selfish_revenue()
    plot_gamma_sensitivity()
    plot_alpha_sweep()
    plot_asic_advantage()
    plot_mev_effect()
    plot_network_delay()
    plot_multichain_attack()
    plot_defense_comparison()
    print("All figures generated successfully.")


if __name__ == "__main__":
    run_all_plots()