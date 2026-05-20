import inspect
from typing import Iterable, Callable, get_type_hints

type Annotation = type
type ParameterKind = inspect._ParameterKind

def require_method(
    cls: type,
    name: str,
    params: Iterable[tuple[str, ParameterKind, Annotation | Callable[[Annotation], bool]]],
    result: Annotation | Callable[[Annotation], bool]
):
    
    unbound = cls.__dict__.get(name)
    hints = get_type_hints(unbound.__func__)
    
    if unbound is None:
        raise TypeError(f"class '{cls.__name__}' is missing required method '{name}'")
    
    sig = inspect.signature(unbound.__func__)
    parameters = list(sig.parameters.values())
    
    for param in params:
        namepattern, kind, annotation = param
        
        if not name in (parameter.name for parameter in parameters):
            raise TypeError(f"method '{cls.__name__}.{name}' is missing required parameter '{namepattern}'")
        parameter = next(parameter for parameter in parameters if parameter.name == name)
        
        if parameter.kind != kind:
            raise TypeError(f"parameter {parameter.name} of method '{cls.__name__}.{name}' must be of kind '{kind}'")
        
        if isinstance(annotation, Callable):
            if not annotation(parameter.annotation):
                raise TypeError(f"annotation of parameter {parameter.name} of method '{cls.__name__}.{name}' is not valid")
        
        elif annotation is not parameter.annotation:
            raise TypeError(f"annotation of parameter {parameter.name} of method '{cls.__name__}.{name}' must be {repr(annotation)}")
        
    resultannotation = hints.get("return")
        
    if isinstance(result, Callable):
        if not result(resultannotation):
            raise TypeError(f"annotation of result of method '{cls.__name__}.{name}' is not valid")
        
    elif hints.get("return") is not result:
        raise TypeError(f"annotation of result of method '{cls.__name__}.{name}' must be {repr(result)}")