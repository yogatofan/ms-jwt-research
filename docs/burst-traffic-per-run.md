### Data Ringkasan Cepat per Run (Burst Traffic)

Jika ingin melihat angka mentah per-run secara langsung tanpa membuka satu per satu file JSON:

#### A. Burst — Without Security
| Run | Total Attempted | 2xx Responses | Failed HTTP Reqs | 429 Responses | Overall HTTP Fail Rate | Login-Stage Fail Rate |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Run 1** | $87,292$ | $42,346$ | $44,946$ | $0$ | $51.49\%$ | $84.08\%$ |
| **Run 2** | $87,080$ | $42,495$ | $44,585$ | $0$ | $51.20\%$ | $83.57\%$ |
| **Run 3** | $87,823$ | $40,989$ | $46,834$ | $0$ | $53.33\%$ | $85.51\%$ |
| **Run 4** | $84,954$ | $42,004$ | $42,950$ | $0$ | $50.56\%$ | $83.33\%$ |
| **Run 5** | $86,289$ | $41,078$ | $45,211$ | $0$ | $52.39\%$ | $84.06\%$ |
| **Mean $\pm$ SD** | $\mathbf{86,687.6 \pm 1,115.0}$ | $\mathbf{41,782.4 \pm 707.1}$ | $\mathbf{44,905.2 \pm 1,391.1}$ | $\mathbf{0.0 \pm 0.0}$ | $\mathbf{51.79\% \pm 1.08\%}$ | $\mathbf{84.11\% \pm 0.84\%}$ |

#### B. Burst — With JWT + Rate Limiting
| Run | Total Attempted | 2xx Responses | HTTP 429 Responses | Rate-Limited Rate (%) | Backend Forwarded |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Run 1** | $2,975,750$ | $60$ | $2,975,690$ | $99.9980\%$ | $60$ |
| **Run 2** | $2,987,894$ | $60$ | $2,987,834$ | $99.9980\%$ | $60$ |
| **Run 3** | $2,947,402$ | $60$ | $2,947,342$ | $99.9980\%$ | $60$ |
| **Run 4** | $2,988,765$ | $60$ | $2,988,705$ | $99.9980\%$ | $60$ |
| **Run 5** | $2,938,795$ | $60$ | $2,938,735$ | $99.9980\%$ | $60$ |
| **Mean $\pm$ SD** | $\mathbf{2,967,721.2 \pm 23,258.5}$ | $\mathbf{60.0 \pm 0.0}$ | $\mathbf{2,967,661.2 \pm 23,258.5}$ | $\mathbf{99.9980\% \pm 0.0008\%}$ | $\mathbf{60.0 \pm 0.0}$ |