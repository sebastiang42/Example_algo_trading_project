# -*- coding: utf-8 -*-
"""
Created on Sat Sep 25 18:47:33 2021

Generate signals for when to go long/short.

@author: sebas
"""

import time
from joblib import Parallel, delayed
import numpy as np
import os
import math
from all_functions import signal_generator_function, generate_inputs, merge_signals



# Candle width in seconds
imp_step = 60

# Length (in candles) of data chunk to be input into the signal generator function each time it is run
fitlength = 720

# Import historical data
data_comp = np.load('BTC-USD_historical_data_' + str(int(imp_step/60)) + 'min_complete.npy')

data_comp = data_comp[:,[0,4]] # Keep only the times and close prices


''' Because some signal generators can take some time to run, I break up 
data_comp into subsections, run the signal generator on those subsections, and 
 recombine them at the end. That way, if something crashes while the code is 
 running, I don't have to rerun the signal generator for the completed 
 subsections '''
range_length = 100000
range_starts = [e*range_length for e in range(math.floor(len(data_comp)/range_length))]



start = time.time() # I like to time things

num_cores=16 # Number of CPU cores to use for running the code in parallel

for i in range_starts:
    
    folder = 'signals_flen' + str(fitlength) # Folder to save the generated signals in
    
    if not os.path.isfile('Example_signal_A/' + folder + '/' + folder + '_range' + str(i) + '_' + str(i+range_length) + '.npy'): # Check if this subsection has already been completed
        
        # Generate list of indices where the signal generator function will be run
        inputs = generate_inputs(data_comp, fitlength, i, range_length)
        
        # Create a parallel pool to run the signal generator function at every index in "inputs"
        processed_list = Parallel(n_jobs=num_cores)(delayed(signal_generator_function)(data_comp[j-fitlength:j,:]) for j in inputs)
        
        print(time.time()-start)
        
        np.save('Example_signal_A/test.npy',processed_list)
        
        processed_list= np.load('Example_signal_A/test.npy',allow_pickle=True)
        
        reduced_list = processed_list[processed_list!=None]
        
        np.save('Example_signal_A/test2.npy',reduced_list)
        
        signals = np.zeros((len(reduced_list),2))
        
        j = 0
        
        for row in reduced_list:
            signals[j,:] = np.array(row)
            signals[j,0] = np.where(data_comp[:,0]==signals[j,0])[0][0]
            j+=1
        
        if not os.path.isdir('Example_signal_A/' + folder):
            os.mkdir('Example_signal_A/' + folder)
            
        np.save('Example_signal_A/' + folder + '/' + folder + '_range' + str(i) + '_' + str(i+range_length) + '.npy', signals)


start_subsection = 0
end_subsection = math.floor(len(data_comp)/range_length)

merge_signals(fitlength, range_length, start_subsection, end_subsection) #merge the subsection signals together