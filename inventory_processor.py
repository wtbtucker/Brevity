import pandas as pd
import os
from Inventory import Inventory

class InventoryProcessor:
    def __init__(self, base_path):
        self.base_path = base_path

    def load_inventory(self):
        onhand_df = self._load_onhand()
        in_transit_df = self._load_in_transit()
        self.inv_df = pd.concat([onhand_df, in_transit_df])
        self.inv_df = self.inv_df.dropna(subset = ['INV'])

    def add_keyword(self, sku_df):
        '''
        Adds RICS keyword eg "KAYANO" to the inventory dataframe
        '''
        self.inv_df = pd.merge(self.inv_df, sku_df, on = 'SKU', how = 'outer')
        self.inv_df.dropna(subset=['INV'], inplace=True)
        self.inv_df['PULL ID'] = (self.inv_df['SEX'].astype(str) + '-' + self.inv_df['ITEM'].astype(str) + '-' + \
            self.inv_df['SIZE'].astype(str))     

    def add_upc(self):
        upc_df = pd.read_csv(self.base_path + 'FW Reports\\UPC List\\UPCList.csv', usecols=['SKU', 'UPC', 'COL'], encoding='utf_8_sig', dtype=str)
        upc_df.drop_duplicates(subset=['UPC'], inplace=True)
        self.inv_df = pd.merge(upc_df, self.inv_df, how='right', left_on=['SKU', 'COL'], right_on=['SKU', 'SIZE'])      
    
    # load dataframe of onhand items from RICS stock status report
    def _load_onhand(self):
        ss_df = pd.read_csv(self.base_path + 'FW REPORTS\\STOCK STATUS\\StockStatus.csv', usecols=['StoreCode', 'SKU', 'COL', 'OnHand'], encoding='utf_8_sig',\
            converters={'StoreCode':str, 'SKU':str, 'COL':str})
        ss_df.columns = ['STORE', 'SKU', 'SIZE', 'INV']	
        return ss_df
        
    def _load_in_transit(self):
        raw_rit_df = pd.read_csv(self.base_path + 'FW REPORTS\\STOCK STATUS\\in-transit.csv', usecols=['Sku', 'GridColumn', 'InventoryType', 'Qty', 'Comment'],\
            converters={'SKU':str, 'GridColumn':str, 'Qty':int})									#create raw RIT (RICS in transit) 
        raw_rit_df = raw_rit_df[raw_rit_df['Comment'].str.contains("SD")]							#filters RIT to only stock drops
        if(len(raw_rit_df.index))==0:
            rit_df = pd.DataFrame(columns = ['STORE','SKU','SIZE','INV'])
        else:
            temp_df = raw_rit_df[raw_rit_df['InventoryType'] == 'Transfer Out']							#sets the df to only RIT out bound transfers
            tran_out_df = temp_df.groupby(['InventoryType','Comment'])									#filters the df by TO# 
            tran_out_df = tran_out_df.sum()																#sums the out bound product by TO#
            tran_out_df = tran_out_df.reset_index()														#un-filters the df into a normal df setup	
            tran_out_df.drop(tran_out_df.columns[[0]], axis = 1, inplace=True)							#deletes old index
            rit_df = raw_rit_df.groupby(['Comment'])													#filters RIT by TO# (in AND out bound)
            rit_df = rit_df.sum()																		#sums the in AND out bound  product by TO#
            rit_df = rit_df.reset_index()																#un-filters the df into a normal df setup	
            rit_df = pd.merge(rit_df, tran_out_df, on = 'Comment', how = 'outer')						#creates a df by TO# which has trans out & (trans in - trans out )
            rit_df['ADD'] = rit_df['Qty_x'] - rit_df['Qty_y']											#creates a column which adds trans out to (trans in - trans out )
            rit_df = rit_df[rit_df['ADD'] == 0]															#filters the df down to only unreceived TO's
            rit_df = pd.merge(rit_df, raw_rit_df, on = 'Comment', how = 'inner')						#filters down the raw RIT df to only unreceived TO's
            store_df = pd.read_csv(self.base_path + 'Brevity Stuff\\STORES.csv', converters={'STORE':str})																#CALLS FUNCTION - creates a df w/ store name AND #
            rit_df['SHORT'] = rit_df['Comment'].str[7:11]												#finds the store name from the TO#
            rit_df = pd.merge(rit_df, store_df, on = 'SHORT', how = 'inner')							#merges df's thus adding store # to the RIT df
            rit_df = rit_df.loc[:,['STORE', 'Sku', 'GridColumn', 'Qty']]									#drops all irrelevant columns
            rit_df.columns = ['STORE', 'SKU', 'SIZE', 'INV']											#renames the columns
            rit_df['INV'] = rit_df['INV'] * -1															#makes the negative inv positive
        return rit_df

    def clean_inventory(self) -> Inventory:
        '''
        Transform dataframe into dictionary datastructure for faster operations
        '''
        inventory = {}
        upc_to_id = {}
        for _, row in self.inv_df.iterrows():
            id_ = row["PULL ID"]
            store = int(row["STORE"])
            upc = row["UPC"]
            inv = int(row["INV"])
            inventory.setdefault(id_, {}).setdefault(store, {})[upc] = inv
            upc_to_id[upc] = id_

        return Inventory(inventory, upc_to_id)