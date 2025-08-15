from dataclasses import dataclass, asdict, field
from typing import Literal

@dataclass
class Icon:
    path: str

ICON_DEFAULT = Icon(path="assets/translate.png")
ICON_PHONETIC = Icon(path="assets/translate-say.png")


@dataclass
class Item:
    title: str
    subtitle: str
    arg: str
    icon: Icon = ICON_DEFAULT
    mods: dict = field(default_factory=dict)
    quicklookurl: str = ""
    autocomplete: str = ""
    valid: bool = True


@dataclass
class Mod:
    subtitle: str
    arg: str
    valid: bool = True


def filter_asdict(obj):
    def filter(d):
        if isinstance(d, dict):
            return {k: filter(v) for k, v in d.items() if v or isinstance(v, (dict, list))}
        elif isinstance(d, list):
            return [filter(i) for i in d if i or isinstance(i, (dict, list))]
        else:
            return d
    return filter(asdict(obj))


class Workflow:
    def __init__(self):
        self.items = []

    def add_item(self, title: str, subtitle: str, arg: str, icon: Literal["default", "phonetic"] = "default", quicklookurl: str = "", autocomplete: str = "", valid: bool = True):
        pronunciation, content = arg.split("\0")
        item = Item(title=title, subtitle=subtitle, arg=pronunciation, quicklookurl=quicklookurl, autocomplete=autocomplete, valid=valid)
        item.mods = {
            "ctrl": Mod(subtitle=f"📣 {pronunciation}", arg=pronunciation),
            "cmd": Mod(subtitle=f"🔊 {pronunciation}", arg=pronunciation),
            "alt": Mod(subtitle="复制到剪贴板", arg=content)
        }
        if icon == "phonetic":
            item.icon = ICON_PHONETIC
        self.items.append(item)

    def to_dict(self):
        return {"items": [filter_asdict(item) for item in self.items]}