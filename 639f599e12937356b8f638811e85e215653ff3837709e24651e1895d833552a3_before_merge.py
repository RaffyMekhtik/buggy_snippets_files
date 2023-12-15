    def __init__(self, win_id, parent=None):
        super().__init__(parent)
        bar = TabBar(win_id, self)
        self.setStyle(TabBarStyle())
        self.setTabBar(bar)
        bar.tabCloseRequested.connect(self.tabCloseRequested)
        bar.tabMoved.connect(functools.partial(
            QTimer.singleShot, 0, self._update_tab_titles))
        bar.currentChanged.connect(self._on_current_changed)
        bar.new_tab_requested.connect(self._on_new_tab_requested)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setDocumentMode(True)
        self.setElideMode(Qt.ElideRight)
        self.setUsesScrollButtons(True)
        bar.setDrawBase(False)
        self._init_config()
        config.instance.changed.connect(self._init_config)