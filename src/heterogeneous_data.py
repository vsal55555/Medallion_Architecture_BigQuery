import pandas as pd
import numpy as np

np.random.seed(42)
n = 10000
temp = np.random.uniform(15, 35, n)
weekdays = np.random.randint(0, 7, n)
cost = np.random.uniform(1.0, 3.0, n)
price = np.random.uniform(4, 10, n)

sales = (50 + 1.5 * temp - 2.75 * price + 0.1 * (temp - 25) * price - 0.5 * cost + np.random.normal(0, 5, n))

df = pd.DataFrame({
    'temperature': np.round(temp, 2),
    'weekdays': weekdays,
    'cost': np.round(cost, 2),
    'price': np.round(price, 2),
    'sales': np.round(sales, 2)
})
df.to_csv('synthetic_ice_cream_data.csv', index=False)