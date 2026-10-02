import json,re
def parse_choice_strict(raw, options):
    try:
        obj=json.loads(raw); value=str(obj.get('choice','')).strip().upper()
        return (value,'json') if value in options else (None,'unresolved')
    except Exception: pass
    # Accept only an embedded JSON object, e.g. after a reasoning block.
    matches=list(re.finditer(r'\{[^{}]*"choice"\s*:\s*"?([A-Za-z]+)"?[^{}]*\}',raw,re.S))
    if matches:
        value=matches[-1].group(1).upper()
        return (value,'json_embedded') if value in options else (None,'unresolved')
    return None,'unresolved'
