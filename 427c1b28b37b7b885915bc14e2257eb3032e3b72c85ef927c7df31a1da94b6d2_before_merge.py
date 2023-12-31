def tokenize(buf):
    """
    Tokenize a Lisp file or string buffer into internal Hy objects.
    """
    try:
        return parser.parse(lexer.lex(buf))
    except LexingError as e:
        pos = e.getsourcepos()
        raise LexException("Could not identify the next token.",
                           pos.lineno, pos.colno)
    except LexException as e:
        if e.source is None:
            e.source = buf
        raise