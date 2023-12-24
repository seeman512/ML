import os
import logging
import requests
import pandas as pd


currencies_url = 'https://www.smartcurrencybusiness.com/wp-content/date.php'
food_prices_file = 'global_food_prices.csv'
out_file = 'usd_monthly_hist.csv'

logging.basicConfig(level=logging.INFO)


def load_currencies(from_date, to_date, from_currency, to_currency, tick):
    response = requests.get(
        currencies_url,
        params={'fd': f'01/01/{from_date}',
                'td': f'31/12/{to_date}',
                'sym': from_currency + to_currency,
                'tick': tick}
    )
    return response.json()


def currency_response_to_serires(response):
    data = []
    index = []

    for item in response:
        data.append(item['mid'])
        index.append(item['date'])

    return pd.Series(data, index=index)


def main():
    df = pd.read_csv(food_prices_file, low_memory=False)

    year_column = 'mp_year'
    min_year = df[year_column].min()
    max_year = df[year_column].max()

    currencies = list(df['cur_name'].unique())

    serires = {}

    for currency in currencies:
        if currency == 'USD':
            continue

        response = load_currencies(min_year, max_year, 'USD', currency, '1d')
        logging.info(f'Loaded {min_year}-{max_year}; {currency} '
                      + str(len(response)) + ' records')
        serires[currency] = currency_response_to_serires(response)

    df = pd.concat(serires, axis=1)
    df.to_csv(out_file)
    logging.info(f'Saved to {out_file}')


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(e)
