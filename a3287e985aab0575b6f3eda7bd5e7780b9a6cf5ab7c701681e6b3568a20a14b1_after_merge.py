    def _on_highlight_change(self, event=None):
        if len(self.layer._highlight_index) > 0:
            # Color the hovered or selected points
            data = self.layer._data_view[self.layer._highlight_index]
            if data.ndim == 1:
                data = np.expand_dims(data, axis=0)
            size = self.layer._size_view[self.layer._highlight_index]
        else:
            data = np.zeros((1, self.layer.dims.ndisplay))
            size = 0

        self.node._subvisuals[1].set_data(
            data[:, ::-1] + 0.5,
            size=size,
            edge_width=self._highlight_width,
            symbol=self.layer.symbol,
            edge_color=self._highlight_color,
            face_color=transform_color('transparent'),
            scaling=True,
        )

        # only draw a box in 2D
        if self.layer.dims.ndisplay == 2:
            if (
                self.layer._highlight_box is None
                or 0 in self.layer._highlight_box.shape
            ):
                pos = np.zeros((1, self.layer.dims.ndisplay))
                width = 0
            else:
                pos = self.layer._highlight_box
                width = self._highlight_width

            self.node._subvisuals[2].set_data(
                pos=pos[:, ::-1] + 0.5,
                color=self._highlight_color,
                width=width,
            )

        self.node.update()