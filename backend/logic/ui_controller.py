class UIController:
    def __init__(self, main_logic):
        self.main_logic = main_logic
        self.ui = main_logic.ui

    def select_next_song(self):
        """Select the next song in the UI list."""
        song_count = len(self.ui.song_widgets)
        if not song_count:
            return
        
        new_index = (self.main_logic.selected_song_index + 1) % song_count
        self.ui.select_song_by_index(new_index)
        self.main_logic.selected_song_index = new_index

    def select_prev_song(self):
        """Select the previous song in the UI list."""
        song_count = len(self.ui.song_widgets)
        if not song_count:
            return
        
        new_index = (self.main_logic.selected_song_index - 1 + song_count) % song_count
        self.ui.select_song_by_index(new_index)
        self.main_logic.selected_song_index = new_index
        
    def play_selected_song(self):
        """Play the currently selected song."""
        if self.main_logic.selected_song_index != -1:
            self.main_logic.play_song_by_index(self.main_logic.selected_song_index)

    def update_song_selection(self, index):
        """Update the selected song index."""
        self.main_logic.selected_song_index = index