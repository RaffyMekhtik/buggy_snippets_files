    def movie(self, **kwargs):
        """
        Discover movies by different types of data like average rating, 
        number of votes, genres and certifications.

        Args:
            page: (optional) Minimum 1, maximum 1000.
            language: (optional) ISO 639-1 code.
            sort_by: (optional) Available options are 'vote_average.desc', 
                     'vote_average.asc', 'release_date.desc', 'release_date.asc'
                     'popularity.desc', 'popularity.asc'.
            include_adult: (optional) Toggle the inclusion of adult titles. 
                           Expected value is a boolean, True or False.
            year: (optional) Filter the results release dates to matches that
                  include this value. Expected value is a year.
            primary_release_year: (optional) Filter the results so that 
                                  only the primary release date year has 
                                  this value.  Expected value is a year.
            vote_count.gte or vote_count_gte: (optional) Only include movies 
                            that are equal to, or have a vote count higher 
                            than this value.  Expected value is an integer.
            vote_average.gte or vote_average_gte: (optional) Only include 
                              movies that are equal to, or have a higher 
                              average rating than this value.  Expected value 
                              is a float.
            with_genres: (optional) Only include movies with the specified 
                         genres.  Expected value is an integer (the id of 
                         a genre).  Multiple values can be specified. 
                         Comma separated indicates an 'AND' query, while 
                         a pipe (|) separated value indicates an 'OR'.
            release_date.gte or release_date_gte: (optional) The minimum 
                              release to include.  Expected format is 
                              'YYYY-MM-DD'.
            releaste_date.lte or release_date_lte: (optional) The maximum 
                              release to include.  Expected format is 
                              'YYYY-MM-DD'.
            certification_country: (optional) Only include movies with
                                   certifications for a specific country. When
                                   this value is specified, 'certification.lte'
                                   is required. An ISO 3166-1 is expected.
            certification.lte or certification_lte: (optional) Only include 
                               movies with this certification and lower. 
                               Expected value is a valid certification for 
                               the specified 'certification_country'.
            with_companies: (optional) Filter movies to include a specific 
                            company.  Expected value is an integer (the id 
                            of a company).  They can be comma separated 
                            to indicate an 'AND' query.
          
        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        # Periods are not allowed in keyword arguments but several API 
        # arguments contain periods. See both usages in tests/test_discover.py.
        for param in kwargs:
            if '_lte' in param:
                kwargs[param.replace('_lte', '.lte')] = kwargs.pop(param)
            if '_gte' in param:
                kwargs[param.replace('_gte', '.gte')] = kwargs.pop(param)
        
        path = self._get_path('movie')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response