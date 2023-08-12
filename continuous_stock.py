"""
Store the last 15 minutes of stock values for several companies.
Info is updated once per minute
"""

# Standard Library Imports
import asyncio
import os
from pathlib import Path
from datetime import datetime, timedelta
from random import randint

# External Library Imports
import pandas as pd
import yfinance as yf
from collections import deque

# Local imports
from util_logger import setup_logger
from fetch import fetch_from_url

# Set up logger
logger, log_filename = setup_logger(__file__)


# Takes company name string and returns stock ticker string
def lookup_ticker(company):
    stocks_dictionary = {
        "Tesla Inc": "TSLA",
        "Ford Motor Company": "F",
        "Ferrari": "RACE",
        "Honda Motor Co": "HMC",
        "General Motor Co": "GM",
        "Toyota Motor Corporation": "TM",
        "Microsoft Corp": "MSFT",
        "Amazon": "AMZN",
        "Apple": "AAPL",


    }
    ticker = stocks_dictionary[company]
    return ticker

# Asynchronous set up with ticker string and returning current stock price
async def get_stock_price(ticker):
    logger.info(f"Calling get_stock_price for {ticker}")
    stock_api_url = f'https://query1.finance.yahoo.com/v7/finance/options/{ticker}'
    logger.info(f"Calling fetch_from_url for {stock_api_url}")
    result = await fetch_from_url(stock_api_url, "json")
    logger.info(f'Data from yahoofinance: {result}')
    new_price = result.data['optionChain']['result'][0]['quote']['regularMarketPrice']
    # price = randint(132, 148)   # Use to test code without calling API
    return new_price

# Price to Book
async def get_daily_low(ticker):
    logger.info(f"Calling get_price_to_book for {ticker}")
    stock_api_url = f'https://query1.finance.yahoo.com/v7/finance/options/{ticker}'
    logger.info(f"Calling fetch from url for {stock_api_url}")
    result = await fetch_from_url(stock_api_url, "json")
    logger.info(f"Data from yahoofinance: {result}")
    daily_low = result.data["optionChain"]["result"][0]["quote"]["regularMarketDayLow"]
    return daily_low


# Create or overwrite CSV with column headings
def init_stock_csv_file(file_path):
    df_empty = pd.DataFrame(columns=["Company", "Ticker", "Time", "Price"])
    df_empty.to_csv(file_path, index=False)

# Writes new stock info to CSV
async def update_csv_stock():
    logger.info("Calling update_csv_stock")
    try:
        companies = [
            "Tesla Inc",
            "Ford Motor Company",
            "Ferrari",
            "Honda Motor Co",
            "General Motor Co",
            "Toyota Motor Corporation",
            "Microsoft Corp",
            "Amazon",
            "Apple"
        ]
        update_interval = 60  # Update every 1 minute (60 seconds)
        total_runtime = 15 * 60  # Total runtime maximum of 15 minutes
        num_updates = 50  # Keep the most recent 10 readings for each location
        logger.info(f"update_interval: {update_interval}")
        logger.info(f"total_runtime: {total_runtime}")
        logger.info(f"num_updates: {num_updates}")

        # Use a deque to store just the last, most recent 10 readings in order
        records_deque = deque(maxlen=num_updates)

        fp = Path(__file__).parent.joinpath("data").joinpath("mtcars_stock.csv")

        # Check if the file exists, if not, create it with only the column headings
        if not os.path.exists(fp):
            init_stock_csv_file(fp)

        logger.info(f"Initialized csv file at {fp}")

        for _ in range(num_updates):  # To get num_updates readings
            for company in companies:
                ticker = lookup_ticker(company)
                price = await get_stock_price(ticker)
                daily_low = await get_daily_low(ticker)
                time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time
                new_record = {
                    "Company": company,
                    "Ticker": ticker,
                    "Time": time_now,
                    "Price": price,
                    "Lowest_Price": daily_low, # adding price to book
                }
                records_deque.append(new_record)

            # Use the deque to make a DataFrame
            df = pd.DataFrame(records_deque)

            # Save the DataFrame to the CSV file, deleting its contents before writing
            df.to_csv(fp, index=False, mode="w")
            logger.info(f"Saving prices to {fp}")
             # Wait for update_interval seconds before the next reading
            await asyncio.sleep(update_interval)

    except Exception as e:
        logger.error(f"ERROR in update_csv_stock: {e}")
