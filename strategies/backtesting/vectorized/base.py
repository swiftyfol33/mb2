import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brute


class VectorizedBacktester:
    """ Class for the vectorized backtesting of SMA-based trading strategies.

    Attributes
    ==========
    symbol: str
        ticker symbol with which to work with
    SMA_S: int
        time window in days for shorter SMA
    SMA_L: int
        time window in days for longer SMA
    start: str
        start date for data retrieval
    end: str
        end date for data retrieval


    Methods
    =======
    get_data:
        retrieves and prepares the data

    set_parameters:
        sets one or two new SMA parameters

    test_strategy:
        runs the backtest for the SMA-based strategy

    plot_results:
        plots the performance of the strategy compared to buy and hold

    update_and_run:
        updates SMA parameters and returns the negative absolute performance (for minimization algorithm)

    optimize_parameters:
        implements a brute force optimization for the two SMA parameters
    """

    def __init__(self, data, symbol, trading_costs=0, price_col='close', returns_col='returns'):
        self.data = data.copy()
        self.tc = trading_costs / 100
        self.symbol = symbol
        self.price_col = price_col
        self.returns_col = returns_col
        self.results = None

    def _calculate_returns(self):
        self.data[self.returns_col] = np.log(self.data[self.price_col] / self.data[self.price_col].shift(1))

    def _update_data(self):
        """ Retrieves and prepares the data.
        """
        self._calculate_returns()

    def _set_parameters(self, *args):
        """ Updates parameters.
        """
        raise NotImplementedError

    def _calculate_position(self, data):
        """
        Calculates position according to strategy

        :param data:
        :return: data with position calculated
        """
        return data

    def test_strategy(self, *args):
        """ Backtests the trading strategy.
        """
        raise NotImplementedError

    def _assess_strategy(self, data, plot_results, title):

        data = self._calculate_position(data.copy())

        data["trades"] = data["position"].diff().fillna(0).abs()

        data["strategy"] = data["position"].shift(1) * data[self.returns_col]
        data["strategy_tc"] = data["strategy"] - np.abs(data[self.returns_col]) * data.trades * self.tc
        data.dropna(inplace=True)

        data["creturns"] = data[self.returns_col].cumsum().apply(np.exp)
        data["cstrategy"] = data["strategy"].cumsum().apply(np.exp)
        data["cstrategy_tc"] = data["strategy_tc"].cumsum().apply(np.exp)

        number_trades = data.trades.sum()

        print(f"Numer of trades: {number_trades}")

        self.results = data

        # absolute performance of the strategy
        perf = data["cstrategy"].iloc[-1]

        # out-/underperformance of strategy
        outperf = perf - data["creturns"].iloc[-1]

        if plot_results:
            self.plot_results(title)

        return round(perf, 6), round(outperf, 6)

    def plot_results(self, title):
        """ Plots the cumulative performance of the trading strategy
        compared to buy and hold.
        """
        if self.results is None:
            print("No results to plot yet. Run a strategy first.")
        else:
            plotting_cols = ["creturns", "cstrategy", "position"]
            if self.tc != 0:
                plotting_cols.append("cstrategy_tc")

            self.results[plotting_cols].plot(title=title, figsize=(12, 8), secondary_y='position')
            plt.show()

    def _update_and_run(self, *args, plot_results=False):
        """ Updates SMA parameters and returns the negative absolute performance (for minimization algorithm).

        Parameters
        ==========
        SMA: tuple
            SMA parameter tuple
        """
        return -self.test_strategy(*args, plot_results)[0]

    def optimize_parameters(self, *opt_params, **kwargs):
        ''' Finds global maximum given the SMA parameter ranges.

        Parameters
        ==========
        SMA1_range, SMA2_range: tuple
            tuples of the form (start, end, step size)
        '''

        opt = brute(self._update_and_run, opt_params, finish=None)

        return opt, -self._update_and_run(opt, plot_results=True)

