    def _lookup(self, name, *args, **kwargs):
        instance = self._lookup_loader.get(name.lower(), loader=self._loader, templar=self)

        if instance is not None:
            wantlist = kwargs.pop('wantlist', False)

            from ansible.utils.listify import listify_lookup_plugin_terms
            loop_terms = listify_lookup_plugin_terms(terms=args, templar=self, loader=self._loader, fail_on_undefined=True, convert_bare=False)
            # safely catch run failures per #5059
            try:
                ran = instance.run(loop_terms, variables=self._available_variables, **kwargs)
            except (AnsibleUndefinedVariable, UndefinedError) as e:
                raise AnsibleUndefinedVariable(e)
            except Exception as e:
                if self._fail_on_lookup_errors:
                    raise AnsibleError("An unhandled exception occurred while running the lookup plugin '%s'. Error was a %s, original message: %s" % (name, type(e), e))
                ran = None

            if ran:
                from ansible.vars.unsafe_proxy import UnsafeProxy, wrap_var
                if wantlist:
                    ran = wrap_var(ran)
                else:
                    try:
                        ran = UnsafeProxy(",".join(ran))
                    except TypeError:
                        if isinstance(ran, list) and len(ran) == 1:
                            ran = wrap_var(ran[0])
                        else:
                            ran = wrap_var(ran)

            return ran
        else:
            raise AnsibleError("lookup plugin (%s) not found" % name)