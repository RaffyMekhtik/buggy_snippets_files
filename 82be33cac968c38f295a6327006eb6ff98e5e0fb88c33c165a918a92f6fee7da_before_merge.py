def start_download_data(args: Dict[str, Any]) -> None:
    """
    Download data (former download_backtest_data.py script)
    """
    config = setup_utils_configuration(args, RunMode.UTIL_EXCHANGE)

    timerange = TimeRange()
    if 'days' in config:
        time_since = arrow.utcnow().shift(days=-config['days']).strftime("%Y%m%d")
        timerange = TimeRange.parse_timerange(f'{time_since}-')

    if 'pairs' not in config:
        raise OperationalException(
            "Downloading data requires a list of pairs. "
            "Please check the documentation on how to configure this.")

    logger.info(f'About to download pairs: {config["pairs"]}, '
                f'intervals: {config["timeframes"]} to {config["datadir"]}')

    pairs_not_available: List[str] = []

    # Init exchange
    exchange = ExchangeResolver.load_exchange(config['exchange']['name'], config)
    try:

        if config.get('download_trades'):
            pairs_not_available = refresh_backtest_trades_data(
                exchange, pairs=config["pairs"], datadir=config['datadir'],
                timerange=timerange, erase=config.get("erase"))

            # Convert downloaded trade data to different timeframes
            convert_trades_to_ohlcv(
                pairs=config["pairs"], timeframes=config["timeframes"],
                datadir=config['datadir'], timerange=timerange, erase=config.get("erase"))
        else:
            pairs_not_available = refresh_backtest_ohlcv_data(
                exchange, pairs=config["pairs"], timeframes=config["timeframes"],
                datadir=config['datadir'], timerange=timerange, erase=config.get("erase"))

    except KeyboardInterrupt:
        sys.exit("SIGINT received, aborting ...")

    finally:
        if pairs_not_available:
            logger.info(f"Pairs [{','.join(pairs_not_available)}] not available "
                        f"on exchange {exchange.name}.")