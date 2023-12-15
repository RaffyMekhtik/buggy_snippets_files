    def __call__(self, projectables, optional_datasets=None, **info):
        (band,) = projectables

        factor = 4

        LOG.info('Reducing datasize by a factor %d.', factor)

        proj = band[::factor, ::factor]

        # newshape = (band.shape[0] / factor, factor,
        #            band.shape[1] / factor, factor)
        # proj = Dataset(band.reshape(newshape).mean(axis=3).mean(axis=1),
        #               copy=False, **band.info)

        old_area = proj.attrs['area']
        proj.attrs['area'] = AreaDefinition(old_area.area_id,
                                            old_area.name,
                                            old_area.proj_id,
                                            old_area.proj_dict,
                                            old_area.x_size / factor,
                                            old_area.y_size / factor,
                                            old_area.area_extent)
        proj.attrs['resolution'] *= factor
        self.apply_modifier_info(band, proj)
        return proj