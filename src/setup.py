import curses
import sys
import unicodedata


ACTIVE_COLOR = 1


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
    active_attr = curses.A_BOLD
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(ACTIVE_COLOR, curses.COLOR_GREEN, -1)
        active_attr = curses.color_pair(ACTIVE_COLOR) | curses.A_BOLD
    curses.mousemask(curses.ALL_MOUSE_EVENTS | getattr(curses, "REPORT_MOUSE_POSITION", 0))
    stdscr.keypad(True)

    normalized_rows = [_normalize_row(row) for row in rows]
    names = [row["name"] for row in normalized_rows]
    selected = set(default_selected)
    cursor = 0
    top = 0

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        visible = max(1, height - 5)

        if cursor < top:
            top = cursor
        while cursor >= top and _rendered_height(normalized_rows[top:cursor + 1], width) > visible:
            top += 1

        _add_line(stdscr, 0, 0, title, width, curses.A_BOLD)
        help_text = "Up/Down: move  Enter: next  b: back  q/Esc: cancel" if single else "Up/Down: move  Space/Click: toggle  a: all  n: none  Enter: next  b: back  q/Esc: cancel"
        _add_line(stdscr, 1, 0, help_text, width)

        y = 3
        last_row_idx = top
        row_positions = {}
        for row_idx in range(top, len(normalized_rows)):
            if y >= height - 1:
                break
            last_row_idx = row_idx
            row = normalized_rows[row_idx]
            name = row["name"]
            desc = row["desc"]
            active = row["active"]
            marker = "x" if name in selected else " "
            prefix = ">" if row_idx == cursor else " "
            badge = "  active" if active else ""
            header = f"{prefix} [{marker}] {name}{badge}"
            attr = curses.A_REVERSE if row_idx == cursor else curses.A_NORMAL
            row_positions[y] = row_idx
            _add_line(stdscr, y, 0, header, width, attr)
            if active:
                _add_line(stdscr, y, max(0, len(header) - len("active")), "active", width, active_attr | attr)
            y += 1
            for detail in _wrap_text(desc, max(10, width - 6)):
                if y >= height - 1:
                    break
                _add_line(stdscr, y, 6, detail, width, attr)
                row_positions[y] = row_idx
                y += 1
            if y < height - 1 and desc:
                y += 1

        footer = f"{len(selected)} selected"
        if y >= height - 1 or top > 0:
            footer += f" | showing {top + 1}-{min(len(rows), last_row_idx + 1)} of {len(rows)}"
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
            row_idx = row_positions.get(y)
            if row_idx is not None and 0 <= row_idx < len(rows):
                cursor = row_idx
                if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED):
                    name = names[row_idx]
                    if single:
                        selected = {name}
                    elif name in selected:
                        selected.remove(name)
                    else:
                        selected.add(name)


def _normalize_row(row):
    if len(row) == 2:
        name, desc = row
        meta = {}
    else:
        name, desc, meta = row
    return {
        "name": name,
        "desc": desc or "",
        "active": bool((meta or {}).get("active")),
    }


def _wrap_text(text, width):
    if not text:
        return []
    lines = []
    for paragraph in str(text).splitlines():
        current = ""
        for word in paragraph.split(" "):
            if not word:
                continue
            candidate = word if not current else f"{current} {word}"
            if _display_width(candidate) > width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def _display_width(text):
    width = 0
    for ch in str(text):
        width += 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
    return width


def _rendered_height(rows, width):
    total = 0
    for row in rows:
        total += 1
        desc_lines = _wrap_text(row["desc"], max(10, width - 6))
        total += len(desc_lines)
        if desc_lines:
            total += 1
    return total


def _add_line(stdscr, y, x, text, width, attr=curses.A_NORMAL):
    if y < 0:
        return
    try:
        stdscr.addnstr(y, x, text, max(1, width - x - 1), attr)
    except curses.error:
        pass
