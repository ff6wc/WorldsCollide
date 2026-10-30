import menus.pregame_track_scroll_area as scroll_area
import instruction.f0 as f0

class FlagsCommandWeights(scroll_area.ScrollArea):
    MENU_NUMBER = 18

    def __init__(self, rows, other = None):
        # rows: [(skill name, weight text)] for the skills -comw names; the others weigh
        # `other` (None: the default of 1)
        self.number_items = len(rows)
        self.lines = []

        self.lines.append(scroll_area.Line(f"Skill Weights ({self.number_items})", f0.set_blue_text_color))
        self.lines.append(scroll_area.Line(f"Others weigh {1 if other is None else other:g}:", f0.set_gray_text_color))

        for list_value in FlagsCommandWeights._format_menu(rows):
            padding = scroll_area.WIDTH - (len(list_value))
            self.lines.append(scroll_area.Line(f"{' ' * padding}{list_value}", f0.set_user_text_color))

        super().__init__()

    def _format_menu(rows):
        # one skill per line: name on the left, weight on the right
        return [f"  {name:<10}{text:>12}" for name, text in rows]
