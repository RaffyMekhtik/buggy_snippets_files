    def __init__(self, ds, field_list):
        f = ds._handle
        bp = ds.base_path
        mp = ds.meshes_path
        pp = ds.particles_path
        fields = f[bp + mp]

        for fname in fields.keys():
            field = fields[fname]
            if type(field) is h5.Dataset or is_const_component(field):
                # Don't consider axes. This appears to be a vector field of single dimensionality
                ytname = str("_".join([fname.replace("_", "-")]))
                parsed = parse_unit_dimension(np.asarray(field.attrs["unitDimension"], dtype=np.int))
                unit = str(YTQuantity(1, parsed).units)
                aliases = []
                # Save a list of magnetic fields for aliasing later on
                # We can not reasonably infer field type/unit by name in openPMD
                if unit == "T" or unit == "kg/(A*s**2)":
                    self._mag_fields.append(ytname)
                self.known_other_fields += ((ytname, (unit, aliases, None)),)
            else:
                for axis in field.keys():
                    ytname = str("_".join([fname.replace("_", "-"), axis]))
                    parsed = parse_unit_dimension(np.asarray(field.attrs["unitDimension"], dtype=np.int))
                    unit = str(YTQuantity(1, parsed).units)
                    aliases = []
                    # Save a list of magnetic fields for aliasing later on
                    # We can not reasonably infer field type by name in openPMD
                    if unit == "T" or unit == "kg/(A*s**2)":
                        self._mag_fields.append(ytname)
                    self.known_other_fields += ((ytname, (unit, aliases, None)),)
        for i in self.known_other_fields:
            mylog.debug("open_pmd - known_other_fields - {}".format(i))
        particles = f[bp + pp]
        for species in particles.keys():
            for record in particles[species].keys():
                try:
                    pds = particles[species + "/" + record]
                    parsed = parse_unit_dimension(pds.attrs["unitDimension"])
                    unit = str(YTQuantity(1, parsed).units)
                    ytattrib = str(record).replace("_", "-")
                    if ytattrib == "position":
                        # Symbolically rename position to preserve yt's interpretation of the pfield
                        # particle_position is later derived in setup_absolute_positions in the way yt expects it
                        ytattrib = "positionCoarse"
                    if type(pds) is h5.Dataset or is_const_component(pds):
                        name = ["particle", ytattrib]
                        self.known_particle_fields += ((str("_".join(name)), (unit, [], None)),)
                    else:
                        for axis in pds.keys():
                            aliases = []
                            name = ["particle", ytattrib, axis]
                            ytname = str("_".join(name))
                            self.known_particle_fields += ((ytname, (unit, aliases, None)),)
                except KeyError:
                    mylog.info("open_pmd - {}_{} does not seem to have unitDimension".format(species, record))
        for i in self.known_particle_fields:
            mylog.debug("open_pmd - known_particle_fields - {}".format(i))
        super(OpenPMDFieldInfo, self).__init__(ds, field_list)