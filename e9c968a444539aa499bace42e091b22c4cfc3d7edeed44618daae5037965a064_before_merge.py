def blacklist(context, config):
    """Generic blacklist test, B001.

    This generic blacklist test will be called for any encountered node with
    defined blacklist data available. This data is loaded via plugins using
    the 'bandit.blacklists' entry point. Please see the documentation for more
    details. Each blacklist datum has a unique bandit ID that may be used for
    filtering purposes, or alternatively all blacklisting can be filtered using
    the id of this built in test, 'B001'.
    """
    blacklists = config
    node_type = context.node.__class__.__name__

    if node_type == 'Call':
        func = context.node.func
        if isinstance(func, ast.Name) and func.id == '__import__':
            if len(context.node.args):
                if isinstance(context.node.args[0], ast.Str):
                    name = context.node.args[0].s
                else:
                    # TODO(??): import through a variable, need symbol tab
                    name = "UNKNOWN"
            else:
                name = ""  # handle '__import__()'
        else:
            name = context.call_function_name_qual
            # In the case the Call is an importlib.import, treat the first
            # argument name as an actual import module name.
            if name in ["importlib.import_module", "importlib.__import__"]:
                name = context.call_args[0]
        for check in blacklists[node_type]:
            for qn in check['qualnames']:
                if fnmatch.fnmatch(name, qn):
                    return report_issue(check, name)

    if node_type.startswith('Import'):
        prefix = ""
        if node_type == "ImportFrom":
            if context.node.module is not None:
                prefix = context.node.module + "."

        for check in blacklists[node_type]:
            for name in context.node.names:
                for qn in check['qualnames']:
                    if (prefix + name.name).startswith(qn):
                        return report_issue(check, name.name)