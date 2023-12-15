    def __init__(self, parent=None):
        super().__init__()
        # Also keep track of our parent, if defined
        if parent:
            SettingStore.save_app(parent)
        # Set the data type name for logging clarity (base class functions use this variable)
        self.data_type = "user settings"
        self.settings_filename = "openshot.settings"
        self.default_settings_filename = os.path.join(info.PATH, 'settings', '_default.settings')