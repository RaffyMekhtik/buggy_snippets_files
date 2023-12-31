def split_args(args):
    '''
    Splits args on whitespace, but intelligently reassembles
    those that may have been split over a jinja2 block or quotes.

    When used in a remote module, we won't ever have to be concerned about
    jinja2 blocks, however this function is/will be used in the
    core portions as well before the args are templated.

    example input: a=b c="foo bar"
    example output: ['a=b', 'c="foo bar"']

    Basically this is a variation shlex that has some more intelligence for
    how Ansible needs to use it.
    '''

    # the list of params parsed out of the arg string
    # this is going to be the result value when we are done
    params = []

    # Initial split on white space
    args = args.strip()
    items = args.strip().split('\n')

    # iterate over the tokens, and reassemble any that may have been
    # split on a space inside a jinja2 block.
    # ex if tokens are "{{", "foo", "}}" these go together

    # These variables are used
    # to keep track of the state of the parsing, since blocks and quotes
    # may be nested within each other.

    quote_char = None
    inside_quotes = False
    print_depth   = 0 # used to count nested jinja2 {{ }} blocks
    block_depth   = 0 # used to count nested jinja2 {% %} blocks
    comment_depth = 0 # used to count nested jinja2 {# #} blocks

    # now we loop over each split chunk, coalescing tokens if the white space
    # split occurred within quotes or a jinja2 block of some kind
    for itemidx,item in enumerate(items):

        # we split on spaces and newlines separately, so that we
        # can tell which character we split on for reassembly
        # inside quotation characters
        tokens = item.strip().split(' ')

        line_continuation = False
        for idx,token in enumerate(tokens):

            # if we hit a line continuation character, but
            # we're not inside quotes, ignore it and continue
            # on to the next token while setting a flag
            if token == '\\' and not inside_quotes:
                line_continuation = True
                continue

            # store the previous quoting state for checking later
            was_inside_quotes = inside_quotes
            quote_char = _get_quote_state(token, quote_char)
            inside_quotes = quote_char is not None

            # multiple conditions may append a token to the list of params,
            # so we keep track with this flag to make sure it only happens once
            # append means add to the end of the list, don't append means concatenate
            # it to the end of the last token
            appended = False

            # if we're inside quotes now, but weren't before, append the token
            # to the end of the list, since we'll tack on more to it later
            # otherwise, if we're inside any jinja2 block, inside quotes, or we were
            # inside quotes (but aren't now) concat this token to the last param
            if inside_quotes and not was_inside_quotes:
                params.append(token)
                appended = True
            elif print_depth or block_depth or comment_depth or inside_quotes or was_inside_quotes:
                if idx == 0 and was_inside_quotes:
                    params[-1] = "%s%s" % (params[-1], token)
                elif len(tokens) > 1:
                    spacer = ''
                    if idx > 0:
                        spacer = ' '
                    params[-1] = "%s%s%s" % (params[-1], spacer, token)
                else:
                    params[-1] = "%s\n%s" % (params[-1], token)
                appended = True

            # if the number of paired block tags is not the same, the depth has changed, so we calculate that here
            # and may append the current token to the params (if we haven't previously done so)
            prev_print_depth = print_depth
            print_depth = _count_jinja2_blocks(token, print_depth, "{{", "}}")
            if print_depth != prev_print_depth and not appended:
                params.append(token)
                appended = True

            prev_block_depth = block_depth
            block_depth = _count_jinja2_blocks(token, block_depth, "{%", "%}")
            if block_depth != prev_block_depth and not appended:
                params.append(token)
                appended = True

            prev_comment_depth = comment_depth
            comment_depth = _count_jinja2_blocks(token, comment_depth, "{#", "#}")
            if comment_depth != prev_comment_depth and not appended:
                params.append(token)
                appended = True

            # finally, if we're at zero depth for all blocks and not inside quotes, and have not
            # yet appended anything to the list of params, we do so now
            if not (print_depth or block_depth or comment_depth) and not inside_quotes and not appended and token != '':
                params.append(token)

        # if this was the last token in the list, and we have more than
        # one item (meaning we split on newlines), add a newline back here
        # to preserve the original structure
        if len(items) > 1 and itemidx != len(items) - 1 and not line_continuation:
            params[-1] += '\n'

        # always clear the line continuation flag
        line_continuation = False

    # If we're done and things are not at zero depth or we're still inside quotes,
    # raise an error to indicate that the args were unbalanced
    if print_depth or block_depth or comment_depth or inside_quotes:
        raise AnsibleError("error while splitting arguments, either an unbalanced jinja2 block or quotes")

    return params