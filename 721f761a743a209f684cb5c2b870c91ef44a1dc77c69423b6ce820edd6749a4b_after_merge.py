def define_binding(db):
    class TorrentMetadata(db.Metadata):
        _discriminator_ = REGULAR_TORRENT
        infohash = orm.Optional(buffer, default='\x00' * 20)
        title = orm.Optional(str, default='')
        size = orm.Optional(int, size=64, default=0)
        tags = orm.Optional(str, default='')
        tracker_info = orm.Optional(str, default='')
        torrent_date = orm.Optional(datetime, default=datetime.utcnow)
        _payload_class = TorrentMetadataPayload

        def get_magnet(self):
            return ("magnet:?xt=urn:btih:%s&dn=%s" %
                    (str(self.infohash).encode('hex'), self.title)) + \
                   ("&tr=%s" % self.tracker_info if self.tracker_info else "")

        @classmethod
        def search_keyword(cls, query, entry_type=None, lim=100):
            # Requires FTS5 table "FtsIndex" to be generated and populated.
            # FTS table is maintained automatically by SQL triggers.
            # BM25 ranking is embedded in FTS5.

            # Sanitize FTS query
            if not query:
                return []
            if query.endswith("*"):
                query = "\"" + query[:-1] + "\"" + "*"
            else:
                query = "\"" + query + "\""

            metadata_type = entry_type or cls._discriminator_
            sql_search_fts = "metadata_type = %d AND rowid IN (SELECT rowid FROM FtsIndex WHERE " \
                             "FtsIndex MATCH $query ORDER BY bm25(FtsIndex) LIMIT %d)" % (metadata_type, lim)
            return cls.select(lambda x: orm.raw_sql(sql_search_fts))[:]

        @classmethod
        def get_auto_complete_terms(cls, keyword, max_terms, limit=100):
            with db_session:
                result = cls.search_keyword(keyword + "*", lim=limit)
            titles = [g.title.lower() for g in result]

            # Copy-pasted from the old DBHandler (almost) completely
            all_terms = set()
            for line in titles:
                if len(all_terms) >= max_terms:
                    break
                i1 = line.find(keyword)
                i2 = line.find(' ', i1 + len(keyword))
                term = line[i1:i2] if i2 >= 0 else line[i1:]
                if term != keyword:
                    all_terms.add(term)
            return list(all_terms)

    return TorrentMetadata