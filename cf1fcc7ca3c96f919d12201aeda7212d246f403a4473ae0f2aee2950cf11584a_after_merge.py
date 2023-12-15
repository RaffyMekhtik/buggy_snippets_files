    def serialise_tracker(self, tracker: "DialogueStateTracker") -> Dict:
        """Serializes the tracker, returns object with decimal types"""
        d = tracker.as_dialogue().as_dict()
        d.update(
            {
                "sender_id": tracker.sender_id,
                "session_date": int(datetime.now(tz=timezone.utc).timestamp()),
            }
        )
        # DynamoDB cannot store `float`s, so we'll convert them to `Decimal`s
        return core_utils.replace_floats_with_decimals(d)