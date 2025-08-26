import pandas as pd
import os
from datetime import datetime

class SalesProcessor:
    def __init__(self, base_path):
        #removes warning of filtering and replacing values
        pd.options.mode.chained_assignment = None
        self.base_path = base_path
        
    def pull_sales(self, sku_df):
        '''
        Creates a comprehensive sales df based on RICS sales data across different time frames
        '''
        self.clean_sales (sku_df)																	#CALLS FUNCTION - filters sales by date & adds custom entries
        self.unique_df = self.sales_df.drop_duplicates(['ID'])												#filters all the IDs down to unique IDs
        # unique_df.to_csv(filepath + 'Testing2.csv',index=False)
        self.sum_over_time('LAST 8')												#CALLS FUNCTION - finds the total sold over the last 8 weeks	
        self.sum_over_time('COMP 8')												#CALLS FUNCTION - finds the total sold over the comp 8 weeks
        self.sum_over_time('FUT 2')												#CALLS FUNCTION - finds the total sold over the fut 2 weeks
        self.sum_over_time('YEAR')												#CALLS FUNCTION - finds the total sold over the last year
        temp_df = self.sales_df[self.sales_df['WEEK NUM'] <= 52]												#filters the sales_df to the last 52 weeks
        temp_df = temp_df.loc[:,['ID', 'WEEK NUM', 'UNITS']]											#drops all irrelevant columns
        temp_df['UNITS'] = temp_df['UNITS'] * -1													#converts neg units from RICS to positive
        temp_df2 = temp_df.groupby(['ID', 'WEEK NUM'])												#filters the df into sales by week	
        temp_df2 = temp_df2.sum()																	#finds the sum units sold in by week & by ID
        temp_df2 = temp_df2.reset_index()															#un-filters the df into a normal df setup 
        temp_df2.drop(temp_df2.columns[[1]], axis = 1, inplace=True)								#deletes the week column
        max_df = temp_df2.groupby(['ID'])															#filters by ID
        max_df = max_df.max()																		#finds the max units sold in a week
        max_df = max_df.reset_index()																#un-filters the df into a normal df setup
        max_df.columns = ['ID', 'MAX WK SALES']														#renames columns for laster df merger
        self.unique_df = pd.merge(self.unique_df, max_df, on = 'ID', how = 'outer')							#adds time frame sales onto unique IDs
        self.unique_df['MAX WK SALES'].fillna(0, inplace=True)											#fills missing mapped data with zero
        self.unique_df.drop(self.unique_df.columns[[2,4,5,6,7,8,9,10]], axis=1, inplace=True)					#drops irrelevant columns
        #unique_df.to_csv(filepath + 'Z-Sales2.csv', index=False)									#saves sales_df to a file
        return self.unique_df

    # TODO: pass sku df as argument when initializing class?
    # both inventory and sales processors use the same function
    # repeats the exact same function invocation
    def clean_sales(self, sku_df):
        '''
        Loads and cleans RICS sales file
        '''
        self.sales_df = pd.read_csv(self.base_path + 'FW REPORTS\\INVENTORY DETAIL\\InventoryDetail.csv',usecols = ['Sku', 'InventoryStore', 'InventoryDate', \
            'GridColumn','Qty'], converters = {'Sku':str,'GridColumn':str, 'InventoryStore':str})
        self.sales_df.columns = ['SKU', 'STORE', 'DATE', 'SIZE', 'UNITS']
        dates_df = pd.DataFrame(self.sales_df['DATE'])
        dates_df = dates_df.drop_duplicates(['DATE'])
        dates_df['DATES ISO'] = pd.to_datetime(dates_df['DATE'])									# convert to datetime for easier comparison of dates and sorting
        dates_df = dates_df.sort_values(['DATES ISO'], ascending=False)								
        dates_df = dates_df.reset_index()															# resets the df's order so it stays new to old
        dates_df.drop(dates_df.columns[[0,2]], axis = 1, inplace=True)								# deletes the old index & python date format
        days_df = pd.read_csv(self.base_path + 'Brevity Stuff\\DATE_DB.csv')                        # Maps time tables (year, week, etc) to day indices using modulo math
        dates_df = pd.concat([dates_df, days_df], axis=1)											# maps the time tables with the correct dates
        dates_df = dates_df.dropna(subset = ['DAY NUM'])											# shrinks the df to only relevant dates	
        self.sales_df = pd.merge(self.sales_df, dates_df, on = 'DATE', how = 'outer')							# maps the time table df to the sales df
        self.sales_df = self.sales_df.dropna(subset = ['DAY NUM'])																
        self.sales_df = pd.merge(self.sales_df, sku_df, on = 'SKU', how = 'outer')							
        self.sales_df = self.sales_df.dropna(subset = ['UNITS'])												# drop products that don't have sales data	
        self.sales_df['PULL ID'] = (self.sales_df['SEX'].astype(str) + '-' + self.sales_df['ITEM'].astype(str) + '-' + \
            self.sales_df['SIZE'].astype(str))															
        self.sales_df['ID'] = (self.sales_df['STORE'].astype(str) + '-' + self.sales_df['PULL ID'].astype(str))	

    def sum_over_time(self, time):
        '''
        Calculates total units sold over given time frame
        '''
        temp_df = self.sales_df[self.sales_df[time] == 1]														#sets the df to specified time frame
        temp_df = temp_df.loc[:,['ID', 'UNITS']]														#drops all irrelevant columns
        sum_df = temp_df.groupby(['ID'])															#filters the df into sales by ID
        sum_df = sum_df.sum()																		#finds the sum of the ID sold in that time frame
        sum_df = sum_df.reset_index()																#un-filters the df into a normal df setup
        sum_df.columns = ['ID', time + ' SALES']			 										#renames columns for df merger
        self.unique_df = pd.merge(self.unique_df, sum_df, on = 'ID', how = 'outer')							#adds time frame sales onto unique IDs
        self.unique_df[time + ' SALES'] = self.unique_df[time + ' SALES'].fillna(0)											#fills missing mapped data with zero
        self.unique_df[time + ' SALES'] = self.unique_df[time + ' SALES'] * -1								#converts units from negative to positive
        return self.unique_df

    