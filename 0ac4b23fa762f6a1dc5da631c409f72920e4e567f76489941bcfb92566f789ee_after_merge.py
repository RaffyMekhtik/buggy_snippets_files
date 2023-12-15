def _update_search_strings(series, session, search=None):
    search_strings = series.search_strings
    aliases = [a.lower() for a in series.aliases] if series.aliases else []
    searches = [search.lower()] if search else []
    add = [series.name.lower()] + aliases + searches
    for name in set(add):
        if name not in search_strings:
            search_result = session.query(TVDBSearchResult).filter(TVDBSearchResult.search == name).first()
            if not search_result:
                search_result = TVDBSearchResult(search=name)
            search_result.series_id = series.id
            session.add(search_result)