def validated(base_model=None):
    """
    Decorates an ``__init__`` method with typed parameters with validation
    and auto-conversion logic.

    >>> class ComplexNumber:
    ...     @validated()
    ...     def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
    ...         self.x = x
    ...         self.y = y

    Classes with decorated initializers can be instantiated using arguments of
    another type (e.g. an ``y`` argument of type ``str`` ). The decorator
    handles the type conversion logic.

    >>> c = ComplexNumber(y='42')
    >>> (c.x, c.y)
    (0.0, 42.0)

    If the bound argument cannot be converted, the decorator throws an error.

    >>> c = ComplexNumber(y=None)
    Traceback (most recent call last):
        ...
    pydantic.error_wrappers.ValidationError: 1 validation error for ComplexNumberModel
    y
      none is not an allowed value (type=type_error.none.not_allowed)

    Internally, the decorator delegates all validation and conversion logic to
    `a Pydantic model <https://pydantic-docs.helpmanual.io/>`_, which can be
    accessed through the ``Model`` attribute of the decorated initiazlier.

    >>> ComplexNumber.__init__.Model
    <class 'ComplexNumberModel'>

    The Pydantic model is synthesized automatically from on the parameter
    names and types of the decorated initializer. In the ``ComplexNumber``
    example, the synthesized Pydantic model corresponds to the following
    definition.

    >>> class ComplexNumberModel(BaseValidatedInitializerModel):
    ...     x: float = 0.0
    ...     y: float = 0.0


    Clients can optionally customize the base class of the synthesized
    Pydantic model using the ``base_model`` decorator parameter. The default
    behavior uses :class:`BaseValidatedInitializerModel` and its
    `model config <https://pydantic-docs.helpmanual.io/#config>`_.

    See Also
    --------
    BaseValidatedInitializerModel
        Default base class for all synthesized Pydantic models.
    """

    def validator(init):
        init_qualname = dict(inspect.getmembers(init))["__qualname__"]
        init_clsnme = init_qualname.split(".")[0]
        init_params = inspect.signature(init).parameters
        init_fields = {
            param.name: (
                param.annotation
                if param.annotation != inspect.Parameter.empty
                else Any,
                param.default
                if param.default != inspect.Parameter.empty
                else ...,
            )
            for param in init_params.values()
            if param.name != "self"
            and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        }

        if base_model is None:
            PydanticModel = create_model(
                model_name=f"{init_clsnme}Model",
                __config__=BaseValidatedInitializerModel.Config,
                **init_fields,
            )
        else:
            PydanticModel = create_model(
                model_name=f"{init_clsnme}Model",
                __base__=base_model,
                **init_fields,
            )

        def validated_repr(self) -> str:
            return dump_code(self)

        def validated_getnewargs_ex(self):
            return (), self.__init_args__

        @functools.wraps(init)
        def init_wrapper(*args, **kwargs):
            self, *args = args

            nmargs = {
                name: arg
                for (name, param), arg in zip(
                    list(init_params.items()), [self] + args
                )
                if name != "self"
            }
            model = PydanticModel(**{**nmargs, **kwargs})

            # merge nmargs, kwargs, and the model fields into a single dict
            all_args = {**nmargs, **kwargs, **model.__dict__}

            # save the merged dictionary for Representable use, but only of the
            # __init_args__ is not already set in order to avoid overriding a
            # value set by a subclass initializer in super().__init__ calls
            if not getattr(self, "__init_args__", {}):
                self.__init_args__ = OrderedDict(
                    {
                        name: arg
                        for name, arg in sorted(all_args.items())
                        if type(arg) != mx.gluon.ParameterDict
                    }
                )
                self.__class__.__getnewargs_ex__ = validated_getnewargs_ex
                self.__class__.__repr__ = validated_repr

            return init(self, **all_args)

        # attach the Pydantic model as the attribute of the initializer wrapper
        setattr(init_wrapper, "Model", PydanticModel)

        return init_wrapper

    return validator