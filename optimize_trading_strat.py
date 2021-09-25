# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 11:28:46 2021

Optimize the profit trading algo for the price data + signals

@author: sebas
"""



from scipy.optimize import curve_fit, differential_evolution, least_squares, dual_annealing, shgo, basinhopping, NonlinearConstraint, LinearConstraint
from all_functions import calc_profit_simple
import numpy as np
import time

imp_step = 60

fitlength = 60

optimization_range_upper_limit = 2400000 #lower limit is just 0. I typically use around 75% of my historical data for training.


folder = 'signals_flen' + str(fitlength)

data_comp = np.load('BTC-USD_historical_data_1min_complete.npy')

data_comp = data_comp[:,[0,1,2,4]]


test_range = range(optimization_range_upper_limit+1)

signals = np.load('Example_signal_A/' + folder + '/' + folder + '_range0_' + str(optimization_range_upper_limit) + '.npy')



def profit_fitter(x):
    
    profits, total_profits, sigs_w_close, balance_ext, positions, gains, losses, total_profits_aft_tax = calc_profit_simple(signals, data_comp, x[0], x[1])
    
    # Minimize the negative profit. I don't always use this metric as my "cost function," but this is the simplest option
    to_minimize = -total_profits_aft_tax
    
    return to_minimize




# Define bounds
bounds = [(0.003, 0.2),(1,50)] # calc_profit_simple


start = time.time()

# I often use differential evolution because my cost function has a ton of local minima
fit_coeffs = differential_evolution(profit_fitter, bounds, popsize=20, disp=True)


# Alternative minimization algorithms

# fit_coeffs = dual_annealing(profit_fitter, bounds, seed=1234)
# fit_coeffs = shgo(profit_fitter, bounds, iters=1)
# fit_coeffs = basinhopping(profit_fitter, [0.05, 0.05, 5])



best_value = fit_coeffs.x
best_profit = -fit_coeffs.fun

print(time.time()-start)

print(best_value)
print(best_profit)