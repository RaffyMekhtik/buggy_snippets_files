def radd(df, other, axis='columns', level=None, fill_value=None):
    op = DataFrameAdd(axis=axis, level=level, fill_value=fill_value, lhs=other, rhs=df)
    return op.rcall(df, other)