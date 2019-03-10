# -*- encoding: utf-8 -*-

from functools import reduce

unhtml_map = {
    '&quot;': '"', '&laquo;': '"', '&raquo;': '"', '&#34;': '"', '&#8220;': '"',
    '&#171;': '"', '&#187;': '"', '&#039;': '\'', '&#39;': '\'', '&amp;': '&',
    '&copy;': '(c)', '&bull;': '*', '&#151;': '-', '&#8211;': '-', '&#8212;': '-',
    '&#45;': '-', '&mdash;': '-', '&lt;': '<', '&gt;': '>', '&nbsp;': ' ', '&#160;': ' ',
    '\n': '', '\r': '', '&#124;': '|', '&#033;': '!', '&#33;': '!', '&#58;': ':', '&#x3a;': ':',
    '&lsaquo;': '<', '&rsaquo;': '>', '&#178;': '²', '&#179;': '³', '&#180;': '´', '&#181;': 'µ',
    '&#176;': '°'
}

COLORS = {'red': 31, 'green': 32, 'yellow': 33, 'blue': 34}

def with_color(c, s):
    if isinstance(c, str):
        color = COLORS.get(c, 39)
    else:
        color = c
    return "\x1b[%dm%s\x1b[0m" % (color, s)

def unhtml(s):
    """
    Replaces enquoted special HTML charactes with their ASCII analogs
    """
    return reduce(lambda x, y: x.replace(y, unhtml_map[y]), unhtml_map, s)
