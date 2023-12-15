    def get_init_guess(self, cell=None, key='minao'):
        if cell is None:
            cell = self.cell
        dm_kpts = None
        key = key.lower()
        if key == '1e' or key == 'hcore':
            dm_kpts = self.init_guess_by_1e(cell)
        elif getattr(cell, 'natm', 0) == 0:
            logger.info(self, 'No atom found in cell. Use 1e initial guess')
            dm_kpts = self.init_guess_by_1e(cell)
        elif key == 'atom':
            dm = self.init_guess_by_atom(cell)
        elif key[:3] == 'chk':
            try:
                dm_kpts = self.from_chk()
            except (IOError, KeyError):
                logger.warn(self, 'Fail to read %s. Use MINAO initial guess',
                            self.chkfile)
                dm = self.init_guess_by_minao(cell)
        else:
            dm = self.init_guess_by_minao(cell)

        if dm_kpts is None:
            nao = dm[0].shape[-1]
            nkpts = len(self.kpts)
            # dm[spin,nao,nao] at gamma point -> dm_kpts[spin,nkpts,nao,nao]
            dm_kpts = np.repeat(dm[:,None,:,:], nkpts, axis=1)
            dm_kpts[0,:] *= 1.01
            dm_kpts[1,:] *= 0.99  # To slightly break spin symmetry
            assert dm_kpts.shape[0]==2

        if cell.dimension < 3:
            ne = np.einsum('xkij,kji->xk', dm_kpts, self.get_ovlp(cell)).real
            nelec = np.asarray(cell.nelec).reshape(2,1)
            if np.any(abs(ne - nelec) > 1e-7):
                logger.warn(self, 'Big error detected in the electron number '
                            'of initial guess density matrix (Ne/cell = %g)!\n'
                            '  This can cause huge error in Fock matrix and '
                            'lead to instability in SCF for low-dimensional '
                            'systems.\n  DM is normalized to correct number '
                            'of electrons', ne.mean())
                dm_kpts *= (nelec/ne).reshape(2,-1,1,1)
        return dm_kpts