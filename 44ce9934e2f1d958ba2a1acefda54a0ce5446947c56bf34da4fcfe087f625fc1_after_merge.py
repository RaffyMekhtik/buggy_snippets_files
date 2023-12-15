    def __init__(self, config=None):
        self.config = config or default_config
        self.matcher = RepeatedMultiMatcher(
            RegexMatcher.from_shorthand("whitespace", r"[\t ]*"),
            RegexMatcher.from_shorthand("inline_comment", r"(-- |#)[^\n]*", is_comment=True),
            RegexMatcher.from_shorthand("block_comment", r"\/\*([^\*]|\*[^\/])*\*\/", is_comment=True),
            RegexMatcher.from_shorthand("single_quote", r"'[^']*'", is_code=True),
            RegexMatcher.from_shorthand("double_quote", r'"[^"]*"', is_code=True),
            RegexMatcher.from_shorthand("back_quote", r"`[^`]*`", is_code=True),
            RegexMatcher.from_shorthand("numeric_literal", r"(-?[0-9]+(\.[0-9]+)?)", is_code=True),
            RegexMatcher.from_shorthand("greater_than_or_equal", r">=", is_code=True),
            RegexMatcher.from_shorthand("less_than_or_equal", r"<=", is_code=True),
            RegexMatcher.from_shorthand("newline", r"\r\n"),
            RegexMatcher.from_shorthand("casting_operator", r"::"),
            RegexMatcher.from_shorthand("not_equals", r"!="),
            SingletonMatcher.from_shorthand("newline", "\n"),
            SingletonMatcher.from_shorthand("equals", "=", is_code=True),
            SingletonMatcher.from_shorthand("greater_than", ">", is_code=True),
            SingletonMatcher.from_shorthand("less_than", "<", is_code=True),
            SingletonMatcher.from_shorthand("dot", ".", is_code=True),
            SingletonMatcher.from_shorthand("comma", ",", is_code=True),
            SingletonMatcher.from_shorthand("plus", "+", is_code=True),
            SingletonMatcher.from_shorthand("tilde", "~", is_code=True),
            SingletonMatcher.from_shorthand("minus", "-", is_code=True),
            SingletonMatcher.from_shorthand("divide", "/", is_code=True),
            SingletonMatcher.from_shorthand("star", "*", is_code=True),
            SingletonMatcher.from_shorthand("bracket_open", "(", is_code=True),
            SingletonMatcher.from_shorthand("bracket_close", ")", is_code=True),
            SingletonMatcher.from_shorthand("semicolon", ";", is_code=True),
            RegexMatcher.from_shorthand("code", r"[0-9a-zA-Z_]*", is_code=True)
        )