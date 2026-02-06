import json

# Gold Data from BCRP (Monthly)
with open(r'C:\Users\User\.gemini\antigravity\brain\3ea0eb1e-c5a2-4e74-bf36-badef1a4ab7e\.system_generated\steps\58\output.txt', 'r') as f:
    gold_monthly = json.load(f)

# Deforestation Area from WB (Annual)
forest_area = {
    "2006": 745490.12, "2007": 744242.09, "2008": 742994.06, "2009": 741746.03, "2010": 740498.0,
    "2011": 738787.46, "2012": 737076.92, "2013": 735366.38, "2014": 733655.84, "2015": 731945.3,
    "2016": 730102.8, "2017": 728347.8, "2018": 726760.4, "2019": 725032.0, "2020": 723303.7,
    "2021": 721575.333, "2022": 719847.011, "2023": 718118.659
}

# Aggregate Gold to Annual
gold_annual = {}
for entry in gold_monthly:
    # time format: "Ene.2006"
    year = entry['time'].split('.')[1]
    val = entry['PN01654XM']
    if year not in gold_annual:
        gold_annual[year] = []
    gold_annual[year].append(val)

gold_avg = {y: sum(vals)/len(vals) for y, vals in gold_annual.items()}

# Calculate Annual Deforestation (Loss)
# Loss(t) = Area(t-1) - Area(t)
loss_annual = {}
years = sorted(forest_area.keys())
for i in range(1, len(years)):
    curr = years[i]
    prev = years[i-1]
    loss_annual[curr] = forest_area[prev] - forest_area[curr]

# Combine for Correlation
combined = []
print("Year | Gold Price | Forest Loss (sq km)")
print("-----|------------|-------------------")
for year in sorted(loss_annual.keys()):
    if year in gold_avg:
        combined.append((gold_avg[year], loss_annual[year]))
        print(f"{year} | {gold_avg[year]:.2f} | {loss_annual[year]:.2f}")

# Simple Correlation Calculation
def correlation(x, y):
    n = len(x)
    mu_x = sum(x)/n
    mu_y = sum(y)/n
    num = sum((xi - mu_x) * (yi - mu_y) for xi, yi in zip(x, y))
    den = (sum((xi - mu_x)**2 for xi in x) * sum((yi - mu_y)**2 for yi in y))**0.5
    return num/den if den != 0 else 0

prices = [c[0] for c in combined]
losses = [c[1] for c in combined]
corr = correlation(prices, losses)

# Normalize for Chart (0-100)
# Gold
max_gold = max(prices)
norm_gold = {year: (val/max_gold)*100 for year, val in gold_avg.items() if year in loss_annual}
# Loss
max_loss = max(losses)
norm_loss = {year: (val/max_loss)*100 for year, val in loss_annual.items()}

chart_data = [
    {"REF_AREA": "PER", "INDICATOR": "Precio Oro (Normalizado)", **{y: round(v, 2) for y, v in norm_gold.items()}},
    {"REF_AREA": "PER", "INDICATOR": "Perdida Forestal (Normalizada)", **{y: round(v, 2) for y, v in norm_loss.items()}}
]

with open('chart_data.json', 'w') as f:
    json.dump(chart_data, f)

print("\nChart data saved to chart_data.json")
