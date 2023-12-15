def _multiply_seq_by_int(self, opnode, other, context):
    node = self.__class__(parent=opnode)
    elts = []
    for elt in self.elts:
        infered = helpers.safe_infer(elt, context)
        if infered is None:
            infered = util.Uninferable
        elts.append(infered)
    node.elts = elts * other.value
    return node