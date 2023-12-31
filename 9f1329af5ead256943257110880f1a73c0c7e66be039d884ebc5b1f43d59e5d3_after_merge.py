    def _resolve_any_reference(self, builder, node, contnode):
        """Resolve reference generated by the "any" role."""
        refdoc = node['refdoc']
        target = node['reftarget']
        results = []
        # first, try resolving as :doc:
        doc_ref = self._resolve_doc_reference(builder, node, contnode)
        if doc_ref:
            results.append(('doc', doc_ref))
        # next, do the standard domain (makes this a priority)
        results.extend(self.domains['std'].resolve_any_xref(
            self, refdoc, builder, target, node, contnode))
        for domain in self.domains.values():
            if domain.name == 'std':
                continue  # we did this one already
            try:
                results.extend(domain.resolve_any_xref(self, refdoc, builder,
                                                       target, node, contnode))
            except NotImplementedError:
                # the domain doesn't yet support the new interface
                # we have to manually collect possible references (SLOW)
                for role in domain.roles:
                    res = domain.resolve_xref(self, refdoc, builder, role, target,
                                              node, contnode)
                    if res and isinstance(res[0], nodes.Element):
                        results.append(('%s:%s' % (domain.name, role), res))
        # now, see how many matches we got...
        if not results:
            return None
        if len(results) > 1:
            nice_results = ' or '.join(':%s:' % r[0] for r in results)
            self.warn_node('more than one target found for \'any\' cross-'
                           'reference %r: could be %s' % (target, nice_results),
                           node)
        res_role, newnode = results[0]
        # Override "any" class with the actual role type to get the styling
        # approximately correct.
        res_domain = res_role.split(':')[0]
        if newnode and newnode[0].get('classes'):
            newnode[0]['classes'].append(res_domain)
            newnode[0]['classes'].append(res_role.replace(':', '-'))
        return newnode