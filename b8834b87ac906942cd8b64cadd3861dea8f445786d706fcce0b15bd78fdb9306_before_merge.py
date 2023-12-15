    def annotate_to_first_argument(self, func: Callable, typ: Type) -> None:
        """Annotate type hint to the first argument of function if needed."""
        try:
            sig = inspect.signature(func, type_aliases=self.config.autodoc_type_aliases)
        except TypeError as exc:
            logger.warning(__("Failed to get a method signature for %s: %s"),
                           self.fullname, exc)
            return
        except ValueError:
            return
        if len(sig.parameters) == 1:
            return

        params = list(sig.parameters.values())
        if params[1].annotation is Parameter.empty:
            params[1] = params[1].replace(annotation=typ)
            try:
                func.__signature__ = sig.replace(parameters=params)  # type: ignore
            except TypeError:
                # failed to update signature (ex. built-in or extension types)
                return