    def __init__(self, interpreter, parser):
        creators, self.key_to_meta, self.describe, self.builtin_key = self.for_interpreter(interpreter)
        super(CreatorSelector, self).__init__(interpreter, parser, "creator", creators)