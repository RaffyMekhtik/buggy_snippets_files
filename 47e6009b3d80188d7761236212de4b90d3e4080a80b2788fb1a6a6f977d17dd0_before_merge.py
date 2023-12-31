def get_search_query_from_webapp(preferences, form):
    # no text for the query ?
    if not form.get('q'):
        raise SearxParameterException('q', '')

    # set blocked engines
    disabled_engines = preferences.engines.get_disabled()

    # parse query, if tags are set, which change
    # the serch engine or search-language
    raw_text_query = RawTextQuery(form['q'], disabled_engines)
    raw_text_query.parse_query()

    # set query
    query = raw_text_query.getSearchQuery()

    # get and check page number
    pageno_param = form.get('pageno', '1')
    if not pageno_param.isdigit() or int(pageno_param) < 1:
        raise SearxParameterException('pageno', pageno_param)
    query_pageno = int(pageno_param)

    # get language
    # set specific language if set on request, query or preferences
    # TODO support search with multible languages
    if len(raw_text_query.languages):
        query_lang = raw_text_query.languages[-1]
    elif 'language' in form:
        query_lang = form.get('language')
    else:
        query_lang = preferences.get_value('language')

    # check language
    if not VALID_LANGUAGE_CODE.match(query_lang):
        raise SearxParameterException('language', query_lang)

    # get safesearch
    if 'safesearch' in form:
        query_safesearch = form.get('safesearch')
        # first check safesearch
        if not query_safesearch.isdigit():
            raise SearxParameterException('safesearch', query_safesearch)
        query_safesearch = int(query_safesearch)
    else:
        query_safesearch = preferences.get_value('safesearch')

    # safesearch : second check
    if query_safesearch < 0 or query_safesearch > 2:
        raise SearxParameterException('safesearch', query_safesearch)

    # get time_range
    query_time_range = form.get('time_range')

    # check time_range
    if query_time_range not in ('None', None, '', 'day', 'week', 'month', 'year'):
        raise SearxParameterException('time_range', query_time_range)

    # query_engines
    query_engines = raw_text_query.engines

    # timeout_limit
    query_timeout = raw_text_query.timeout_limit
    if query_timeout is None and 'timeout_limit' in form:
        raw_time_limit = form.get('timeout_limit')
        try:
            query_timeout = float(raw_time_limit)
        except ValueError:
            raise SearxParameterException('timeout_limit', raw_time_limit)

    # query_categories
    query_categories = []

    # if engines are calculated from query,
    # set categories by using that informations
    if query_engines and raw_text_query.specific:
        additional_categories = set()
        for engine in query_engines:
            if 'from_bang' in engine and engine['from_bang']:
                additional_categories.add('none')
            else:
                additional_categories.add(engine['category'])
        query_categories = list(additional_categories)

    # otherwise, using defined categories to
    # calculate which engines should be used
    else:
        # set categories/engines
        load_default_categories = True
        for pd_name, pd in form.items():
            if pd_name == 'categories':
                query_categories.extend(categ for categ in map(unicode.strip, pd.split(',')) if categ in categories)
            elif pd_name == 'engines':
                pd_engines = [{'category': engines[engine].categories[0],
                               'name': engine}
                              for engine in map(unicode.strip, pd.split(',')) if engine in engines]
                if pd_engines:
                    query_engines.extend(pd_engines)
                    load_default_categories = False
            elif pd_name.startswith('category_'):
                category = pd_name[9:]

                # if category is not found in list, skip
                if category not in categories:
                    continue

                if pd != 'off':
                    # add category to list
                    query_categories.append(category)
                elif category in query_categories:
                    # remove category from list if property is set to 'off'
                    query_categories.remove(category)

        if not load_default_categories:
            if not query_categories:
                query_categories = list(set(engine['category']
                                            for engine in query_engines))
        else:
            # if no category is specified for this search,
            # using user-defined default-configuration which
            # (is stored in cookie)
            if not query_categories:
                cookie_categories = preferences.get_value('categories')
                for ccateg in cookie_categories:
                    if ccateg in categories:
                        query_categories.append(ccateg)

            # if still no category is specified, using general
            # as default-category
            if not query_categories:
                query_categories = ['general']

            # using all engines for that search, which are
            # declared under the specific categories
            for categ in query_categories:
                query_engines.extend({'category': categ,
                                      'name': engine.name}
                                     for engine in categories[categ]
                                     if (engine.name, categ) not in disabled_engines)

    query_engines = deduplicate_query_engines(query_engines)

    return (SearchQuery(query, query_engines, query_categories,
                        query_lang, query_safesearch, query_pageno,
                        query_time_range, query_timeout),
            raw_text_query)