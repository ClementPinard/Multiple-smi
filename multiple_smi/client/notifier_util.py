def init_notifier(backend=None):
    if backend == "gnome":
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            gi.require_version('Notify', '0.7')
            from gi.repository import Notify as notify
            notify.init('notifier')

            def notify_func(title, message, icon):
                notify.Notification.new(
                    title, message, icon).show()
        except (ImportError, ValueError):
            return init_notifier(backend="ntfy")
    elif backend == "ntfy":
        try:
            from ntfy import notify

            def notify_func(title, message, icon, **kwargs):
                notify(message, title, icon=icon, **kwargs)
        except ImportError:
            return init_notifier(None)
    else:
        def notify_func(*args, **kwargs):
            return
    return notify_func
