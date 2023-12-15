def get_record(name, zone, record_type, fetch_all=False, region=None, key=None,
               keyid=None, profile=None, split_dns=False, private_zone=False,
               retry_on_rate_limit=True, rate_limit_retries=5):
    '''
    Get a record from a zone.

    CLI example::

        salt myminion boto_route53.get_record test.example.org example.org A
    '''
    if region is None:
        region = 'universal'

    conn = _get_conn(region=region, key=key, keyid=keyid, profile=profile)

    while rate_limit_retries > 0:
        try:
            if split_dns:
                _zone = _get_split_zone(zone, conn, private_zone)
            else:
                _zone = conn.get_zone(zone)
            if not _zone:
                msg = 'Failed to retrieve zone {0}'.format(zone)
                log.error(msg)
                return None
            _type = record_type.upper()
            ret = odict.OrderedDict()

            name = _encode_name(name)
            if _type == 'A':
                _record = _zone.get_a(name, fetch_all)
            elif _type == 'CNAME':
                _record = _zone.get_cname(name, fetch_all)
            elif _type == 'MX':
                _record = _zone.get_mx(name, fetch_all)
            else:
                _record = _zone.find_records(name, _type, all=fetch_all)

            break  # the while True

        except DNSServerError as e:
            # if rate limit, retry:
            if retry_on_rate_limit and 'Throttling' == e.code:
                log.debug('Throttled by AWS API.')
                time.sleep(2)
                rate_limit_retries -= 1
                continue  # the while True; try again if not out of retries
            raise e

    if _record:
        ret['name'] = _decode_name(_record.name)
        ret['value'] = _record.to_print()
        ret['record_type'] = _record.type
        ret['ttl'] = _record.ttl

    return ret