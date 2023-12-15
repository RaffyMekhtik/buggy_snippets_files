    def deserialize(cls, data: JsonDict) -> 'OverloadedFuncDef':
        assert data['.class'] == 'OverloadedFuncDef'
        res = OverloadedFuncDef([
            cast(OverloadPart, SymbolNode.deserialize(d))
            for d in data['items']])
        if data.get('impl') is not None:
            res.impl = cast(OverloadPart, SymbolNode.deserialize(data['impl']))
            # set line for empty overload items, as not set in __init__
            if len(res.items) > 0:
                res.set_line(res.impl.line)
        if data.get('type') is not None:
            res.type = mypy.types.deserialize_type(data['type'])
        res._fullname = data['fullname']
        set_flags(res, data['flags'])
        # NOTE: res.info will be set in the fixup phase.
        return res