    def process(self):
        report = self.receive_message()

        columns = [
            "source.ip",
            "source.geolocation.cc",
            "event_description.text",
            "source.asn"
        ]

        headers = True
        raw_report = utils.base64_decode(report.get("raw"))
        for row in csv.reader(io.StringIO(raw_report)):
            # ignore headers
            if headers:
                headers = False
                continue

            event = self.new_event(report)

            for key, value in zip(columns, row):
                if key == "__IGNORE__":
                    continue

                event.add(key, value)

            event.add('classification.type', 'scanner')
            event.add("raw", ",".join(row))

            self.send_message(event)
        self.acknowledge_message()