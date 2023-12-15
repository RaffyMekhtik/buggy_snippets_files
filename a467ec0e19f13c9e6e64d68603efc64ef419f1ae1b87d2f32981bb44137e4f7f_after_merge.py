    def _generate_classification_page_as_list(self, taxonomy, classification, filtered_posts, context, kw, lang):
        """Render a single flat link list with this classification's posts."""
        kind = taxonomy.classification_name
        template_name = taxonomy.template_for_single_list
        output_name = os.path.join(self.site.config['OUTPUT_FOLDER'], self.site.path(kind, classification, lang))
        context["lang"] = lang
        # list.tmpl expects a different format than list_post.tmpl (Issue #2701)
        if template_name == 'list.tmpl':
            context["items"] = [(post.title(), post.permalink(), None) for post in filtered_posts]
        else:
            context["posts"] = filtered_posts
        context["kind"] = kind
        if "pagekind" not in context:
            context["pagekind"] = ["list", "tag_page"]
        task = self.site.generic_post_list_renderer(lang, filtered_posts, output_name, template_name, kw['filters'], context)
        task['uptodate'] = task['uptodate'] + [utils.config_changed(kw, 'nikola.plugins.task.taxonomies:list')]
        task['basename'] = str(self.name)
        yield task

        if taxonomy.generate_atom_feeds_for_post_lists and self.site.config['GENERATE_ATOM']:
            yield self._generate_classification_page_as_list_atom(taxonomy, classification, filtered_posts, context, kw, lang)