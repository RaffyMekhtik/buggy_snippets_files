def sjoin(left_df, right_df, how='inner', op='intersects',
          lsuffix='left', rsuffix='right', **kwargs):
    """Spatial join of two GeoDataFrames.

    left_df, right_df are GeoDataFrames
    how: type of join
        left -> use keys from left_df; retain only left_df geometry column
        right -> use keys from right_df; retain only right_df geometry column
        inner -> use intersection of keys from both dfs;
                 retain only left_df geometry column
    op: binary predicate {'intersects', 'contains', 'within'}
        see http://toblerity.org/shapely/manual.html#binary-predicates
    lsuffix: suffix to apply to overlapping column names (left GeoDataFrame)
    rsuffix: suffix to apply to overlapping column names (right GeoDataFrame)
    """

    # CHECK VALIDITY OF JOIN TYPE
    allowed_hows = ['left', 'right', 'inner']

    if how not in allowed_hows:
        raise ValueError("`how` was \"%s\" but is expected to be in %s" % \
            (how, allowed_hows))
    
    # CHECK VALIDITY OF PREDICATE OPERATION
    allowed_ops = ['contains', 'within', 'intersects']

    if op not in allowed_ops:
        raise ValueError("`op` was \"%s\" but is expected to be in %s" % \
            (op, allowed_ops))

    # IF WITHIN, SWAP NAMES
    if op == "within":
        # within implemented as the inverse of contains; swap names
        left_df, right_df = right_df, left_df

    # CONVERT CRS IF NOT EQUAL
    if left_df.crs != right_df.crs:
        print('Warning: CRS does not match!')

    # CONSTRUCT SPATIAL INDEX FOR RIGHT DATAFRAME
    tree_idx = rtree.index.Index()
    right_df_bounds = right_df['geometry'].apply(lambda x: x.bounds)
    for i in right_df_bounds.index:
        tree_idx.insert(i, right_df_bounds[i])

    # FIND INTERSECTION OF SPATIAL INDEX
    idxmatch = (left_df['geometry'].apply(lambda x: x.bounds)
                .apply(lambda x: list(tree_idx.intersection(x))))
    idxmatch = idxmatch[idxmatch.str.len() > 0]

    r_idx = np.concatenate(idxmatch.values)
    l_idx = idxmatch.index.values.repeat(idxmatch.str.len().values) 

    # VECTORIZE PREDICATE OPERATIONS
    def find_intersects(a1, a2):
        return a1.intersects(a2)

    def find_contains(a1, a2):
        return a1.contains(a2)

    predicate_d = {'intersects': find_intersects,
                   'contains': find_contains,
                   'within': find_contains}

    check_predicates = np.vectorize(predicate_d[op])

    # CHECK PREDICATES
    result = (
              pd.DataFrame(
                  np.column_stack(
                      [l_idx,
                       r_idx,
                       check_predicates(
                           left_df['geometry']
                           .apply(lambda x: prepared.prep(x)).values[l_idx],
                           right_df['geometry'].values[r_idx])
                       ]))
               )

    result.columns = ['index_%s' % lsuffix, 'index_%s' % rsuffix, 'match_bool']
    result = (
              pd.DataFrame(result[result['match_bool']==1])
              .drop('match_bool', axis=1)
              )

    # IF 'WITHIN', SWAP NAMES AGAIN
    if op == "within":
        # within implemented as the inverse of contains; swap names
        left_df, right_df = right_df, left_df
        result = result.rename(columns={
                    'index_%s' % (lsuffix): 'index_%s' % (rsuffix),
                    'index_%s' % (rsuffix): 'index_%s' % (lsuffix)})

    # APPLY JOIN
    if how == 'inner':
        result = result.set_index('index_%s' % lsuffix)
        return (
                left_df
                .merge(result, left_index=True, right_index=True)
                .merge(right_df.drop('geometry', axis=1),
                    left_on='index_%s' % rsuffix, right_index=True,
                    suffixes=('_%s' % lsuffix, '_%s' % rsuffix))
                )
    elif how == 'left':
        result = result.set_index('index_%s' % lsuffix)
        return (
                left_df
                .merge(result, left_index=True, right_index=True, how='left')
                .merge(right_df.drop('geometry', axis=1),
                    how='left', left_on='index_%s' % rsuffix, right_index=True,
                    suffixes=('_%s' % lsuffix, '_%s' % rsuffix))
                )
    elif how == 'right':
        return (
                left_df
                .drop('geometry', axis=1)
                .merge(result.merge(right_df,
                    left_on='index_%s' % rsuffix, right_index=True,
                    how='right'), left_index=True,
                    right_on='index_%s' % lsuffix, how='right')
                .set_index('index_%s' % rsuffix)
                )