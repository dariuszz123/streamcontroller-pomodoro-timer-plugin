# Import StreamController modules
from enum import Enum
import time
import os
from src.backend.DeckManagement.InputIdentifier import Input, InputEvent
from src.backend.PluginManager.ActionBase import ActionBase

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk


class State(Enum):
    IDLE = "idle"
    RUNNING = "running"
    FINISHED_BLINKING = "finished_blinking"


class Pomodoro(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._timer_state = State.IDLE
        self.active_timer = 1  # 1 or 2 - which timer is selected
        self.duration_minutes_t1 = 25  # Timer 1 (Focus) duration
        self.duration_minutes_t2 = 5   # Timer 2 (Rest) duration
        self.label_t1 = "Focus"
        self.label_t2 = "Rest"
        self.start_time = None
        self.blink_timer_id = None
        self.blink_on = False  # Toggle for blinking
        self.blink_enabled = True
        self.color1 = [255, 0, 0, 255]  # Red
        self.color2 = [0, 0, 255, 255]  # Blue

    def on_ready(self) -> None:
        """Called when the action is ready to be displayed."""
        settings = self.get_settings()
        self.duration_minutes_t1 = settings.get("duration_minutes_t1", 25)
        self.duration_minutes_t2 = settings.get("duration_minutes_t2", 5)
        self.label_t1 = settings.get("label_t1", "Focus")
        self.label_t2 = settings.get("label_t2", "Rest")
        self.blink_enabled = settings.get("blink_enabled", True)
        self.color1 = settings.get("color1", [255, 0, 0, 255])
        self.color2 = settings.get("color2", [0, 0, 255, 255])
        self._update_display()

    def on_tick(self) -> None:
        """Called every second by StreamController."""
        if self._timer_state == State.RUNNING:
            remaining = self._get_remaining_seconds()
            if remaining <= 0:
                # Timer finished, transition to blinking
                self._transition_to_finished()
            else:
                self._update_display()

    def event_callback(self, event: InputEvent, data) -> None:
        """Handle button press events."""
        if event not in (Input.Key.Events.SHORT_UP, Input.Dial.Events.SHORT_UP,
                         Input.Dial.Events.SHORT_TOUCH_PRESS):
            return

        if self._timer_state == State.IDLE:
            # Start the current timer
            self._start_timer()
        elif self._timer_state == State.RUNNING:
            # Switch to other timer's IDLE (stop, don't auto-start)
            self._switch_to_other_idle()
        elif self._timer_state == State.FINISHED_BLINKING:
            # Switch to other timer and start it
            self._switch_and_start()

    def on_remove(self) -> None:
        """Called when the action is removed - cleanup timers."""
        self._stop_blink_timer()

    def _get_current_duration(self) -> int:
        """Get duration in minutes for the active timer."""
        if self.active_timer == 1:
            return self.duration_minutes_t1
        else:
            return self.duration_minutes_t2

    def _get_current_label(self) -> str:
        """Get label for the active timer."""
        if self.active_timer == 1:
            return self.label_t1
        else:
            return self.label_t2

    def _switch_timer(self) -> None:
        """Switch to the other timer."""
        self.active_timer = 2 if self.active_timer == 1 else 1

    def _start_timer(self) -> None:
        """Start the Pomodoro timer."""
        self._timer_state = State.RUNNING
        self.start_time = time.time()
        self._update_display()

    def _switch_to_other_idle(self) -> None:
        """Switch to other timer's IDLE state (without starting)."""
        self._stop_blink_timer()
        self._switch_timer()
        self._timer_state = State.IDLE
        self.start_time = None
        self.blink_on = False
        # Clear background color
        try:
            self.set_background_color(color=[0, 0, 0, 0])
        except AttributeError:
            pass
        self._update_display()

    def _switch_and_start(self) -> None:
        """Switch to other timer and start it."""
        self._stop_blink_timer()
        self._switch_timer()
        self.blink_on = False
        # Clear background color
        try:
            self.set_background_color(color=[0, 0, 0, 0])
        except AttributeError:
            pass
        self._start_timer()

    def _reset_to_idle(self) -> None:
        """Reset the timer to idle state (same timer)."""
        self._stop_blink_timer()
        self._timer_state = State.IDLE
        self.start_time = None
        self.blink_on = False
        # Clear background color
        try:
            self.set_background_color(color=[0, 0, 0, 0])
        except AttributeError:
            pass
        self._update_display()

    def _transition_to_finished(self) -> None:
        """Transition to the finished/blinking state."""
        self._timer_state = State.FINISHED_BLINKING
        self.blink_on = True
        self._update_display()

        if self.blink_enabled:
            # Start blinking timer (500ms interval)
            self.blink_timer_id = GLib.timeout_add(500, self._blink_callback)
            # Set initial color
            try:
                self.set_background_color(color=self.color1)
            except AttributeError:
                pass
        else:
            # Just set solid color1 without blinking
            try:
                self.set_background_color(color=self.color1)
            except AttributeError:
                pass

    def _blink_callback(self) -> bool:
        """GLib timer callback for blinking effect."""
        if self._timer_state != State.FINISHED_BLINKING:
            return False  # Stop the timer

        self.blink_on = not self.blink_on
        try:
            if self.blink_on:
                self.set_background_color(color=self.color1)
            else:
                self.set_background_color(color=self.color2)
        except AttributeError:
            pass

        return True  # Continue the timer

    def _stop_blink_timer(self) -> None:
        """Stop the blink timer if running."""
        if self.blink_timer_id is not None:
            try:
                GLib.source_remove(self.blink_timer_id)
            except (OSError, ValueError):
                pass
            self.blink_timer_id = None

    def _get_remaining_seconds(self) -> int:
        """Get remaining time in seconds."""
        duration = self._get_current_duration()
        if self.start_time is None:
            return duration * 60

        elapsed = time.time() - self.start_time
        remaining = (duration * 60) - elapsed
        return max(0, int(remaining))

    def _format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02}:{secs:02}"

    def _get_icon_path(self) -> str:
        """Get the path to the pomodoro icon."""
        # Get the plugin directory path
        action_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_dir = os.path.dirname(os.path.dirname(action_dir))
        icon_path = os.path.join(plugin_dir, "assets", "pomodoro.png")
        return icon_path

    def _update_display(self) -> None:
        """Update the button display."""
        # Set the pomodoro icon at the top
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            self.set_media(media_path=icon_path, size=0.35, valign=-1)

        # Set the bottom label with current timer name
        self.set_bottom_label(self._get_current_label())

        # Set the center label with time
        if self._timer_state == State.IDLE:
            total_seconds = self._get_current_duration() * 60
            self.set_center_label(self._format_time(total_seconds))
        elif self._timer_state == State.RUNNING:
            remaining = self._get_remaining_seconds()
            self.set_center_label(self._format_time(remaining))
        else:  # FINISHED_BLINKING
            self.set_center_label("00:00")

    def get_config_rows(self) -> list:
        """Return configuration UI rows."""
        # Timer 1 duration setting
        self.duration_t1_row = Adw.SpinRow.new_with_range(min=1, max=120, step=1)
        self.duration_t1_row.set_title("Timer 1 Duration (minutes)")
        self.duration_t1_row.set_subtitle("Focus timer duration")

        # Timer 2 duration setting
        self.duration_t2_row = Adw.SpinRow.new_with_range(min=1, max=120, step=1)
        self.duration_t2_row.set_title("Timer 2 Duration (minutes)")
        self.duration_t2_row.set_subtitle("Rest timer duration")

        # Timer 1 label
        self.label_t1_entry = Gtk.Entry()
        self.label_t1_entry.set_valign(Gtk.Align.CENTER)
        self.label_t1_row = Adw.ActionRow()
        self.label_t1_row.set_title("Timer 1 Label")
        self.label_t1_row.set_subtitle("Name shown for focus timer")
        self.label_t1_row.add_suffix(self.label_t1_entry)

        # Timer 2 label
        self.label_t2_entry = Gtk.Entry()
        self.label_t2_entry.set_valign(Gtk.Align.CENTER)
        self.label_t2_row = Adw.ActionRow()
        self.label_t2_row.set_title("Timer 2 Label")
        self.label_t2_row.set_subtitle("Name shown for rest timer")
        self.label_t2_row.add_suffix(self.label_t2_entry)

        # Blink enable switch
        self.blink_switch = Adw.SwitchRow()
        self.blink_switch.set_title("Enable blinking")
        self.blink_switch.set_subtitle("Blink between colors when finished")

        # Color 1 picker
        self.color1_button = Gtk.ColorButton()
        self.color1_button.set_use_alpha(True)
        self.color1_button.set_valign(Gtk.Align.CENTER)
        self.color1_row = Adw.ActionRow()
        self.color1_row.set_title("Color 1")
        self.color1_row.set_subtitle("Primary finish color")
        self.color1_row.add_suffix(self.color1_button)

        # Color 2 picker
        self.color2_button = Gtk.ColorButton()
        self.color2_button.set_use_alpha(True)
        self.color2_button.set_valign(Gtk.Align.CENTER)
        self.color2_row = Adw.ActionRow()
        self.color2_row.set_title("Color 2")
        self.color2_row.set_subtitle("Secondary blink color")
        self.color2_row.add_suffix(self.color2_button)

        self._load_config_values()

        # Connect signals
        self.duration_t1_row.connect("notify::value", self._on_duration_t1_changed)
        self.duration_t2_row.connect("notify::value", self._on_duration_t2_changed)
        self.label_t1_entry.connect("changed", self._on_label_t1_changed)
        self.label_t2_entry.connect("changed", self._on_label_t2_changed)
        self.blink_switch.connect("notify::active", self._on_blink_toggled)
        self.color1_button.connect("color-set", self._on_color1_changed)
        self.color2_button.connect("color-set", self._on_color2_changed)

        return [
            self.duration_t1_row,
            self.duration_t2_row,
            self.label_t1_row,
            self.label_t2_row,
            self.blink_switch,
            self.color1_row,
            self.color2_row
        ]

    def _load_config_values(self) -> None:
        """Load configuration values into UI."""
        settings = self.get_settings()
        self.duration_t1_row.set_value(settings.get("duration_minutes_t1", 25))
        self.duration_t2_row.set_value(settings.get("duration_minutes_t2", 5))
        self.label_t1_entry.set_text(settings.get("label_t1", "Focus"))
        self.label_t2_entry.set_text(settings.get("label_t2", "Rest"))
        self.blink_switch.set_active(settings.get("blink_enabled", True))

        # Load colors
        color1 = settings.get("color1", [255, 0, 0, 255])
        color2 = settings.get("color2", [0, 0, 255, 255])

        rgba1 = Gdk.RGBA()
        rgba1.red = color1[0] / 255.0
        rgba1.green = color1[1] / 255.0
        rgba1.blue = color1[2] / 255.0
        rgba1.alpha = color1[3] / 255.0
        self.color1_button.set_rgba(rgba1)

        rgba2 = Gdk.RGBA()
        rgba2.red = color2[0] / 255.0
        rgba2.green = color2[1] / 255.0
        rgba2.blue = color2[2] / 255.0
        rgba2.alpha = color2[3] / 255.0
        self.color2_button.set_rgba(rgba2)

    def _on_duration_t1_changed(self, *args) -> None:
        """Handle timer 1 duration setting change."""
        settings = self.get_settings()
        self.duration_minutes_t1 = round(self.duration_t1_row.get_value())
        settings["duration_minutes_t1"] = self.duration_minutes_t1
        self.set_settings(settings)

        # Update display if idle and on timer 1
        if self._timer_state == State.IDLE and self.active_timer == 1:
            self._update_display()

    def _on_duration_t2_changed(self, *args) -> None:
        """Handle timer 2 duration setting change."""
        settings = self.get_settings()
        self.duration_minutes_t2 = round(self.duration_t2_row.get_value())
        settings["duration_minutes_t2"] = self.duration_minutes_t2
        self.set_settings(settings)

        # Update display if idle and on timer 2
        if self._timer_state == State.IDLE and self.active_timer == 2:
            self._update_display()

    def _on_label_t1_changed(self, *args) -> None:
        """Handle timer 1 label change."""
        settings = self.get_settings()
        self.label_t1 = self.label_t1_entry.get_text()
        settings["label_t1"] = self.label_t1
        self.set_settings(settings)

        # Update display if on timer 1
        if self.active_timer == 1:
            self._update_display()

    def _on_label_t2_changed(self, *args) -> None:
        """Handle timer 2 label change."""
        settings = self.get_settings()
        self.label_t2 = self.label_t2_entry.get_text()
        settings["label_t2"] = self.label_t2
        self.set_settings(settings)

        # Update display if on timer 2
        if self.active_timer == 2:
            self._update_display()

    def _on_blink_toggled(self, *args) -> None:
        """Handle blink enable toggle."""
        settings = self.get_settings()
        self.blink_enabled = self.blink_switch.get_active()
        settings["blink_enabled"] = self.blink_enabled
        self.set_settings(settings)

    def _on_color1_changed(self, button) -> None:
        """Handle color 1 change."""
        rgba = button.get_rgba()
        self.color1 = [
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255),
            int(rgba.alpha * 255)
        ]
        settings = self.get_settings()
        settings["color1"] = self.color1
        self.set_settings(settings)

    def _on_color2_changed(self, button) -> None:
        """Handle color 2 change."""
        rgba = button.get_rgba()
        self.color2 = [
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255),
            int(rgba.alpha * 255)
        ]
        settings = self.get_settings()
        settings["color2"] = self.color2
        self.set_settings(settings)
