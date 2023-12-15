    def current_face_color(self, face_color: ColorType) -> None:
        self._current_face_color = transform_color(face_color)
        if self._update_properties and len(self.selected_data) > 0:
            cur_colors: np.ndarray = self.face_color
            cur_colors[self.selected_data] = self._current_face_color
            self.face_color = cur_colors
        self.events.face_color()
        self.events.highlight()