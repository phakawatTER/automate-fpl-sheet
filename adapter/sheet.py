import gspread
from gspread import Spreadsheet
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSheet:
    def __init__(self, credential: ServiceAccountCredentials):
        self.gc = gspread.authorize(credential)
        self.spreadsheet: Spreadsheet = None

    def open_sheet_by_url(self, url: str):
        spreadsheet = self.gc.open_by_url(url)
        self.spreadsheet = spreadsheet
        return self

    def open_worksheet_from_default_sheet(self, name: str):
        worksheet = self.spreadsheet.worksheet(name)
        return worksheet
