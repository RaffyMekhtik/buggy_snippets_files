    def __init__(self):
        self.read_handle = GetStdHandle(STD_INPUT_HANDLE)
        self.read_handle.SetConsoleMode(ENABLE_LINE_INPUT | ENABLE_ECHO_INPUT | ENABLE_PROCESSED_INPUT)
        self.cur_event_length = 0
        self.cur_keys_length = 0
        self.captured_chars = []