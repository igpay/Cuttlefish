# Some code based on Camaleón, another Sublime Text plugin.
# https://github.com/SublimeText/Camaleon

import sublime, sublime_plugin

SUBLIME_PREFS_FILENAME = "Preferences.sublime-settings"
CUTTLEFISH_PREFS_FILENAME = "Cuttlefish.sublime-settings"

class Preset:
    DEFAULT_CONTROLLED_SETTINGS = ["color_scheme", "font_face", "font_size"]

    def __init__(self, data):
        self.raw_data = data

    def from_active_view():
        active_view = sublime.active_window().active_view()

        data = {}
        for setting in Preset.get_controlled_settings():
            data[setting] = active_view.settings().get(setting)

        return Preset(data)

    def load(self):
        sublime_preferences = sublime.load_settings(SUBLIME_PREFS_FILENAME)

        missing_settings = False

        for setting in Preset.get_controlled_settings():
            if setting in self.raw_data:
                sublime_preferences.set(setting, self.raw_data[setting])
            else:
                # If a controlled setting is not present in saved preset,
                # figure out its value and save it
                missing_settings = True

        sublime.save_settings(SUBLIME_PREFS_FILENAME)

        if missing_settings:
            new_preset = Preset.from_active_view()
            new_preset.save_as(self.raw_data["name"])

    def save(self):
            cuttlefish_prefs = sublime.load_settings(CUTTLEFISH_PREFS_FILENAME)
            presets = cuttlefish_prefs.get("presets", [])

            overwritten = False
            for i in range(0, len(presets)):
                if presets[i]["name"] == self.raw_data["name"]:
                    presets[i] = self.raw_data
                    overwritten = True

            if not overwritten: presets.append(self.raw_data)

            cuttlefish_prefs.set("presets", presets)
            sublime.save_settings(CUTTLEFISH_PREFS_FILENAME)

    def save_as(self, name):
        if len(name) > 0:
            self.raw_data["name"] = name
            self.save()


    def get_controlled_settings():
        cuttlefish_prefs = sublime.load_settings(CUTTLEFISH_PREFS_FILENAME)
        return cuttlefish_prefs.get("controlled_settings", Preset.DEFAULT_CONTROLLED_SETTINGS)


class CuttlefishCommandBase(sublime_plugin.WindowCommand):
    def __init__(self, window):
        self.window = window

        self.reload_data_from_preferences()

    def reload_data_from_preferences(self):
        self.preferences = sublime.load_settings(CUTTLEFISH_PREFS_FILENAME)
        self.current_preset = self.preferences.get("current_preset", 0)
        self.presets = self.preferences.get("presets", [])

    def switch_to_preset(self, preset_number):
        num_presets = len(self.presets)

        if num_presets == 0: return

        if preset_number >= num_presets: preset_number = 0
        elif preset_number < 0: preset_number = num_presets - 1

        preset = Preset(self.presets[preset_number])
        preset.load()

        self.current_preset = preset_number
        self.preferences.set("current_preset", preset_number)

        sublime.save_settings(CUTTLEFISH_PREFS_FILENAME)

    def show_preset_select_panel(self, callback):
        names = list(map((lambda preset: preset["name"]), self.presets))

        def checked_callback(choice):
            if choice != -1: callback(choice)

        self.window.show_quick_panel(names, checked_callback)
 

class CuttlefishCycleCommand(CuttlefishCommandBase):
    def run(self, direction="next"):
        self.reload_data_from_preferences()

        next_preset = self.current_preset

        if direction == "next": next_preset += 1
        else: next_preset -= 1

        self.switch_to_preset(next_preset)

class CuttlefishLoadCommand(CuttlefishCommandBase):
    def run(self):
        self.reload_data_from_preferences()
        self.show_preset_select_panel(self.switch_to_preset)


class CuttlefishSaveCommand(CuttlefishCommandBase):
    def run(self):
        preset = Preset.from_active_view()
        self.window.show_input_panel("Preset name:","",preset.save_as,None,None)

class CuttlefishDeleteCommand(CuttlefishCommandBase):
    def run(self):
        self.reload_data_from_preferences()

        def callback(choice):
            del self.presets[choice]
            self.preferences.set("presets", self.presets)
            sublime.save_settings(CUTTLEFISH_PREFS_FILENAME)

        self.show_preset_select_panel(callback)