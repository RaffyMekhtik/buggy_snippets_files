    def generate_stats(self, request, response):
        self.record_stats(
            {
                "get": [(k, request.GET.getlist(k)) for k in sorted(request.GET)],
                "post": [(k, request.POST.getlist(k)) for k in sorted(request.POST)],
                "cookies": [
                    (k, request.COOKIES.get(k)) for k in sorted(request.COOKIES)
                ],
            }
        )
        view_info = {
            "view_func": _("<no view>"),
            "view_args": "None",
            "view_kwargs": "None",
            "view_urlname": "None",
        }
        try:
            match = resolve(request.path)
            func, args, kwargs = match
            view_info["view_func"] = get_name_from_obj(func)
            view_info["view_args"] = args
            view_info["view_kwargs"] = kwargs
            view_info["view_urlname"] = getattr(match, "url_name", _("<unavailable>"))
        except Http404:
            pass
        self.record_stats(view_info)

        if hasattr(request, "session"):
            self.record_stats(
                {
                    "session": [
                        (k, request.session.get(k))
                        for k in sorted(request.session.keys())
                    ]
                }
            )