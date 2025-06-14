"""Compatibility patch for pymorphy2 with Python 3.12+

This module patches the inspect.getargspec issue that prevents pymorphy2
from working with Python 3.12 and later versions.

Import this module before importing pymorphy2 to apply the patch.
"""

import inspect

# Patch inspect.getargspec for Python 3.12+ compatibility
if not hasattr(inspect, 'getargspec'):
    from collections import namedtuple
    
    ArgSpec = namedtuple('ArgSpec', 'args varargs keywords defaults')
    
    def getargspec(func):
        from inspect import signature, _empty
        sig = signature(func)
        args = []
        defaults = []
        varargs = None
        keywords = None
        
        for param in sig.parameters.values():
            if param.kind == param.VAR_POSITIONAL:
                varargs = param.name
            elif param.kind == param.VAR_KEYWORD:
                keywords = param.name
            else:
                args.append(param.name)
                if param.default is not _empty:
                    defaults.append(param.default)
        
        return ArgSpec(args, varargs, keywords, tuple(defaults) if defaults else None)
    
    inspect.getargspec = getargspec
    print("Applied pymorphy2 compatibility patch for Python 3.12+")