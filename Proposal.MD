# Proposal: Tracking Correlation Between GPU Rental Prices and Stock Returns

By Drew Hetzer, Matt Stugart, Cullen Kingston

## Research Question

To find out if stock returns respond to GPU rental prices, we propose the following question:

**Do GPU rental prices and stock returns move together on the same day?**

We would also like to answer these specific questions.

- Do changes in compute prices lead or lag changes in stocks?
- Which companies' share prices are most exposed to the cost of compute?

## Data Set

The unit of observation is a firm-day. It is one stock to one trading day. The date range is from December 12th 2023, to November 5th, 2026. Each row has the stock's daily return, excess market return, risk-free rate, excess return, and GPU rental prices from ORNN.

We included 10 tech stocks to identify correlations. On the buy side, we used META and ABDE. On the sell side, we used NVDA, AMD, IREN, and ORCL. We used two power and data center stocks (VST and VRT) and two controls with no compute exposure (KO, PG).

The must-have variables are the stock returns, the risk-free rate, excess market return, and GPU prices. The stock prices are adjusted closing prices from Yahoo Finance. Excess market return and risk-free rate come from the Ken French Data Library.

## The Method

We examine whether changes in GPU rental prices are associated with stock returns and whether this relationship differs across compute suppliers, buyers, infrastructure companies, and comparable firms.

Our pipeline has four main steps:

1. **Prepping the Data:** Use the data-processing script (`poc.py`) to calculate the adjusted stock returns and combine them with the GPU price changes, market returns, and the risk-free rate. We use actual trading-day stock returns and align the GPU price changes to the same intervals. This incorporates weekend GPU movements into the next trading-day observation. Then, it replaces the current fake GPU data with the real Ornn data before coming to conclusions.

2. **Estimate Stock Exposure:** Run a separate regression for each stock to measure its relationship against each GPU rental-price index, controlling for market movements. Then compare the results across suppliers, buyers, infrastructure companies, and the ten comparison firms.

3. **Explore Relationships:** Create price charts, scatterplots, and daily, five-day, and rolling correlations across the six GPU indexes. Use lead-lag analysis to explore whether GPU price changes precede or follow stock returns. These analyses identify associations rather than establish causation.

4. **Reproduce and Present:** Use the pipeline runner (`run_all.py`) to regenerate the analysis tables and figures, then display the results in the Streamlit dashboard.

## Threats and checks

**Threat: GPU public data exposure**
- **Reason:** Ornn requested that the data remain private.
- **Check:** Created fake GPU data that copied the rows and columns of the real data to prevent public exposure.

**Threat: Alternative sources cause GPU price movement**
- **Reason:** AI news, such as earnings or model launches, can move both GPU prices and AI stocks.
- **Check:** Add more controls such as the Fama-French factors or a semiconductor index and compare the betas.

**Threat: Merges**
- **Reason:** Rows could be silently dropped or duplicated when joining returns, Ken French factors, and GPU pricing.
- **Check:** Print the row count before and after each merge. List any dropped dates and the reason for each.

## Dashboard Mockup

Our GPU Stock Exposure dashboard will help users explore the relationship between GPU rental changes and stock returns through our four tabs:

- **Introduction:** Presents the research question, the 10 companies studied, and a summary of the available data.
- **Methodology:** Explains the data sources, how GPU prices are aligned with stock trading days, and the regression used to estimate each stock's exposure to GPU price change.
- **Results:** Displays regression estimates, computes betas with 95% confidence intervals, and lead-lag correlations to compare relationships across companies.
- **Explore:** An interactive page that allows users to select stocks, adjust the date range and lag window, and switch between normalized price charts, scatter plots, lead-lag comparisons, regression estimates, and underlying data.

The website layout allows users to move from understanding the research question to examining results and exploring individual companies. The current version uses fake GPU prices, so the displayed relationships are illustrative. The placeholders will be replaced with real Ornn data.

*(The mockup screenshots in the original PDF are not included here.)*

## Bibliography

Bowen, Donald. "9.5. Estimating Better Models." *LeDataSciFi-2025*, 2025, ledatascifi.github.io/ledatascifi-2025/content/05/05c_factorloadings.html.

French, Kenneth R. "Data Library." *Kenneth R. French*, Tuck School of Business at Dartmouth, mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html.

"Microsoft Corporation (MSFT) Stock Price." *Yahoo! Finance*, yahoo.com.

Streamlit Inc. *Streamlit*. Streamlit Inc., streamlit.io.
