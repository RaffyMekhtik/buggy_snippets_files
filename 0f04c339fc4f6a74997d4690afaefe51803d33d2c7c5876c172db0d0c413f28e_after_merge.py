    def get_value(self, name):
        """Ask kernel for a value"""
        reason_big = _("The variable is too big to be retrieved")
        reason_not_picklable = _("The variable is not picklable")
        reason_dead = _("The kernel is dead")
        reason_other = _("An error occured, see the console.")
        msg = _("%s.<br><br>"
                "Note: Please don't report this problem on Github, "
                "there's nothing to do about it.")
        try:
            return self.call_kernel(
                interrupt=True,
                blocking=True,
                display_error=True,
                timeout=CALL_KERNEL_TIMEOUT).get_value(name)
        except TimeoutError:
            raise ValueError(msg % reason_big)
        except (PicklingError, UnpicklingError):
            raise ValueError(msg % reason_not_picklable)
        except RuntimeError:
            raise ValueError(msg % reason_dead)
        except KeyError:
            raise
        except Exception:
            raise ValueError(msg % reason_other)