# -*- coding: utf-8 -*-
"""
Created on Sat Sep 25 14:36:11 2021

All functions needed for the various steps of the project are stored here.

@author: sebas
"""

import requests
import numpy as np



#----------------- Functions related to obtaining price data -----------------

def dl_historical_data(product_id, start_time, end_time, granularity):
    ''' Uses the Coinbase Pro API to import historical data'''
    
    time_data = {
            'start': start_time,
            'end': end_time,
            'granularity': granularity
    }
    response = requests.get('https://api.pro.coinbase.com/products/' + product_id + '/candles', params=time_data)
    
    # check for invalid api response
    if response.status_code != 200:
        raise Exception('Invalid Coinbase Status Code: %d' % response.status_code)
    
    return response.json()


def clean_historical_data(filename):
    ''' Fills in missing candles from the data imported using 
    dl_historical_data'''

    data = np.load(filename)
    data = np.flipud(data) # Put earliest candles at the top
    
    data_complete = np.copy(data)
    
    data_spacing = data[1:,0]-data[:-1,0]
    
    imp_step = np.min(data_spacing) # Desired candle width
    
    data_gaps = np.where(data_spacing>imp_step)[0] # Locate indices where gaps larger than imp_step appear
    
    offset = int(0)
    
    for i in range(len(data_gaps)):
        
        missing_rows = int(data_spacing[data_gaps[i]]/imp_step - 1)
        
        newrows = np.array([[data_complete[data_gaps[i]+offset,0]+imp_step, # time, low, high, open, close, volume
                         data_complete[data_gaps[i]+offset,4],
                         data_complete[data_gaps[i]+offset,4],
                         data_complete[data_gaps[i]+offset,4],
                         data_complete[data_gaps[i]+offset,4],
                         0]])
        
        if missing_rows>1: # If more than one candle is missing in a row
            
            for j in range(1,missing_rows):
                
                newrows = np.vstack([newrows,
                                  np.array([[newrows[j-1,0]+imp_step,
                                          newrows[j-1,1],
                                          newrows[j-1,2],
                                          newrows[j-1,3],
                                          newrows[j-1,4],
                                          newrows[j-1,5]]])])
        
        data_complete = np.insert(data_complete, data_gaps[i]+1+offset, newrows, 0)
        
        offset += missing_rows
        
        if i % 100 == 0:
            print("{:.1f}".format(100*i/len(data_gaps)) + '% complete')
    
    return data_complete



#------------ Functions related to generating and testing signals ------------



def signal_generator_function(data):
    ''' This is a dummy function that will just generate a random set of 
    signals throughout the time period covered by "data"'''
    
    # Generate random (approximate) number of trade signals over the period covered by data
    signals_length = np.random.randint(len(data))
    
    # Generate random times for trade signals to occur (as indices of data). 
    # Because randint can generate duplicates, this might be shorter than 
    # signals_length, but in this example it doesn't really matter.
    rand_ints = np.unique(np.sort(np.random.randint(0,len(data), size=signals_length)))
    
    # First column is index in data where the signal occurs, second column is 
    # the type of signal (1=increase long position, -1 = increase short position)
    signals = np.zeros((len(rand_ints),2)) 
    
    signals[:,0] = rand_ints
    
    rand_signs = np.random.randint(0,2, size = len(rand_ints))
    rand_signs[rand_signs==0]=-1
    
    signals[:,1] = rand_signs
    
    return signals


def generate_inputs(data_comp, fitlength, i, range_length):
    ''' This function produces a list of indices in data_comp where the 
    signal_generator function should be applied. It essentially filters out 
    long flat sections of data_comp that may lead to meaningless or unreliable 
    behavior from the signal generator function. These flat sections typically 
    correspond to times when the Coinbase servers went down.'''
    
    searchrange = range(i+1,i+range_length+1)
    
    currentlen = 1 #will track the length of the current flat section
    
    currentlenstart = searchrange[0] #used to make the start of the current flat section
    
    flats = np.empty((0,2)).astype(int)
    
    for p in searchrange:
        
        #Step through the search range, and if a candle close is identical to 
        #the previous candle's close, add one to the length of the current flat section
        if data_comp[p,1] == data_comp[p-1,1]:
            currentlen+=1
        
        #If the current close price differs from the previous candle's, check 
        #how long the current flat section is, and if it's too long 
        #(>fitlength/2), add that section to "flats"
        else:
            if currentlen>fitlength/2:
                flats = np.vstack((flats,[currentlenstart,currentlen]))
            currentlen = 1 #reset currentlen and currentlenstart after adding to flats
            currentlenstart = p
    
    #excepts is a list of indices marking places where the signal generator function will not be run
    excepts = list(range(fitlength))
    
    for k in range(len(flats)):
        excepts = excepts + list(range(flats[k,0],sum(flats[k,:])+fitlength))
    
    
    inputs = list(range(i,i+range_length)) #initialize inputs list as full range
    
    inputs = [x for x in inputs if x not in excepts] #remove exceptions
    
    return inputs


def merge_signals(fitlength, range_length, start_subsection, end_subsection):
    '''Merges the subsection signals from start_subsection to end_subsection '''
    
    total_signals = np.empty((0,3))
    
    
    folder = 'signals_flen' + str(fitlength)
    
    for i in [e*range_length for e in range(start_subsection,end_subsection)]:
        
        signals = np.load('Example_signal_A/' + folder + '/' + folder + '_range' + str(i) + '_' + str(i+range_length) + '.npy')
        
        total_signals = np.vstack((total_signals, signals))
    
    np.save('Example_signal_A/' + folder + '/' + folder + '_range' + str(start_subsection*range_length) + '_' + str(end_subsection*range_length) + '.npy',total_signals)



#------ Functions for testing trading strategies based on the signals --------



def calc_max_drawdown(balance_ext):
    
    """Takes in a balance_ext matrix and determines the largest drawdown over 
    the covered time period"""
    
    largest_drawdown = 0
    
    i = 0
    
    while i < len(balance_ext)-1:
        if balance_ext[i,1]>balance_ext[i+1,1]:
            drawdown_range_end = np.where(balance_ext[i+1:,1]>balance_ext[i,1])[0]
            if len(drawdown_range_end)>0:
                drawdown = 1-min(balance_ext[i+1:i+drawdown_range_end[0]+1,1])/balance_ext[i,1]
                
                if drawdown>largest_drawdown:
                    largest_drawdown = drawdown
                    largest_drawdown_index = i
                    min_index = np.argmin(balance_ext[i+1:i+drawdown_range_end[0]+1,1]) + i + 1
                i += drawdown_range_end[0]+1
            else:
                drawdown = 1-min(balance_ext[i+1:,1])/balance_ext[i,1]
                if drawdown>largest_drawdown:
                    largest_drawdown = drawdown
                    largest_drawdown_index = i
                    min_index = np.argmin(balance_ext[i+1:,1]) + i + 1
                break
        else:
            i+=1
    
    return largest_drawdown, largest_drawdown_index, min_index


def process_sigs(events, price_data, sigs_w_close, lev, lev_limit, slippage):
    
    """This piece takes over once 'events' has been generated, and calculates 
    gains, losses, balance over time, total profits before and after tax, etc. 
    
    events is a list of all events (increase/decrease long/short position, by how much, and when)
    
    price_data is just the historical price data
    
    sigs_with_close lists the signals when they occur, and when they later get closed
    
    lev is the leverage used each time a position is added to. it is a 
    percentage of the current total account balance
    
    lev_limit is the maximum total leverage (long + short) allowed. If 
    reacting to a given signal would cause lev_limit to be exceeded, then the 
    signal is ignored
    
    slippage is simply the estimated average slippage per order"""
    
    # balance_ext will list account balance at every minute for the entire period
    balance_ext = np.zeros((int(1+max(sigs_w_close[:,2]))-int(sigs_w_close[0,0]),2),dtype='float64')
    balance_ext[:,0] = range(int(sigs_w_close[0,0]),int(1+max(sigs_w_close[:,2])))
    balance_ext[:,1] = 1
    
    # will keep track of total gains and losses for calculating profit after taxes later
    gains = 0
    losses = 0
    
    total_profits = 1
    total_profits_aft_tax = 1
    
    # matrix that will keep track of positions over time
    positions = np.zeros((len(balance_ext),6)) # 0 long pos, 1 short pos, 2 net pos, 3 total pos, 4 long avg entry, 5 short avg entry
    
    chunk = 10000 #breaks everything up into smaller chunks to avoid many manipulations of large arrays. 10000 seems to be a generally good value
    offset = 0
    
    amounts = np.zeros((len(sigs_w_close),1))
    
    #indices marking the start of each chunk
    subs_starts = range(np.floor(events[0,0]/chunk).astype(int), np.ceil(events[-1,0]/chunk).astype(int))
    
    skipped_signals = np.zeros((len(sigs_w_close),1))
    
    for j in subs_starts:
        
        sub_events = events[np.logical_and(events[:,0]>=j*chunk, events[:,0]<(j+1)*chunk),:]
        sub_balance_ext = balance_ext[np.logical_and(balance_ext[:,0]>=j*chunk, balance_ext[:,0]<(j+1)*chunk),:]
        sub_positions = positions[np.logical_and(balance_ext[:,0]>=j*chunk, balance_ext[:,0]<(j+1)*chunk),:]
        sub_price_data = price_data[j*chunk:(j+1)*chunk,:]
        
        for i in range(len(sub_events)):
            
            update_ind = sub_events[i,0]-sub_balance_ext[0,0].astype(int) #current index within the current chunk
            
            if sub_events[i,1]==1: #increase long position size
                
                if sub_positions[update_ind,3]/sub_balance_ext[update_ind,1] + lev < lev_limit: #check if lev_limit will be exceeded
                    
                    amounts[sub_events[i,2]] = sub_balance_ext[update_ind,1]*lev
                    
                    if sub_positions[update_ind,0] == 0:
                        sub_positions[update_ind:,4] = sub_price_data[sub_events[i,0]-j*chunk,3]*(1+slippage)
                    else:
                        sub_positions[update_ind:,4] = (np.prod(sub_positions[update_ind,[0,4]]) + (1+slippage)*sub_price_data[sub_events[i,0]-j*chunk,3]*amounts[sub_events[i,2]])/(sub_positions[update_ind,0] + amounts[sub_events[i,2]])
                    
                    sub_positions[update_ind:,0] += amounts[sub_events[i,2]]
                    sub_balance_ext[update_ind:,1] -= amounts[sub_events[i,2]]*0.00075
                
                else:
                    skipped_signals[sub_events[i,2]] = 1
                
                
            elif sub_events[i,1]==-1: #increase short position size
                
                if sub_positions[update_ind,3]/sub_balance_ext[update_ind,1] + lev < lev_limit: #check if lev_limit will be exceeded
                    
                    amounts[sub_events[i,2]] = sub_balance_ext[update_ind,1]*lev
                    
                    if sub_positions[update_ind,1] == 0:
                        sub_positions[update_ind:,5] = sub_price_data[sub_events[i,0]-j*chunk,3]*(1-slippage)
                    else:
                        sub_positions[update_ind:,5] = (np.prod(sub_positions[update_ind,[1,5]]) - (1-slippage)*sub_price_data[sub_events[i,0]-j*chunk,3]*amounts[sub_events[i,2]])/(sub_positions[update_ind,1] - amounts[sub_events[i,2]])
                    
                    sub_positions[update_ind:,1] -= amounts[sub_events[i,2]]
                    sub_balance_ext[update_ind:,1] -= amounts[sub_events[i,2]]*0.00075
                    
                else:
                    skipped_signals[sub_events[i,2]] = 1
                
                
            elif sub_events[i,1]==2: #reduce long position size
                
                if skipped_signals[sub_events[i,2]] == 0:
                    
                    #includes taker fees at open and close (must remove opening 
                    #fee before adding to balance_ext, since it's already been 
                    #accounted for)
                    profit = ((sigs_w_close[sub_events[i,2],3]*(1-slippage)/sub_positions[update_ind,4])*(1-0.00075) - 0.00075 - 1)*amounts[sub_events[i,2],0]
                    
                    sub_positions[update_ind:,0] -= amounts[sub_events[i,2]]
                    
                    if sub_positions[update_ind,0] == 0:
                        sub_positions[update_ind:,4] = 0
                    elif sub_positions[update_ind,0] != 0 and abs(sub_positions[update_ind,0]/sub_balance_ext[update_ind,1]) < 0.000001: #catches rounding errors
                        sub_positions[update_ind:,4] = 0
                        sub_positions[update_ind:,0] = 0
                    
                    
                    sub_balance_ext[update_ind:,1] += profit + amounts[sub_events[i,2]]*0.00075
                    
                        
            elif sub_events[i,1]==-2: #reduce short position size
                
                if skipped_signals[sub_events[i,2]] == 0:
                    
                    #includes taker fees at open and close (must remove opening 
                    #fee before adding to balance_ext, since it's already been 
                    #accounted for)
                    profit = ((sub_positions[update_ind,5]*(1+slippage)/sigs_w_close[sub_events[i,2],3])*(1-0.00075) - 0.00075 - 1)*amounts[sub_events[i,2],0]
                    
                    sub_positions[update_ind:,1] += amounts[sub_events[i,2]]
                    
                    if sub_positions[update_ind,1] == 0:
                        sub_positions[update_ind:,5] = 0
                    elif sub_positions[update_ind,1] != 0 and abs(sub_positions[update_ind,1]/sub_balance_ext[update_ind,1]) < 0.000001:
                        sub_positions[update_ind:,5] = 0
                        sub_positions[update_ind:,1] = 0
                    
                    
                    sub_balance_ext[update_ind:,1] += profit + amounts[sub_events[i,2]]*0.00075
                    
            
            sub_positions[update_ind:,2] = sub_positions[update_ind:,0] + sub_positions[update_ind:,1]
            sub_positions[update_ind:,3] = sub_positions[update_ind:,0] - sub_positions[update_ind:,1]
            
            # if total leverage gets too high at any point, throw out the result
            if sub_positions[update_ind,3]/sub_balance_ext[update_ind,1]>95:
                print('Leverage too high')
                total_profits=0
                total_profits_aft_tax=0
                break
            
            # if balance gets too low, give up and stop
            if sub_balance_ext[update_ind,1] < 0.0001:
                print('Account drained')
                total_profits=0
                total_profits_aft_tax=0
                break
            
            # check for liquidations between current event and next event
            if i<len(sub_events)-1 and sub_events[i,0] != sub_events[i+1,0]:
                
                if sub_positions[update_ind,2]>sub_balance_ext[update_ind,1]: #long positions with leverage below 1 can't be liquidated
                    
                    liq_price = sub_positions[update_ind,4]*(1 - (sub_balance_ext[update_ind,1]/sub_positions[update_ind,2]))
                    
                    if sum(sub_price_data[sub_events[i,0]-j*chunk:sub_events[i+1,0]-j*chunk,1]<=liq_price)>0:
                        total_profits=0
                        total_profits_aft_tax=0
                        print('Long position liquidated')
                        break
                    
                    
                elif sub_positions[update_ind,2]<0: #short positions with leverage below 1 CAN be liquidated
                    
                    liq_price = sub_positions[update_ind,5]*(1 - (sub_balance_ext[update_ind,1]/sub_positions[update_ind,2]))
                    
                    if sum(sub_price_data[sub_events[i,0]-j*chunk:sub_events[i+1,0]-j*chunk,2]>=liq_price)>0:
                        total_profits=0
                        total_profits_aft_tax=0
                        print('Short position liquidated')
                        break
                    
            
        if total_profits == 0: #break out of the second for loop if any of the inner breaks get triggered (since they always set total_profits=0)
            break
        
        balance_ext[np.logical_and(balance_ext[:,0]>=j*chunk, balance_ext[:,0]<(j+1)*chunk),:] = sub_balance_ext
        positions[np.logical_and(balance_ext[:,0]>=j*chunk, balance_ext[:,0]<(j+1)*chunk),:] = sub_positions
        
        balance_ext[balance_ext[:,0]>=(j+1)*chunk,1] = sub_balance_ext[-1,1]
        positions[balance_ext[:,0]>=(j+1)*chunk,:] = sub_positions[-1,:]
        
        offset+=chunk
    
    # Sum up all events that generate gains and all events that generate losses. This is necessary to calculate profits after tax
    balance_changes = np.ones((len(balance_ext),1))
    balance_changes[0,0] = balance_ext[0,1]-1
    balance_changes[1:,0] = balance_ext[1:,1]-balance_ext[:-1,1]
    
    gains = sum(balance_changes[balance_changes>0])
    losses = sum(balance_changes[balance_changes<0])
    
    #Calculate profits before and after tax. Because of the way Swedish taxes 
    #work, one may only subtract 70% of ones losses from one's gains before 
    #calculating tax. This means, e.g., that one could "break even," but still 
    #end up owing tax. This is why it's incredibly important to use profits 
    #AFTER tax as a metric to judge trading algorithms
    total_profits = 1 + gains + losses
    total_profits_aft_tax = 1 + 0.7*gains + 0.79*losses 
        
    return total_profits, sigs_w_close, balance_ext, positions, gains, losses, total_profits_aft_tax, skipped_signals


def calc_profit_simple(signals, price_data, lev, lev_limit): 
    '''
    This is a simple example trading algorithm. In reality, the ones I end up 
    using are considerably more complicated (use stop losses, take profits, 
    moving stop losses, hedging, etc).
    
    Calculates profit very simply. At a buy trigger, either adds 'lev' leverage 
    to an open long position, or closes an open short position and opens a 'lev' 
    long position. Vice versa for a sell trigger. No hedging, i.e., long and 
    short positions are never open at the same time. 

    Parameters
    ----------
    signals : numpy array
        column 0: index in the price_data where the trigger occurs
        column 1: trigger type. 1 is a buy trigger and -1 is a sell trigger
    price_data : numpy array
        column 0: time
        column 1: low price
        column 2: high price
        column 3: close price
    lev : float
        amount of leverage to add per trigger. 1 = 1x
    
    -------
    None.

    '''
    
    # can set average slippage manually (as a percentage)
    slippage = 0.00
    
    
    # convert signals to int to use the first column as indices
    signals = signals.astype(int)
    
    sig_flips = np.nonzero(signals[1:,1]-signals[:-1,1])[0]+1
    
    pos_flips = signals[sig_flips[0],0]*np.ones((len(signals)))
    for j in range(1,len(sig_flips)):
        pos_flips[sig_flips[j-1]:sig_flips[j]] = signals[sig_flips[j],0]
    
    # pos_flips[sig_flips[j]:] = len(price_data)-1
    pos_flips = pos_flips.astype(int)
    
    pos_flips = pos_flips[:sig_flips[j]]
    signals = signals[:sig_flips[j]]
    
    
    # new array, same as signals, plus an extra column listing when each 
    # position is closed
    sigs_w_close = np.zeros((len(signals),4),dtype='float64')
    sigs_w_close[:,0] = signals[:,0]
    sigs_w_close[:,1] = signals[:,1]
    
    profits = np.ones((len(signals),1))
    
    for i in range(len(signals)):
        current_price = price_data[signals[i,0],3]
        
        if np.sign(signals[i,1])==1:
            TP_pct = price_data[pos_flips[i],3]/current_price - 1
            
        elif np.sign(signals[i,1])==-1:
            TP_pct = 1 - price_data[pos_flips[i],3]/current_price
        
        profits[i] = 1 + (TP_pct*(1-0.00075*lev) - 0.0015 - slippage)*lev
        sigs_w_close[i,2] = pos_flips[i]
        sigs_w_close[i,3] = price_data[pos_flips[i],3]
    
    
    # put all opens and closes into a single list. 0: index in price_data when 
    # it takes place, 1: indicates whether it's open long/short (+/-1) or 
    # close long/short (+/-2), 2: row number in sigs_w_close where the event 
    # came from
    events = np.zeros((2*len(sigs_w_close),3))
    
    events[:len(sigs_w_close),:2] = sigs_w_close[:,:2]
    events[:len(sigs_w_close),2] = range(len(sigs_w_close))
    events[len(sigs_w_close):,0] = sigs_w_close[:,2]
    events[len(sigs_w_close):,1] = 2*sigs_w_close[:,1]
    events[len(sigs_w_close):,2] = range(len(sigs_w_close))
    
    #sort by when they occur
    events = events[np.lexsort((events[:,2],events[:,0])),:].astype(int)
    
    # keep track of individual additions to positions
    # amounts = np.zeros((len(sigs_w_close),1))
    
    
    if np.any(profits<0):
        total_profits=0
        total_profits_aft_tax=0
        balance_ext = 0
        positions = 0
    else:
        
        total_profits, sigs_w_close, balance_ext, positions, gains, losses, total_profits_aft_tax, skipped_signals = process_sigs(events, price_data, sigs_w_close, lev, lev_limit)
        
    
    if total_profits != 0:
        print('profit BT: ' + str(round(total_profits,4)) + ', profit AT: ' + str(round(total_profits_aft_tax,4)) + ', params: [' + str(round(lev,8)) + ']')
    
    return profits, total_profits, sigs_w_close, balance_ext, positions, gains, losses, total_profits_aft_tax