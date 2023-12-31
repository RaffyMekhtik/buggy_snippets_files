    def _is_valid(self, *args, **kwargs):
        need_groups = ["Constants", "Header", "Parameters", "Units"]
        veto_groups = [
            "SUBFIND",
            "FOF",
            "PartType0/ChemistryAbundances",
            "PartType0/ChemicalAbundances",
            "RuntimePars",
            "HashTable",
        ]
        valid = True
        valid_fname = args[0]
        # If passed arg is a directory, look for the .0 file in that dir
        if os.path.isdir(args[0]):
            valid_files = []
            for f in os.listdir(args[0]):
                fname = os.path.join(args[0], f)
                if (".0" in f) and (".ewah" not in f) and os.path.isfile(fname):
                    valid_files.append(fname)
            if len(valid_files) == 0:
                valid = False
            elif len(valid_files) > 1:
                valid = False
            else:
                valid_fname = valid_files[0]
        try:
            fileh = h5py.File(valid_fname, mode="r")
            for ng in need_groups:
                if ng not in fileh["/"]:
                    valid = False
            for vg in veto_groups:
                if vg in fileh["/"]:
                    valid = False
            fileh.close()
        except Exception:
            valid = False
            pass
        return valid