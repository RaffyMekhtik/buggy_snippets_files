def comparator(operator: Comparator) -> Comparator:
    """Wrap a Version binary op method in a type-check."""

    @wraps(operator)
    def wrapper(self: "Version", other: Comparable) -> bool:
        comparable_types = (
            Version,
            dict,
            tuple,
            list,
            *String.__args__,  # type: ignore
        )
        if not isinstance(other, comparable_types):
            return NotImplemented
        return operator(self, other)

    return wrapper