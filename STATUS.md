# STATUS: Checkpoint 1 (Fri Oct 23)

**What we picked, and why.** We picked seed 15: *which stocks' share prices are most exposed to the cost of compute, and do GPU rental prices lead or lag stock returns?* It beat our other candidates for three reasons:
- It has a real reader. Ornn would use a "compute beta" for each firm to show its customers what GPU-price risk looks like in equities.
- It combines two course tools, L15-style betas and event-style lead-lag timing, on data almost no one has studied.
- It connects to work one of us does on datacenter and compute economics.

**Our proof of concept.** `python run_all.py` builds the firm × day panel for 5 firms, one or two per group: NVDA, MSFT, ORCL, PLTR, and KO as the control.
- Returns come from yfinance and the market factor and risk-free rate from Ken French's daily file. Both are real.
- The GPU column comes from `data/raw/ornn_FAKE.csv` until we get Ornn's data. That file has the columns we expect, with random numbers.
- Real sample rows are in `outputs/panel_sample_rows_FAKE_GPU.csv`.
- We checked the regression code by planting known compute betas in synthetic data (0.8, 0.5, 0.3, 0, 0). It recovered them: 0.80, 0.49, 0.31, 0.02, −0.02. Lead and lag coefficients stayed near zero, as they should.

What worried us:
- Ken French's daily factors stop 1–2 months before today, which cuts the end of our sample.
- CoreWeave and Nebius have short histories.
- We don't yet know when each day's GPU price is set, or what happens on weekends. For now, the GPU price for each trading day is the last one on or before that day, and weekend moves roll into Monday.

**Questions for you.**
1. Can you set up the Ornn data access? Which GPU models, regions, and rental terms (on-demand vs. term) does it cover, and back to what date?
2. What time of day is each daily price set, and are there weekend prices? This decides whether same-day betas are clean or partly look-ahead.
3. Is it OK to use SPY minus the T-bill rate as the market return, so we aren't limited by the French file's lag?
4. Should the 30 firms stay in four fixed groups, or can borderline firms (META, MSFT) be classified by revenue share?
