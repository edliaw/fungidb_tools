"""Helper functions for the ElementTree library.

2012/11/14
Edward Liaw
"""

def _is_empty(text):
    return not text or text.isspace()


def indent(elem, level=0, tab='  '):
    """Recursive in-place pretty indenting for an Element Tree.

    Source: http://effbot.org/zone/element-lib.htm#prettyprint
    """
    i = '\n' + level * tab
    j = i + tab  # j = i_n+1
    indent_parent = False

    if len(elem):
        if _is_empty(elem.text):
            # Indent before element.
            elem.text = j
        if _is_empty(elem.tail):
            # Indent after element.
            elem.tail = i

        prev = None
        for child in elem:
            indent_block = indent(child, level + 1, tab)
            if indent_block or len(child) > 1:
                # This child or some lower child block should be super-indented.
                if len(elem) == 1:
                    # Pass indentation up because this level only has one child.
                    indent_parent = True
                else:
                    # Surround this block with newlines for emphasis.
                    if prev is not None and _is_empty(prev.tail):
                        prev.tail = '\n' + j
                    if _is_empty(child.tail):
                        child.tail = '\n' + j
            prev = child

        if _is_empty(child.tail):
            # Last child element determines closing tag tab level.
            child.tail = i
    else:
        if level and _is_empty(elem.tail):
            elem.tail = i

    return indent_parent
