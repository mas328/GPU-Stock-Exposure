# Ornn data: what we have, and what we're asking for

## What we have (as of 2026-11-06)

The two Ornn files we have are website exports, and each has **one row**: the latest price only.

| File | GPU | Rows | Timestamp (UTC) | Index column |
|---|---|---|---|---|
| `ornn-price-history-h100-sxm-1m-365d-2026-10-15.csv` | H100 SXM | 1 | 2026-10-15 17:00 | H100 SXM hourly index (USD/GPU-hr) |
| `ornn-price-history-b200-1m-365d-2026-10-23.csv` | B200 | 1 | 2026-10-23 19:00 | B200 hourly index (USD/GPU-hr) |

The file names say "365d", so the export was supposed to cover a year, but it didn't. **We can't run any analysis until we get the full history.** `python ornn_audit.py` flags this automatically.

What we learned from the format, which the fake file now copies exactly:
`GPU, Timestamp (UTC), "<GPU> hourly index (USD/GPU-hr)"`, one file per GPU, timestamps in UTC to the hour.

## The request (draft for Prof. Bowen to send to Ornn; not sent yet)

> Hi, we're the FIN 331 team studying how GPU compute prices relate to stock returns. Could you send the full history of every Ornn price series you have, at daily frequency (or finer), going back as far as possible? Five years or more would be ideal. It's only a handful of series, so file size shouldn't be an issue.
>
> Specifically:
> 1. **Every GPU type** you track (A100, H100 SXM/PCIe, H200, B200, GB200, and others).
> 2. **Each contract type**: on-demand/rental vs. spot, and term contracts (1-month, 1-year, and so on) if you have them.
> 3. **Each region**, if prices differ by region.
> 4. **The time of day each daily price is set** (in UTC). We need this to line up with the 4pm ET stock close.
> 5. **Weekends and holidays**: are those real observations, or carried forward from the last weekday?
> 6. **How the index is built**: which providers it averages, and any method changes over time (structural breaks).
>
> The same CSV format as your website export is perfect (`GPU, Timestamp (UTC), <index>`), ideally with columns added for contract type and region. We'll keep the data private: it stays on our machines and never goes into our public repo.

## When it arrives

1. Put the files in `data/ornn/` (git-ignored, never committed).
2. Run `python ornn_audit.py`. It reports, for every series, the GPU, start and end dates, frequency, weekend and holiday coverage, and the share of days where the price is unchanged (carry-forward).
3. If Ornn's columns differ from the export format (for example, extra `region` or `term` columns), update `ornn.py`, **then** regenerate the fake file with `python make_fake_ornn.py` so the two match.
