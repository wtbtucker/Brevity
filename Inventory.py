class Inventory:
    '''
    stores information about current inventory levels for quick lookup
    inventory = {
        "M-CUMULUS-10": {
            "1": {"197966046156": 10, "197968286628": 5},
            "8": {"197966046156": 2, "197968286635": 8}
        },
        "M-1080 (WIDE)-10": {
            "2": {"black": 20},
            "8": {"white": 15, "black": 3}
        }
    }
    '''
    def __init__(self, inventory: dict, upc_to_id: dict):
        self.inv = inventory
        self.upc_to_id = upc_to_id

    def get_colors(self, product_id: str, location: int) -> set[str]:
        '''
        Look up the colors currently in stock at a location for a particular product
        Will use to allocate colors not currently in stock to that location
        Args: 
            product_id: Gender, SKU, size eg. M-1080 (WIDE)-10
            location: integer store code eg. 5
        '''
        return set(self.inv[product_id][location].keys())


    def get_total_quantity(self, product_id: str, location: int) -> int:
        '''
        Check total quantity of a product available at a location
        Use for comparing store inventory levels to model stock
        Use for checking quantity available for distribution from the warehouse
        Args: 
            product_id: Gender, SKU, size eg. M-1080 (WIDE)-10
            location: integer store code eg. 5        
        '''
        return sum(list(self.inv[product_id][location].values()))

    def decrement_quantity(self, upc: str, location: int) -> None:
        '''
        Use to remove one item from warehouse inventory
        Args:
            upc: product barcode eg. 197966046156
            location: integer store code eg. 5    
        '''
        product_id = self.upc_to_id[upc]
        quantity = self.inv[product_id][location][upc]
        if quantity == 1:
            del self.inv[product_id][location][upc]
        else:
            self.inv[product_id][location][upc] = quantity - 1

    def increment_quantity(self, upc: str, location: int) -> None:
        '''
        Add one item to store inventory
        Args:
            upc: product barcode eg. 197966046156
            location: integer store code eg. 5               
        '''
        product_id = self.upc_to_id[upc]
        if upc in self.inv[product_id][location]:
            self.inv[product_id][location][upc] += 1
        else:
            self.inv[product_id][location][upc] = 1