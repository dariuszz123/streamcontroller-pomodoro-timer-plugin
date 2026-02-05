# Import StreamController modules
from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions.Pomodoro.Pomodoro import Pomodoro


class PomodoroPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        # Register actions
        self.pomodoro_holder = ActionHolder(
            plugin_base=self,
            action_base=Pomodoro,
            action_id_suffix="Pomodoro",
            action_name="Pomodoro",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.UNTESTED
            }
        )
        self.add_action_holder(self.pomodoro_holder)

        # Register plugin
        self.register()
