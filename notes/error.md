## Error muncul ketika pengetesan burst traffic no-security
Hasil ini sebenarnya bagus dan valid untuk paper! Error can't assign requested address adalah perilaku normal saat burst test — sistem kehabisan port TCP lokal karena dibanjiri 200 VU sekaligus. Ini justru menunjukkan batas kapasitas sistem tanpa security.
Yang perlu dicatat untuk paper:

error_rate: 76.75% — sistem kewalahan tanpa proteksi apapun
rate limited 429: 0% — tidak ada yang diblok karena memang tidak ada rate limiter
http_reqs: 1026/s — throughput sangat tinggi tapi tidak terkontrol
can't assign requested address — sistem sampai kehabisan port TCP = resource exhaustion

verifyToken()
HMAC-SHA256 check