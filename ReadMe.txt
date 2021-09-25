This is an example project for developing a cryptocurrency algorithm. I have not included any details corresponding to actual algorithms that I use for trading, but these files should provide most of the framework needed for the full process, from downloading historical price data to plotting the account balance over time produced by a given trading algorithm. The included files are:

all_functions.py: This contains all the functions used in the other files.

historical_data_importer.py: This script is used to import and "clean" the historical price data for a desired time period and currency pair (e.g., BTC-USD).

generate_signals.py: This script is used for creating a list of signals over the full time period for a given signal generator algorithm that you would like to backtest.

optimize_trading_strat.py: This script takes the list of signals, and optimizes a trading strategy that you would like to test for that set of signals, for a chosen time period.

plot_profits.py: This script can be used to calculate and plot the profits over time generated using a given trading strategy and set of signals.