"""Validated, source-linked tables, equations and quotations for the shared reader."""
import xml.etree.ElementTree as ET

KINDS = {'table', 'equation', 'quotation'}
MATH_TAGS = {'math', 'mrow', 'mi', 'mo', 'mn', 'mfrac', 'msup', 'msub', 'msubsup',
             'msqrt', 'mroot', 'mfenced', 'mtext', 'mtable', 'mtr', 'mtd', 'mover',
             'munder', 'munderover', 'mspace'}
MATH_ATTRS = {'display', 'mathvariant', 'stretchy', 'fence', 'separator', 'columnalign',
              'rowalign', 'columnspacing', 'rowspacing', 'width', 'height', 'depth'}


def mathml(value):
    if not isinstance(value, str) or '<!' in value:
        raise ValueError('equation MathML must be a declaration-free string')
    root = ET.fromstring(value)
    if root.tag.rsplit('}', 1)[-1] != 'math':
        raise ValueError('MathML root must be math')
    for node in root.iter():
        if node.tag.rsplit('}', 1)[-1] not in MATH_TAGS:
            raise ValueError('unsupported MathML element')
        for key, val in node.attrib.items():
            if key not in MATH_ATTRS or any(x in val.lower() for x in ('javascript:', 'url(', 'data:')):
                raise ValueError('unsupported MathML attribute')
    return value


def kind(block):
    return next(iter(block)) if isinstance(block, dict) and len(block) == 1 and next(iter(block)) in KINDS else None


def validate(block, sources, safe):
    typ = kind(block)
    if not typ:
        raise ValueError('unknown rich evidence block')
    value = block[typ]
    if not isinstance(value, dict):
        raise ValueError('evidence block must be an object')
    for field in ('id', 'label', 'title', 'source', 'locator'):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(typ + ': missing ' + field)
    if not safe(value['id']) or value['source'] not in sources:
        raise ValueError('invalid evidence block id or source')
    source = sources[value['source']]
    if source.get('format') == 'pdf':
        page = value.get('page')
        if isinstance(page, bool) or not isinstance(page, int) or page < 1 or page > source.get('pages', 0):
            raise ValueError(typ + ': actual PDF physical page required')
    elif 'page' in value:
        raise ValueError(typ + ': do not assign PDF page numbers to non-PDF sources')
    if typ == 'table':
        cols, rows = value.get('columns'), value.get('rows')
        if (not isinstance(cols, list) or not cols or not isinstance(rows, list) or not rows
                or any(not isinstance(x, str) or not x.strip() for x in cols)
                or any(not isinstance(row, list) or len(row) != len(cols)
                       or any(not isinstance(cell, str) for cell in row) for row in rows)):
            raise ValueError('table needs text columns and rectangular text rows')
        if not value.get('caption'):
            raise ValueError('table needs a condition-preserving caption')
    elif typ == 'equation':
        if not isinstance(value.get('expression'), str) or not value['expression'].strip():
            raise ValueError('equation needs a readable expression')
        if not value.get('explanation') or not isinstance(value.get('variables'), list) or not value['variables']:
            raise ValueError('equation needs an explanation and variable definitions')
        for variable in value['variables']:
            if not isinstance(variable, dict) or not variable.get('symbol') or not variable.get('meaning'):
                raise ValueError('equation variable needs symbol and meaning')
        if 'mathml' in value:
            mathml(value['mathml'])
    elif not isinstance(value.get('text'), str) or not value['text'].strip():
        raise ValueError('quotation needs exact original text')
    return value


def visible_units(typ, value):
    """Yield relative JSON-pointer parts and visible strings; include math markup for review."""
    for field in ('label', 'title', 'caption', 'explanation', 'text', 'expression', 'mathml'):
        if isinstance(value.get(field), str) and value[field].strip():
            yield [field], value[field]
    for i, text in enumerate(value.get('columns', [])):
        yield ['columns', i], text
    for i, row in enumerate(value.get('rows', [])):
        for j, text in enumerate(row):
            yield ['rows', i, j], text
    for i, variable in enumerate(value.get('variables', [])):
        for field in ('symbol', 'meaning'):
            yield ['variables', i, field], variable[field]


def walk_blocks(case):
    for section in case.get('sections', []):
        for block in section.get('blocks', []):
            if kind(block):
                yield section['id'], block
            elif isinstance(block, dict) and 'detail' in block:
                for inner in block['detail'].get('blocks', []):
                    if kind(inner):
                        yield section['id'], inner
