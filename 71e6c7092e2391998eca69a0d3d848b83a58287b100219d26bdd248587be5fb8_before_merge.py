def add(df, other, axis='columns', level=None, fill_value=None):
    other = wrap_sequence(other)
    op = DataFrameAdd(axis=axis, level=level, fill_value=fill_value, lhs=df, rhs=other)
    return op(df, other)