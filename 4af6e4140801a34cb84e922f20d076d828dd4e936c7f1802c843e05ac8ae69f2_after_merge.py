def width_fn_pandas(df):
    assert isinstance(df, pandas.DataFrame)
    return len(df.columns) if len(df.columns) > 0 else 0