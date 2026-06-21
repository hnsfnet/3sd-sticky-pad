import config

try:
    import keyboard
    HAS_KEYBOARD = True
except Exception:
    HAS_KEYBOARD = False


class HotkeyManager:
    def __init__(self, root, on_new_note):
        self.root = root
        self._on_new_note = on_new_note
        self._registered = False

    def register(self):
        if not HAS_KEYBOARD:
            return False
        try:
            keyboard.add_hotkey(config.HOTKEY_NEW_NOTE, self._hotkey_new_note, suppress=False)
            self._registered = True
            return True
        except Exception as e:
            print(f"全局快捷键注册失败: {e}")
            return False

    def _hotkey_new_note(self):
        self.root.after(0, self._on_new_note)

    def unregister(self):
        if HAS_KEYBOARD and self._registered:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
            self._registered = False
