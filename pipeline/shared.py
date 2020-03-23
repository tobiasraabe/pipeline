def ensure_list(string_or_list):
    return [string_or_list] if isinstance(string_or_list, str) else string_or_list
