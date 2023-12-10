import gspread
from gspread import Spreadsheet,Worksheet
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheet:
    def __init__(self,credentials_path:str):
        # Connect to Google Sheets API using credentials
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        self.gc = gspread.authorize(credentials)
        self.spreadsheet:Spreadsheet = None
        
    def open_sheet_by_url(self,spreadsheet_name:str):
        spreadsheet = self.gc.open_by_url(spreadsheet_name)
        self.spreadsheet = spreadsheet
        return self
    
    def open_worksheet_from_default_sheet(self,name:str):
        worksheet = self.spreadsheet.worksheet(name)
        return worksheet
    
if __name__ == "__main__":
    game_week = 1
    # TODO: update Google Sheet
    sheet = GoogleSheet("./service_account.json")
    sheet = sheet.open_sheet_by_url("https://docs.google.com/spreadsheets/d/1eciOdiGItEkml98jVLyXysGMtpMa06hbiTTJ40lztw4/edit#gid=1315457538")
    worksheet = sheet.open_worksheet_from_default_sheet("Sheet3")
    # Define the starting column index
    start_column_index = 4  # Column D
    for i in range(0,38):
        next_col = 4 + (3*i)
        worksheet.update_cell(4,next_col,999)
    
