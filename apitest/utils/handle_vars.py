_context_vars = {}

def set_var(k, v):
    _context_vars[k] = v

def get_var(v, default=None):
    v = _context_vars.get(v, default)
    return v

def get_all_vars():
    return _context_vars.copy()

def clear_all_vars():
    _context_vars.clear()

def get_globals():
    pass