# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 20:48:14 2021

Plot the account balance over time for a given time period, set of signals, 
and trading strategy.

@author: sebas
"""

from all_functions import calc_profit_simple, calc_max_drawdown
import numpy as np
from datetime import datetime
import time
import matplotlib.pyplot as plt


imp_step = 60 # this is the timeframe to use

data_comp = np.load('BTC-USD_historical_data_' + str(int(imp_step/60)) + 'min_complete.npy')

data_comp = data_comp[:,[0,1,2,4]] # 0=time, 1=low, 2=high, 3=open, 4=close, 5=volume

dateconv = np.vectorize(datetime.fromtimestamp)


# ---------- input parameters for the signal generator ----------
fitlength = 60
range_start = 2400000
range_end = 3100000
range_length = range_end-range_start

best_params = [0,0] #input the parameters obtained during optimization for the given trading strategy and signal generator function


folder = 'signals_flen' + str(fitlength)

test_range = range(range_start,range_start+range_length+1)
plot_range = test_range

signals = np.load('Example_signal_A/' + folder + '/' + folder + '_range' + str(test_range[0]) + '_' + str(test_range[-1]) + '.npy')



start = time.time()

profits, total_profits, sigs_w_close, balance_ext, positions, gains, losses, total_profits_aft_tax = calc_profit_simple(signals, data_comp, best_params[0], best_params[1])

print(time.time() - start)


# Calculate the largest drawdown for the entire period, to be marked and labeled in the plot
largest_drawdown, largest_drawdown_index, min_index = calc_max_drawdown(balance_ext)


s = ['max drawdown = ' + str(round(largest_drawdown*1000)/10) + '%']

# Plot
fig = plt.figure(figsize=(24,12))
ax = fig.gca()

#plot account balance over time
plt.plot(dateconv(data_comp[balance_ext[:,0].astype(int),0]),data_comp[balance_ext[:,0].astype(int),3]/data_comp[balance_ext[0,0].astype(int),3], color=(12/255, 87/255, 168/255))

#plot the price data
plt.plot(dateconv(data_comp[balance_ext[:,0].astype(int),0]), balance_ext[:,1], color=(7/255, 172/255, 242/255))


#plot the signal opens and closes
if len(sigs_w_close[sigs_w_close[:,1]==1,0])>0:
    plt.plot(dateconv(data_comp[sigs_w_close[sigs_w_close[:,1]==1,0].astype(int),0]),data_comp[sigs_w_close[sigs_w_close[:,1]==1,0].astype(int),3]/data_comp[balance_ext[0,0].astype(int),3],'o', color=(8/255, 196/255, 27/255))
    plt.plot(dateconv(data_comp[sigs_w_close[sigs_w_close[:,1]==1,2].astype(int),0]),data_comp[sigs_w_close[sigs_w_close[:,1]==1,2].astype(int),3]/data_comp[balance_ext[0,0].astype(int),3],'x', color=(8/255, 196/255, 27/255))

if len(sigs_w_close[sigs_w_close[:,1]==-1,0])>0:
    plt.plot(dateconv(data_comp[sigs_w_close[sigs_w_close[:,1]==-1,0].astype(int),0]),data_comp[sigs_w_close[sigs_w_close[:,1]==-1,0].astype(int),3]/data_comp[balance_ext[0,0].astype(int),3],'ro')
    plt.plot(dateconv(data_comp[sigs_w_close[sigs_w_close[:,1]==-1,2].astype(int),0]),data_comp[sigs_w_close[sigs_w_close[:,1]==-1,2].astype(int),3]/data_comp[balance_ext[0,0].astype(int),3],'rx')

#mark the largest drawdown for the plotted period
dd = plt.plot(dateconv(data_comp[balance_ext[[largest_drawdown_index,min_index],0].astype(int),0]),balance_ext[[largest_drawdown_index,min_index],1], 'o', color=(12/255, 87/255, 168/255))

plt.yscale('log')

yrange = ax.get_ylim()

ax.legend(dd, s)



# Can create a second plot to study other metrics for a given trading strategy (long/short leverage over time, long/short average entry price spread)

if False:
    fig = plt.figure(figsize=(24,12))
    ax = fig.gca()
    
    if True:
        plt.plot(dateconv(data_comp[balance_ext[:,0].astype(int),0]), positions[:,0]/balance_ext[:,1], label='long leverage')
        plt.plot(dateconv(data_comp[balance_ext[:,0].astype(int),0]), positions[:,1]/balance_ext[:,1], label='short leverage')
        plt.plot(dateconv(data_comp[balance_ext[:,0].astype(int),0]), positions[:,2]/balance_ext[:,1], label='net leverage')
        plt.plot(dateconv(data_comp[balance_ext[:,0].astype(int),0]), positions[:,3]/balance_ext[:,1], label='total leverage')
    
    if False:
        plt.plot(dateconv(data_comp[balance_ext[:,0].astype(int),0]), (positions[:,5]-positions[:,4])/data_comp[int(signals[0,0]):,3], label='long/short entry spread')
        plt.ylim(-0.02,0.02)
        # plt.plot(dateconv(data_comp[balance_ext[:,0].astype(int),0]), positions[:,1]/balance_ext[:,1], label='short leverage')
    
    ax.legend()
