def maybe_encode_as_char_array(var, name=None):
    if var.dtype.kind in {'S', 'U'}:
        dims, data, attrs, encoding = _var_as_tuple(var)
        if data.dtype.kind == 'U':
            if '_FillValue' in attrs:
                raise NotImplementedError(
                    'variable {!r} has a _FillValue specified, but '
                    '_FillValue is yet supported on unicode strings: '
                    'https://github.com/pydata/xarray/issues/1647'
                    .format(name))

            string_encoding = encoding.pop('_Encoding', 'utf-8')
            safe_setitem(attrs, '_Encoding', string_encoding, name=name)
            data = encode_string_array(data, string_encoding)

        if data.dtype.itemsize > 1:
            data = bytes_to_char(data)
            dims = dims + ('string%s' % data.shape[-1],)

        var = Variable(dims, data, attrs, encoding)
    return var