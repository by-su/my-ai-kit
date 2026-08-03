import curses
import sys


def parse_setup_selection(raw, names, default_selected):
    raw = raw.strip().lower()
    if raw == "":
        return set(default_selected), "next", []
    if raw in ("b", "back"):
        return set(default_selected), "back", []
    if raw in ("q", "quit", "cancel"):
        return set(default_selected), "cancel", []
    if raw in ("all", "*"):
        return set(names), "next", []
    if raw in ("none", "no", "-"):
        return set(), "next", []

    selected = set()
    warnings = []
    tokens = [token.strip() for token in raw.split(",") if token.strip()]
    for token in tokens:
        if token.isdigit():
            idx = int(token)
            if 1 <= idx <= len(names):
                selected.add(names[idx - 1])
            else:
                warnings.append(f"Ignoring out-of-range selection: {token}")
        elif token in names:
            selected.add(token)
        else:
            warnings.append(f"Ignoring unknown selection: {token}")
    return selected, "next", warnings


def run_multiselect(title, rows, default_selected, single=False):
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None

    try:
        return curses.wrapper(_run_multiselect_screen, title, rows, default_selected, single)
    except Exception:
        return None


def _run_multiselect_screen(stdscr, title, rows, default_selected, single=False):
    if not rows:
        return set()

    curses.curs_set(0)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | getattr(curses, "REPORT_MOUSE_POSITION", 0))
    stdscr.keypad(True)

    names = [name for name, _ in rows]
    selected = set(default_selected)
    cursor = 0
    top = 0

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        visible = max(1, height - 5)

        if cursor < top:
            top = cursor
        elif cursor >= top + visible:
            top = cursor - visible + 1

        _add_line(stdscr, 0, 0, title, width, curses.A_BOLD)
        help_text = "Up/Down: move  Enter: next  b: back  q/Esc: cancel" if single else "Up/Down: move  Space/Click: toggle  a: all  n: none  Enter: next  b: back  q/Esc: cancel"
        _add_line(stdscr, 1, 0, help_text, width)

        for screen_idx, row_idx in enumerate(range(top, min(len(rows), top + visible)), start=3):
            name, desc = rows[row_idx]
            marker = "x" if name in selected else " "
            prefix = ">" if row_idx == cursor else " "
            text = f"{prefix} [{marker}] {name}"
            if desc:
                text += f" - {desc}"
            attr = curses.A_REVERSE if row_idx == cursor else curses.A_NORMAL
            _add_line(stdscr, screen_idx, 0, text, width, attr)

        footer = f"{len(selected)} selected"
        if len(rows) > visible:
            footer += f" | showing {top + 1}-{min(len(rows), top + visible)} of {len(rows)}"
        _add_line(stdscr, height - 1, 0, footer, width)

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = min(len(rows) - 1, cursor + 1)
        elif key == ord(" "):
            name = names[cursor]
            if single:
                selected = {name}
            elif name in selected:
                selected.remove(name)
            else:
                selected.add(name)
        elif key in (ord("a"), ord("A")):
            if not single:
                selected = set(names)
        elif key in (ord("n"), ord("N")):
            if not single:
                selected = set()
        elif key in (ord("b"), ord("B")):
            return selected, "back"
        elif key in (ord("q"), ord("Q"), 27):
            return selected, "cancel"
        elif key in (10, 13, curses.KEY_ENTER):
            return selected, "next"
        elif key == curses.KEY_MOUSE:
            try:
                _, _, y, _, bstate = curses.getmouse()
            except curses.error:
                continue
            row_idx = top + y - 3
            if 0 <= row_idx < len(rows):
                cursor = row_idx
                if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED):
                    name = names[row_idx]
                    if single:
                        selected = {name}
                    elif name in selected:
                        selected.remove(name)
                    else:
                        selected.add(name)


def _add_line(stdscr, y, x, text, width, attr=curses.A_NORMAL):
    if y < 0:
        return
    try:
        stdscr.addnstr(y, x, text, max(1, width - x - 1), attr)
    except curses.error:
        pass
