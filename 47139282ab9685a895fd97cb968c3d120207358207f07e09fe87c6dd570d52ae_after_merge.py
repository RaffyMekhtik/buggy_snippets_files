    def tracks_in_tree(self):
        tracks = []
        for track in self.multirglob(*[f"*{ext}" for ext in self._all_music_ext]):
            if track.exists() and track.is_file() and track.parent != self.localtrack_folder:
                tracks.append(Query.process_input(LocalPath(str(track.absolute()))))
        return sorted(tracks, key=lambda x: x.to_string_user().lower())