    def __init__(self, base_region, domain, ds, over_refine_factor = 1):
        super(OctreeSubset, self).__init__(ds, None)
        self._num_zones = 1 << (over_refine_factor)
        self._oref = over_refine_factor
        self.domain = domain
        self.domain_id = domain.domain_id
        self.ds = domain.ds
        self._index = self.ds.index
        self.oct_handler = domain.oct_handler
        self._last_mask = None
        self._last_selector_id = None
        self.base_region = base_region
        self.base_selector = base_region.selector