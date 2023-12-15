    def __setattr__(self, name, value):
        if self.__config__.extra is not Extra.allow and name not in self.__fields__:
            raise ValueError(f'"{self.__class__.__name__}" object has no field "{name}"')
        elif not self.__config__.allow_mutation:
            raise TypeError(f'"{self.__class__.__name__}" is immutable and does not support item assignment')
        elif self.__config__.validate_assignment:
            known_field = self.fields.get(name, None)
            if known_field:
                value, error_ = known_field.validate(value, self.dict(exclude={name}), loc=name)
                if error_:
                    raise ValidationError([error_], type(self))
        self.__dict__[name] = value
        self.__fields_set__.add(name)