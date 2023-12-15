def create_dict_node_class(cls):
    """
    Create dynamic node class
    """
    class node_class(cls):
        """Node class created based on the input class"""
        def __init__(self, x, start_mark, end_mark):
            try:
                cls.__init__(self, x)
            except TypeError:
                cls.__init__(self)
            self.start_mark = start_mark
            self.end_mark = end_mark
            self.condition_functions = ['Fn::If']

        def __deepcopy__(self, memo):
            cls = self.__class__
            result = cls.__new__(cls, self.start_mark, self.end_mark)
            memo[id(self)] = result
            for k, v in self.items():
                result[deepcopy(k)] = deepcopy(v, memo)

            return result

        def __copy__(self):
            return self

        def get_safe(self, key, default=None, path=None, type_t=()):
            """
                Get values in format
            """
            path = path or []
            value = self.get(key, default)
            if not isinstance(value, (dict)):
                if isinstance(value, type_t) or not type_t:
                    return [(value, (path[:] + [key]))]

            results = []
            for sub_v, sub_path in value.items_safe(path):
                if isinstance(sub_v, type_t) or not type_t:
                    results.append((sub_v, sub_path))

            return results

        def items_safe(self, path=None, type_t=()):
            """Get items while handling IFs"""
            path = path or []
            if len(self) == 1:
                for k, v in self.items():
                    if k == 'Fn::If':
                        if isinstance(v, list):
                            if len(v) == 3:
                                for i, if_v in enumerate(v[1:]):
                                    if isinstance(if_v, dict):
                                        # yield from if_v.items_safe(path[:] + [k, i - 1])
                                        # Python 2.7 support
                                        for items, p in if_v.items_safe(path[:] + [k, i + 1]):
                                            if isinstance(items, type_t) or not type_t:
                                                yield items, p
                                    elif isinstance(if_v, list):
                                        if isinstance(if_v, type_t) or not type_t:
                                            yield if_v, path[:] + [k, i + 1]
                                    else:
                                        if isinstance(if_v, type_t) or not type_t:
                                            yield if_v, path[:] + [k, i + 1]
                    elif k != 'Ref' and v != 'AWS::NoValue':
                        if isinstance(self, type_t) or not type_t:
                            yield self, path[:]
            else:
                if isinstance(self, type_t) or not type_t:
                    yield self, path[:]

        def __getattr__(self, name):
            raise TemplateAttributeError('%s.%s is invalid' % (self.__class__.__name__, name))

    node_class.__name__ = '%s_node' % cls.__name__
    return node_class