	def _getEmbedding(self, obj):
		parent = obj.parent
		if not parent:
			# obj is probably dead.
			return None
		# optimisation: Passing an Offsets position checks nCharacters, which is an extra call we don't need.
		info = self._makeRawTextInfo(parent, textInfos.POSITION_FIRST)
		if isinstance(info, FakeEmbeddingTextInfo):
			info._startOffset = obj.indexInParent
			info._endOffset = info._startOffset + 1
			return info
		try:
			hl = obj.IAccessibleObject.QueryInterface(IAccessibleHandler.IAccessibleHyperlink)
			hlOffset = hl.startIndex
			info._startOffset = hlOffset
			info._endOffset = hlOffset + 1
			return info
		except COMError:
			pass
		return None