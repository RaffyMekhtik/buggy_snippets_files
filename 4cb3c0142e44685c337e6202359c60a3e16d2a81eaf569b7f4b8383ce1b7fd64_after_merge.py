    def __truediv__(self, other):
        from ignite.metrics import MetricsLambda
        return MetricsLambda(lambda x, y: x.__truediv__(y), self, other)