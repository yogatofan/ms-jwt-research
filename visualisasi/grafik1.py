import matplotlib.pyplot as plt
import numpy as np

endpoints = ['Login', 'Product', 'Order']
no_sec = [2.81, 2.40, 2.57]
with_sec = [3.04, 2.80, 2.98]

x = np.arange(len(endpoints))
width = 0.35

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(x - width/2, no_sec, width, label='Without Security', color='#B4B2A9')
ax.bar(x + width/2, with_sec, width, label='With JWT + Rate Limiting', color='#378ADD')

ax.set_ylabel('Average Latency (ms)')
# ax.set_title('Fig. 3. Normal Traffic Latency Comparison')
ax.set_xticks(x)
ax.set_xticklabels(endpoints)
ax.legend()
ax.set_ylim(0, 4)
plt.tight_layout()
plt.savefig('fig3-normal-latency.pdf', dpi=300, bbox_inches='tight')
plt.savefig('fig3-normal-latency.png', dpi=300, bbox_inches='tight')
print("Saved: fig3-normal-latency.pdf and fig3-normal-latency.png")