    def __init__(self, tags=None, **kwargs):
        ImageWriter.__init__(self,
                             default_config_filename="writers/mitiff.yaml",
                             **kwargs)

        self.tags = self.info.get("tags",
                                  None) if tags is None else tags
        if self.tags is None:
            self.tags = {}
        elif not isinstance(self.tags, dict):
            # if it's coming from a config file
            self.tags = dict(tuple(x.split("=")) for x in self.tags.split(","))

        self.mitiff_config = {}
        self.translate_channel_name = {}
        self.channel_order = {}