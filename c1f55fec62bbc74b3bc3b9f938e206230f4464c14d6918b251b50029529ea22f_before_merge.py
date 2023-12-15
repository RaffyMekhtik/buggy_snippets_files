    def forward_request(self, method, path, data, headers):

        modified_data = None

        # If this request contains streaming v4 authentication signatures, strip them from the message
        # Related isse: https://github.com/localstack/localstack/issues/98
        # TODO we should evaluate whether to replace moto s3 with scality/S3:
        # https://github.com/scality/S3/issues/237
        if headers.get('x-amz-content-sha256') == 'STREAMING-AWS4-HMAC-SHA256-PAYLOAD':
            modified_data = strip_chunk_signatures(data)

        # POST requests to S3 may include a "${filename}" placeholder in the
        # key, which should be replaced with an actual file name before storing.
        if method == 'POST':
            original_data = modified_data or data
            expanded_data = expand_multipart_filename(original_data, headers)
            if expanded_data is not original_data:
                modified_data = expanded_data

        # persist this API call to disk
        persistence.record('s3', method, path, data, headers)

        parsed = urlparse.urlparse(path)
        query = parsed.query
        path = parsed.path
        bucket = path.split('/')[1]
        query_map = urlparse.parse_qs(query)
        if query == 'notification' or 'notification' in query_map:
            response = Response()
            response.status_code = 200
            if method == 'GET':
                # TODO check if bucket exists
                result = '<NotificationConfiguration xmlns="%s">' % XMLNS_S3
                if bucket in S3_NOTIFICATIONS:
                    notif = S3_NOTIFICATIONS[bucket]
                    events_string = '\n'.join(['<Event>%s</Event>' % e for e in notif['Event']])
                    for dest in ['Queue', 'Topic', 'CloudFunction']:
                        if dest in notif:
                            result += ("""<{dest}Configuration>
                                        <Id>{uid}</Id>
                                        <{dest}>{endpoint}</{dest}>
                                        {events}
                                    </{dest}Configuration>""").format(
                                dest=dest, uid=uuid.uuid4(),
                                endpoint=notif[dest],
                                events=events_string)
                result += '</NotificationConfiguration>'
                response._content = result

            if method == 'PUT':
                parsed = xmltodict.parse(data)
                notif_config = parsed.get('NotificationConfiguration')
                for dest in ['Queue', 'Topic', 'CloudFunction']:
                    config = notif_config.get('%sConfiguration' % (dest))
                    if config:
                        # TODO: what if we have multiple destinations - would we overwrite the config?
                        notification_details = {
                            'Id': config.get('Id'),
                            'Event': config.get('Event'),
                            dest: config.get(dest),
                            'Filter': config.get('Filter')
                        }
                        S3_NOTIFICATIONS[bucket] = json.loads(json.dumps(notification_details))

            # return response for ?notification request
            return response

        if query == 'cors' or 'cors' in query_map:
            if method == 'GET':
                return get_cors(bucket)
            if method == 'PUT':
                return set_cors(bucket, data)
            if method == 'DELETE':
                return delete_cors(bucket)

        if modified_data:
            return Request(data=modified_data, headers=headers, method=method)
        return True