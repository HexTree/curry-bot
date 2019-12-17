import gspread
from oauth2client.service_account import ServiceAccountCredentials


# create scope
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
# create some credential using that scope and content of json


def get_sheet(creds_path, sheet_name):
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    spreadsheet = gspread.authorize(creds).open(sheet_name)
    return spreadsheet.worksheet("cards")
