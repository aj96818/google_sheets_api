
# cd google_sheets_api
# source google_sheets_python_env/bin/activate

# Google Sheets API packages

from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from google.oauth2 import service_account


# CoinMarketCap API

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import pandas as pd



# https://console.cloud.google.com/apis/credentials?folder=&organizationId=&project=charismatic-fx-325016

SERVICE_ACCOUNT_FILE = 'google_sheets_keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


creds = None

creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)



# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1zkf3DJ9Yaod5u6WtnGcfiJmkbY5usnU5nqz4sWXZsD8'

# test_sheet = '1_rhVrmUqOd12YhA_vH-zqO6-po7ibC1INzzfGQ8_FkY'


service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API

sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range="Sheet1!A1:G43").execute()
values = result.get('values', [])

# print(values)


df_crypto_balances = pd.DataFrame(values)
df_crypto_balances.columns = ['Name', 'Symbol', 'Balance', 'Avg Price', 'Avg Total Cost', 'ATH', 'Location']

#print(df_crypto_balances)

# append_data = [["btc", 234.55], ["eth", 3456.43], ["ada", 44.32]]
# request = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Sheet1!A4", 
# 	valueInputOption = "USER_ENTERED", body = {"values":append_data}).execute()




# CoinMarketCap API

api_key = '231f04b7-44ce-4dcd-8dfd-0f0e0e1fbda4'

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
  'start':'1'
  , 'limit':'5000'
  , 'convert':'USD'
}

headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': api_key,
}

session = Session()
session.headers.update(headers)

try:
  response = session.get(url, params=parameters)
  json_text = json.loads(response.text)
  data = json_text['data']

  df = pd.json_normalize(data)

  df_short = df[['symbol', 'slug', 'date_added', 'last_updated', 'quote.USD.price', 'quote.USD.volume_24h', 'quote.USD.market_cap', 'quote.USD.percent_change_24h', 'quote.USD.percent_change_7d', 'quote.USD.percent_change_30d', 'quote.USD.percent_change_60d', 'quote.USD.percent_change_90d']]
  
  crypto_tickers = ['ZRX', '1INCH', 'AAVE', 'AMP', 'BAL', 'BAT', 'BNB', 'BTC', 'BCH', 'ADA',
					'LINK', 'CVC', 'ATOM', 'MANA', 'ETH', 'ICP', 'MIOTA', 'KLAY', 'KSM', 'KNC',
					'LUNA', 'XMR', 'ONT', 'OGN', 'CAKE', 'DOT', 'MATIC', 'REN', 'XRP', 'SOL',
					'XLM', 'GRT', 'THETA', 'RUNE', 'UNI', 'UBT', 'MRPH', 'LSK', 'NEO', 'OMI', 'DAG', 'TRAC']

  #df_short.crypto_tickers.isin(crypto_tickers)
  df_out = df_short[df_short['symbol'].isin(crypto_tickers)]
#  df_out.to_csv(r'coinmarketcap_api_v2.csv')
  df_out.columns = ['Symbol', 'name', 'date_added', 'last_updated', 'price_usd', 'volume_24h', 'market_cap', 'percent_change_24h', 'percent_change_7d', 'percent_change_30d', 'percent_change_60d', 'percent_change_90d']
  #print(df_out)

except (ConnectionError, Timeout, TooManyRedirects) as e:
  print('except error: check code')


df_merged = pd.merge(df_crypto_balances, df_out, on = 'Symbol', how = 'left')

#print(df_merged)

# exclude first row

df_merged = df_merged.iloc[1: , :]

# exclude the following 'names' from coinmktcap df: "luna-coin", "rune", "thorchain-erc20", "unicorn-token"

names_to_exclude = ["luna-coin", "golden-ratio-token", "rune", "thorchain-erc20", "unicorn-token"]
df_merged = df_merged[~df_merged.name.isin(names_to_exclude)]

df_merged[["price_usd", "Avg Price", "Avg Total Cost", "Balance", "ATH"]] = df_merged[["price_usd", "Avg Price", "Avg Total Cost", "Balance", "ATH"]].apply(pd.to_numeric)

df_merged["Avg_Pct_Return"] = ((df_merged["price_usd"] - df_merged["Avg Price"]) / df_merged["Avg Price"]) * 100
df_merged["Total Return"] = ((df_merged["price_usd"] * df_merged["Balance"]) - df_merged["Avg Total Cost"])
df_merged["Total Equity"] = df_merged["price_usd"] * df_merged["Balance"]
df_merged["Pct of ATH"] = df_merged["price_usd"] / df_merged["ATH"]


df_merged = df_merged.round(3)
df_merged = df_merged.sort_values(by=['Pct of ATH'], ascending = False)

cols = ['Name', 'Symbol', 'Avg Price', 'price_usd', 'ATH', 'Pct of ATH', 'Avg_Pct_Return','Balance','Avg Total Cost','Total Return', 'Total Equity', 'last_updated', 'volume_24h', 'market_cap', 'percent_change_24h', 'percent_change_7d', 'percent_change_30d', 'percent_change_60d', 'percent_change_90d']
df_merged = df_merged[cols]
# df_merged = df_merged.fillna('')

#df_merged.to_csv(r'crypto_balances_api_test_v13.csv')


# writing 'df_merged' to new Google Sheet using 'gspread' python package (pip install gspread & gspread_dataframe)

import gspread
from gspread_dataframe import set_with_dataframe

# ACCESS GOOGLE SHEET2
gc = gspread.service_account(filename='google_sheets_keys.json')
sh = gc.open_by_key('1zkf3DJ9Yaod5u6WtnGcfiJmkbY5usnU5nqz4sWXZsD8')
worksheet = sh.get_worksheet(1) #-> 0 - first sheet, 1 - second sheet etc. 

# CLEAR SHEET2 CONTENTS
range_of_cells = worksheet.range('A1:V1000') 
for cell in range_of_cells:
	cell.value = ''
worksheet.update_cells(range_of_cells) 

# APPEND DATA TO SHEET2
set_with_dataframe(worksheet, df_merged)
