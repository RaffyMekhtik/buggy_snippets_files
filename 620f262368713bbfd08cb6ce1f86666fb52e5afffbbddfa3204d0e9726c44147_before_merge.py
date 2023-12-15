    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        return Field(_type, description=field.help_text, required=not field.null)