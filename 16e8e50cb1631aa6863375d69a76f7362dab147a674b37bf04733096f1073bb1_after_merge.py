    def parse_args(self, parser, argv, environ=None):
        args = super().parse_args(parser, argv)
        environ = environ or os.environ
        args.disable_failover = args.disable_failover \
            or bool(int(environ.get('MARS_DISABLE_FAILOVER', '0')))
        options.scheduler.dump_graph_data = bool(int(environ.get('MARS_DUMP_GRAPH_DATA', '0')))
        return args