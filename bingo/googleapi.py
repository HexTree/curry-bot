import gspread
from oauth2client.service_account import ServiceAccountCredentials


# create scope
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
# create some credential using that scope and content of json
creds = ServiceAccountCredentials.from_json_keyfile_name('bingo/creds.json', scope)


def get_sheet():
    spreadsheet = gspread.authorize(creds).open('Azure Dreams Bingo Goals')
    return spreadsheet.worksheet("cards")
