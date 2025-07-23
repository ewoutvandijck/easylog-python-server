# Helper functions for smooth color interpolation
def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{c:02x}" for c in rgb)


def _interpolate_color(start_hex: str, end_hex: str, t: float) -> str:
    """Linearly interpolate between two HEX colors.

    Parameters
    ----------
    start_hex : str
        Starting color in HEX (e.g. '#ff0000')
    end_hex : str
        Ending color in HEX (e.g. '#00ff00')
    t : float
        Interpolation factor between 0.0 and 1.0

    Returns
    -------
    str
        Interpolated HEX color
    """
    r1, g1, b1 = _hex_to_rgb(start_hex)
    r2, g2, b2 = _hex_to_rgb(end_hex)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return _rgb_to_hex((r, g, b))
