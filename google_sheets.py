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
                            range="Sheet1!A1:F20").execute()
values = result.get('values', [])

# print(values)


df_crypto_balances = pd.DataFrame(values)
df_crypto_balances.columns = ['Name', 'symbol', 'Amount', 'Amount in BTC', 'Avg Price', 'Last Updated']

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
  
  crypto_tickers = ['CVC', 'LSK', 'OMG', 'BTC', 'ETH', 'NEO', 'ADA', 'OCEAN', 'DOT', 'TRAC', 'MRPH', 'BAL', 'ZRX'
                    'COMP', 'MKR', 'SNX', 'BNB', 'LINK', 'UNI', 'XMR', 'ALGO', 'UMA', 'REN', 'BAT', 'ONT'
                    , 'KNC', 'UBT', 'OMI', 'EWT', 'SOL', 'WPR', 'XLM', 'ATOM', 'XRP', 'EOS', 'MANA', 'STORJ', 'SC'
                    , 'VTX', 'DWZ', 'CAKE', 'PNT', 'CHART', 'BLANK', 'TRB', 'DVG', 'ALPA', 'PHA', 'KSM', 'BLES'
                    , 'GRC', 'SWAP', '1INCH', 'LRC', 'DVG', 'POLS', 'ROOK', 'MPH', 'TRB', 'BNT', 'GRT', 'VRA', 'ERN'
                    , 'BEPRO', 'MATIC', 'BCH', 'LUNA', 'SOL', 'KSM', 'RUNE']

  #df_short.crypto_tickers.isin(crypto_tickers)
  df_out = df_short[df_short['symbol'].isin(crypto_tickers)]
#  df_out.to_csv(r'coinmarketcap_api_v2.csv')
  df_out.columns = ['symbol', 'name', 'date_added', 'last_updated', 'price_usd', 'volume_24h', 'market_cap', 'percent_change_24h', 'percent_change_7d', 'percent_change_30d', 'percent_change_60d', 'percent_change_90d']
  #print(df_out)

except (ConnectionError, Timeout, TooManyRedirects) as e:
  print('except error: check code')


df_merged = pd.merge(df_crypto_balances, df_out, on = 'symbol', how = 'left')


#print(df_merged)

df_merged.to_csv(r'crypto_balances_api_test.csv')



