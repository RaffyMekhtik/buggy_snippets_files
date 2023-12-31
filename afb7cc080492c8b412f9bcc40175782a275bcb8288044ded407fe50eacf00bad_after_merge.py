    def get_current_state_deltas(self, prev_stream_id):
        """Fetch a list of room state changes since the given stream id

        Each entry in the result contains the following fields:
            - stream_id (int)
            - room_id (str)
            - type (str): event type
            - state_key (str):
            - event_id (str|None): new event_id for this state key. None if the
                state has been deleted.
            - prev_event_id (str|None): previous event_id for this state key. None
                if it's new state.

        Args:
            prev_stream_id (int): point to get changes since (exclusive)

        Returns:
            Deferred[list[dict]]: results
        """
        prev_stream_id = int(prev_stream_id)
        if not self._curr_state_delta_stream_cache.has_any_entity_changed(
            prev_stream_id
        ):
            return []

        def get_current_state_deltas_txn(txn):
            # First we calculate the max stream id that will give us less than
            # N results.
            # We arbitarily limit to 100 stream_id entries to ensure we don't
            # select toooo many.
            sql = """
                SELECT stream_id, count(*)
                FROM current_state_delta_stream
                WHERE stream_id > ?
                GROUP BY stream_id
                ORDER BY stream_id ASC
                LIMIT 100
            """
            txn.execute(sql, (prev_stream_id,))

            total = 0
            max_stream_id = prev_stream_id
            for max_stream_id, count in txn:
                total += count
                if total > 100:
                    # We arbitarily limit to 100 entries to ensure we don't
                    # select toooo many.
                    break

            # Now actually get the deltas
            sql = """
                SELECT stream_id, room_id, type, state_key, event_id, prev_event_id
                FROM current_state_delta_stream
                WHERE ? < stream_id AND stream_id <= ?
                ORDER BY stream_id ASC
            """
            txn.execute(sql, (prev_stream_id, max_stream_id))
            return self.cursor_to_dict(txn)

        return self.runInteraction(
            "get_current_state_deltas", get_current_state_deltas_txn
        )