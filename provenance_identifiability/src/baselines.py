def random_pred(ep):
    return [0]

def lexical_pred(ep):
    text=(ep['claim']+' '+ep['memory']).lower()
    return [i for i in range(4) if f'fact{i}' in text or f'f{i}' in text][:1] or [0]

def trace_pred(ep):
    out=[int(x.split(':')[1]) for x in ep['visible_trace'] if x.startswith('support:')]
    return out or lexical_pred(ep)

def full_oracle(ep):
    return ep['support']
