    def inner(*args, **kwargs):
        if current_user.role_download():
            return f(*args, **kwargs)
        abort(403)