    def _get_step(self, axis):
        # TODO: need to check if this is working fine, particularly with
        """ Use to determine the size of the widget with support for non 
        uniform axis.
        """
        if axis.index >= axis.size - 1:
            return axis.index2value(axis.index) - axis.index2value(axis.index - 1)
        else:
            return axis.index2value(axis.index + 1) - axis.index2value(axis.index)