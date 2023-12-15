    def generic_visit(self, node):
        """Drive the visitor."""
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                max_idx = len(value) - 1
                for idx, item in enumerate(value):
                    if isinstance(item, ast.AST):
                        if idx < max_idx:
                            setattr(item, 'sibling', value[idx + 1])
                        else:
                            setattr(item, 'sibling', None)
                        setattr(item, 'parent', node)

                        if self.pre_visit(item):
                            self.visit(item)
                            self.generic_visit(item)
                            self.post_visit(item)

            elif isinstance(value, ast.AST):
                setattr(value, 'sibling', None)
                setattr(value, 'parent', node)

                if self.pre_visit(value):
                    self.visit(value)
                    self.generic_visit(value)
                    self.post_visit(value)