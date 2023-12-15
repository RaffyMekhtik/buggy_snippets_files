def is_method(var):
  if var is None or is_late_annotation(var):
    return False
  return isinstance(var.data[0], (
      abstract.INTERPRETER_FUNCTION_TYPES,
      special_builtins.ClassMethodInstance,
      special_builtins.PropertyInstance,
      special_builtins.StaticMethodInstance
  ))