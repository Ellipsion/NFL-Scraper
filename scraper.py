import os
import datetime
import json
from pyshell_msg.shell import Shell
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

BASE_URL = "https://www.nfl.com/stats/team-stats/{tab}/{sub_tab}/{year}/reg/all"
DATE = str(datetime.date.today())

TABS = {
    'offense': ['passing', 'rushing', 'receiving', 'scoring', 'downs'],
    'defense': ['passing', 'rushing', 'receiving', 'scoring', 'tackles', 'downs', 'fumbles', 'interceptions'],
    'special-teams': ['field-goals', 'scoring', 'kickoffs', 'kickoff-returns', 'punting', 'punt-returns']
}


MY_SHELL = Shell("NFL")

def format_data(_string):
    '''Format the raw data'''

    for i in _string:
        if i == ' ':
            _string = _string.replace(' ','')
        if i == '\n':
            _string = _string.replace('\n', '')
    return _string

def numeric_only(_string):
    numeric = ''
    for i in _string:
        if i.isdigit() or i == '.':
            numeric += i
    return numeric

def get_request_data(url):
    '''Get a request from the url and returns a BS4 object.'''
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, features='html.parser')
            return soup
        else:
            MY_SHELL.message("ERROR! Can't fetch URL... error code: ", response.status_code)
            exit()
    except (requests.ConnectionError, requests.Timeout) as exception:
        MY_SHELL.message("ERROR! No internet connection.", 'CONNECTION ERROR!')
        exit()

    

def data_scrapper(soup, data_base):
    '''Find useful data from BS4 Object'''
    DATA_BASE = data_base

    if soup != None:
        _table = soup.find('table')
        thead = _table.find('thead').find('tr').find_all('th')
        table_rows = _table.find('tbody').find_all('tr')

        table_head = []
        for cell in thead:
            th = format_data(str(cell.text))
            table_head.append(th)
        DATA_BASE['table-head'].extend(table_head[1:])

        for row in table_rows:
            cell_list = []
            num_cell_list = []
            final_cell_list = []
            cells = row.find_all('td')
            for cell in cells:
                div_list = cell.find_all('div')
                if len(div_list) > 0:
                    div_list = div_list[0]
                    sub_divs_list = div_list.find_all('div')
                    div = sub_divs_list[1]
                    cell_data = format_data(str(div.text))
                else:
                    cell_data = format_data(str(cell.text))
                cell_list.append(cell_data)
            
            for cell in cell_list[1:]:
                cell = numeric_only(cell)
                num_cell_list.append(cell)
            
            final_cell_list = cell_list[:1]
            final_cell_list.extend(num_cell_list)

            key = final_cell_list[0]
            if key in DATA_BASE:
                DATA_BASE[key].extend(final_cell_list[1:])
            else:
                DATA_BASE[key] = final_cell_list

        return DATA_BASE

    else:
        print("Error! Can't process NoneType object")

            
def excel_render(data, year, date=''):
    '''Render given data to new Excel Document in same directory'''
    if len(str(date)) > 0:
        file = "NFL-{}".format(date)
    else:
        file = "NFLbeta-{}".format(year)
    
    extension = ".xlsx"

    if os.path.exists(file+extension):
        file += "(1)"
    
    file += extension

    MY_SHELL.message("initializing Excel render", file)
    wb = Workbook(file)
    sheet = wb.create_sheet(str(year))
    for i in data:
        row = data[i]
        sheet.append(row)
    wb.save(filename=file)
    wb.close()

    MY_SHELL.message("SUCCESS")


def flow_controller(year, date=''):
    '''Controls Url kwargs and flow of program'''

    MY_SHELL.message("Initializing...")
    MY_SHELL.message("YEAR", year)

    data_base = {
        'table-head': ['Team', ],
    }


    for tab in TABS:
        MY_SHELL.message("collecting TAB", tab.upper())
        sub_tabs = TABS[tab]
        for sub_tab in sub_tabs:
            MY_SHELL.message("collecting subtab", sub_tab)
            url = BASE_URL.format(tab=tab, sub_tab=sub_tab, year=year)
            soup = get_request_data(url)
            data_base = data_scrapper(soup, data_base)

    counter = {'rows': len(data_base), 'columns': len(data_base['table-head'])}
    MY_SHELL.message("Data Collected", "{} rows, {} columns".format(counter['rows'], counter['columns']))
    excel_render(data_base, year, date)

def all_year_data():
    ''' 
    Scrape data for all the years into new Excel files.
    For ex. NFL-2002.xlsx
    '''

    for year in range(1970, 2022):
        flow_controller(year)

def update_2021_data():
    ''' 
    Scrape 2021 stats to new Excel File
    and name it with current date
    '''
    flow_controller(2021, DATE)

def specific_year_data(year):
    '''
    Scrape data for a specific year.
    '''
    flow_controller(year)

if __name__ == "__main__":
    # run these functions
    update_2021_data()
    # all_year_data()
    # specific_year_data(2021)
