    def hyperopt_loss_function(results: DataFrame, trade_count: int,
                               min_date: datetime, max_date: datetime,
                               *args, **kwargs) -> float:
        """
        Objective function, returns smaller number for more optimal results.

        Uses Sharpe Ratio calculation.
        """
        total_profit = results["profit_percent"]
        days_period = (max_date - min_date).days

        # adding slippage of 0.1% per trade
        total_profit = total_profit - 0.0005
        expected_returns_mean = total_profit.sum() / days_period
        up_stdev = np.std(total_profit)

        if (np.std(total_profit) != 0.):
            sharp_ratio = expected_returns_mean / up_stdev * np.sqrt(365)
        else:
            # Define high (negative) sharpe ratio to be clear that this is NOT optimal.
            sharp_ratio = -20.

        # print(expected_returns_mean, up_stdev, sharp_ratio)
        return -sharp_ratio