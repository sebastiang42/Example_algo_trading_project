# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 13:37:05 2019

Download and clean historical price data from Coinbase Pro servers

@author: sebas
"""

from datetime import datetime, timedelta
from math import ceil
import numpy as np
import time
from all_functions import dl_historical_data, clean_historical_data


#------------------ IMPORT DATA ----------------------------------------------


# Choose the import step size (i.e., candle width), in seconds. Must be one 
# of {60, 300, 900, 3600, 21600, 86400} to be accepted by Coinbase servers
imp_step = 60 

# Choose the period length to download, in years
import_period = 7

# Choose a trading pair
trading_pair = 'BTC-USD'

# Filename to store imported data
filename = trading_pair + '_historical_data_' + str(int(imp_step/60)) + 'min_test.npy'

# Number of candles to be downloaded
N_steps = import_period*365*24*60*60/imp_step  

start = time.time()

# Coinbase servers return a maximum of 300 candles per request
if N_steps <= 300:  # if <300 steps are needed, everything can be imported with one request
    
    # start and end time for the request
    starttime = (datetime.now() - timedelta(seconds=imp_step*N_steps)).isoformat()
    endtime = datetime.now().isoformat()
    
    data = np.array(dl_historical_data(trading_pair, starttime, endtime, imp_step))
    
else:
    
    N_imports = ceil(N_steps/300) + 1  # number of requests needed to import all data
    timenow = datetime.now()
    
    for i in range(N_imports):
        
        # start and end time for the request
        starttime = (timenow - timedelta(seconds=imp_step*300*(i+1))).isoformat()
        endtime = (timenow - timedelta(seconds=imp_step*300*i)).isoformat()
        
        subdata = np.array(dl_historical_data(trading_pair, starttime, endtime, granularity=imp_step))
        
        if i == 0 and len(subdata)>0: # For first request, define data
            data = subdata
            
        elif len(subdata)>0: # Otherwise, add to existing data
            data = np.vstack((data, subdata))  # add data to total with each request
            
        time.sleep(0.6)  # pause between requests to avoid flooding Coinbase servers
        
        # Periodically report progress and save data imported so far
        if (i>0) and i % 100 == 0:
            np.save(filename,data)
            
            progress = 100*i/N_imports
            prog_time = time.time()
            print("{:.1f}".format(progress) + '% complete after ' + "{:.2f}".format(prog_time - start) + 
                  ' s. Estimated time remaining: ' + 
                  "{:.2f}".format((prog_time - start)*(100-progress)/progress) + ' s.')


#------------------ FILL IN MISSING ROWS -------------------------------------

# Coinbase apparently doesn't store candles with 0 volume, so this code fills 
# in the missing candles which have OLHC all equal to the previous candle's 
# close price, and 0 volume.

data_comp = clean_historical_data(filename)

np.save(trading_pair + '_historical_data_' + str(int(imp_step/60)) + 'min_complete.npy',data_comp)

