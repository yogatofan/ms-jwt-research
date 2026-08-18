============================================================
  ms-jwt-research Statistical Analyzer
  Runs per scenario : 5
  Results dir       : /Users/yogatofan/Research/ms-jwt-research/load-testing/results
  Output dir        : /Users/yogatofan/Research/ms-jwt-research/visualisasi
============================================================

[OK]  Scenario 'normal-no-security': 5 run(s) processed.
[OK]  Scenario 'normal-with-security': 5 run(s) processed.
[OK]  Scenario 'burst-no-security': 5 run(s) processed.
[OK]  Scenario 'burst-with-security': 5 run(s) processed.

══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
Metric                         │ Normal / No Security           │ Normal / JWT + Rate Limiting   │ Burst  / No Security           │ Burst  / JWT + Rate Limiting  
══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
Login Latency avg (ms)         │ 3.562 ± 0.027                  │ 1.118 ± 0.015                  │ 10.924 ± 1.999                 │ 3.001 ± 0.024                 
Login Latency p95 (ms)         │ 4.597 ± 0.127                  │ 1.557 ± 0.020                  │ 11.520 ± 1.028                 │ 4.784 ± 0.024                 
Product Latency avg (ms)       │ 3.070 ± 0.042                  │ 5.122 ± 0.374                  │ 33.713 ± 6.860                 │ 1.515 ± 0.086                 
Product Latency p95 (ms)       │ 4.119 ± 0.096                  │ 7.621 ± 0.940                  │ 30.770 ± 15.786                │ 2.661 ± 0.151                 
Order Latency avg (ms)         │ 3.238 ± 0.059                  │ 6.311 ± 0.224                  │ N/A ± 0.000                    │ N/A ± 0.000                   
HTTP Duration avg (ms)         │ 3.290 ± 0.036                  │ 1.218 ± 0.017                  │ 20.945 ± 3.475                 │ 3.001 ± 0.024                 
HTTP Duration p95 (ms)         │ 4.413 ± 0.085                  │ 1.626 ± 0.032                  │ 19.346 ± 1.331                 │ 4.784 ± 0.024                 
HTTP Duration max (ms)         │ 18.540 ± 0.200                 │ 21.841 ± 1.376                 │ 4373.124 ± 2024.727            │ 23.120 ± 8.149                
Error Rate                     │ 0.00% ± 0.00%                  │ 96.73% ± 0.00%                 │ 84.11% ± 0.84%                 │ 0.00% ± 0.00%                 
Throughput (req/s)             │ 7.656 ± 0.003                  │ 7.613 ± 0.001                  │ 1233.588 ± 18.343              │ 42395.946 ± 332.082           
══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

[OK] CSV saved → /Users/yogatofan/Research/ms-jwt-research/load-testing/results/statistical-summary.csv

Generating charts...
[OK] Saved → /Users/yogatofan/Research/ms-jwt-research/visualisasi/fig3-normal-latency-stats.pdf
[OK] Saved → /Users/yogatofan/Research/ms-jwt-research/visualisasi/fig3-normal-latency-stats.png
[OK] Saved → /Users/yogatofan/Research/ms-jwt-research/visualisasi/fig4-burst-traffic-stats.pdf
[OK] Saved → /Users/yogatofan/Research/ms-jwt-research/visualisasi/fig4-burst-traffic-stats.png
[OK] Saved → /Users/yogatofan/Research/ms-jwt-research/visualisasi/fig5-throughput-stats.pdf
[OK] Saved → /Users/yogatofan/Research/ms-jwt-research/visualisasi/fig5-throughput-stats.png

============================================================
  Analysis complete!
  CSV     → /Users/yogatofan/Research/ms-jwt-research/load-testing/results/statistical-summary.csv
  Charts  → /Users/yogatofan/Research/ms-jwt-research/visualisasi/fig3-*.png, fig4-*.png, fig5-*.png
============================================================