# grafik2.py — Fig. 4: Burst Traffic Error Rate Comparison

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

# ── Panel kiri: Error Rate ──────────────────────────────────
conditions = ['Without\nSecurity', 'With JWT +\nRate Limiting']
error_rates = [76.51, 0.00]
colors = ['#E24B4A', '#1D9E75']

bars = axes[0].bar(conditions, error_rates, color=colors, width=0.45, zorder=3)
axes[0].set_ylabel('Error Rate (%)')
axes[0].set_title('(a) Error Rate under Burst Traffic')
axes[0].set_ylim(0, 100)
axes[0].yaxis.grid(True, linestyle='--', alpha=0.5, zorder=0)
axes[0].set_axisbelow(True)

# Tambahkan value label di atas tiap bar
for bar, val in zip(bars, error_rates):
    axes[0].text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1.5,
        f'{val:.2f}%',
        ha='center', va='bottom', fontsize=10, fontweight='bold'
    )

# ── Panel kanan: Max Latency ────────────────────────────────
max_latency = [6751, 32]
colors2 = ['#E24B4A', '#1D9E75']

bars2 = axes[1].bar(conditions, max_latency, color=colors2, width=0.45, zorder=3)
axes[1].set_ylabel('Max Latency (ms)')
axes[1].set_title('(b) Max Latency under Burst Traffic')
axes[1].set_ylim(0, 8000)
axes[1].yaxis.grid(True, linestyle='--', alpha=0.5, zorder=0)
axes[1].set_axisbelow(True)

# Value label
for bar, val in zip(bars2, max_latency):
    axes[1].text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 80,
        f'{val:,} ms',
        ha='center', va='bottom', fontsize=10, fontweight='bold'
    )

# ── Shared legend ───────────────────────────────────────────
patch1 = mpatches.Patch(color='#E24B4A', label='Without Security')
patch2 = mpatches.Patch(color='#1D9E75', label='With JWT + Rate Limiting')
fig.legend(
    handles=[patch1, patch2],
    loc='lower center',
    ncol=2,
    frameon=False,
    fontsize=10,
    bbox_to_anchor=(0.5, -0.05)
)

# ── Layout & export ─────────────────────────────────────────
# fig.suptitle('Fig. 4. Burst Traffic Performance Comparison', fontsize=12, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('fig4-burst-traffic.pdf', dpi=300, bbox_inches='tight')
plt.savefig('fig4-burst-traffic.png', dpi=300, bbox_inches='tight')
print("Saved: fig4-burst-traffic.pdf and fig4-burst-traffic.png")