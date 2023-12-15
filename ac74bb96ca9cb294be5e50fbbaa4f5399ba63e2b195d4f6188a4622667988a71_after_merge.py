def custom_mangling(filename):
    import_mangling = [
        os.path.join('cluster', '__init__.py'),
        os.path.join('cluster', 'hierarchy.py'),
        os.path.join('cluster', 'vq.py'),
        os.path.join('fftpack', 'basic.py'),
        os.path.join('fftpack', 'pseudo_diffs.py'),
        os.path.join('integrate', 'odepack.py'),
        os.path.join('integrate', 'quadpack.py'),
        os.path.join('integrate', '_ode.py'),
        os.path.join('interpolate', 'fitpack.py'),
        os.path.join('interpolate', 'fitpack2.py'),
        os.path.join('interpolate', 'interpolate.py'),
        os.path.join('interpolate', 'interpolate_wrapper.py'),
        os.path.join('interpolate', 'ndgriddata.py'),
        os.path.join('io', 'array_import.py'),
        os.path.join('io', '__init__.py'),
        os.path.join('io', 'matlab', 'miobase.py'),
        os.path.join('io', 'matlab', 'mio4.py'),
        os.path.join('io', 'matlab', 'mio5.py'),
        os.path.join('io', 'matlab', 'mio5_params.py'),
        os.path.join('linalg', 'basic.py'),
        os.path.join('linalg', 'decomp.py'),
        os.path.join('linalg', 'lapack.py'),
        os.path.join('linalg', 'flinalg.py'),
        os.path.join('linalg', 'iterative.py'),
        os.path.join('linalg', 'misc.py'),
        os.path.join('lib', 'blas', '__init__.py'),
        os.path.join('lib', 'lapack', '__init__.py'),
        os.path.join('ndimage', 'filters.py'),
        os.path.join('ndimage', 'fourier.py'),
        os.path.join('ndimage', 'interpolation.py'),
        os.path.join('ndimage', 'measurements.py'),
        os.path.join('ndimage', 'morphology.py'),
        os.path.join('optimize', 'minpack.py'),
        os.path.join('optimize', 'zeros.py'),
        os.path.join('optimize', 'lbfgsb.py'),
        os.path.join('optimize', 'cobyla.py'),
        os.path.join('optimize', 'slsqp.py'),
        os.path.join('optimize', 'nnls.py'),
        os.path.join('signal', '__init__.py'),
        os.path.join('signal', 'bsplines.py'),
        os.path.join('signal', 'signaltools.py'),
        os.path.join('signal', 'fir_filter_design.py'),
        os.path.join('special', '__init__.py'),
        os.path.join('special', 'add_newdocs.py'),
        os.path.join('special', 'basic.py'),
        os.path.join('special', 'lambertw.py'),
        os.path.join('special', 'orthogonal.py'),
        os.path.join('spatial', '__init__.py'),
        os.path.join('spatial', 'distance.py'),
        os.path.join('sparse', 'linalg', 'isolve', 'iterative.py'),
        os.path.join('sparse', 'linalg', 'dsolve', 'linsolve.py'),
        os.path.join('sparse', 'linalg', 'dsolve', 'umfpack', 'umfpack.py'),
        os.path.join('sparse', 'linalg', 'eigen', 'arpack', 'arpack.py'),
        os.path.join('sparse', 'linalg', 'eigen', 'arpack', 'speigs.py'),
        os.path.join('sparse', 'linalg', 'iterative', 'isolve', 'iterative.py'),
        os.path.join('sparse', 'csgraph', '__init__.py'),
        os.path.join('sparse', 'csgraph', '_validation.py'),
        os.path.join('stats', 'stats.py'),
        os.path.join('stats', 'distributions.py'),
        os.path.join('stats', 'morestats.py'),
        os.path.join('stats', 'kde.py'),
        os.path.join('stats', 'mstats_basic.py'),
    ]

    if any(filename.endswith(x) for x in import_mangling):
        print(filename)
        f = open(filename, 'r', encoding='utf-8')
        text = f.read()
        f.close()
        for mod in ['_vq', '_hierarchy_wrap', '_fftpack', 'convolve',
                    '_flinalg', 'fblas', 'flapack', 'cblas', 'clapack',
                    'calc_lwork', '_cephes', 'specfun', 'orthogonal_eval',
                    'lambertw', 'ckdtree', '_distance_wrap', '_logit',
                    '_ufuncs', '_ufuncs_cxx',
                    '_minpack', '_zeros', '_lbfgsb', '_cobyla', '_slsqp',
                    '_nnls',
                    'sigtools', 'spline', 'spectral',
                    '_fitpack', 'dfitpack', '_interpolate',
                    '_odepack', '_quadpack', 'vode', '_dop', 'lsoda',
                    'vonmises_cython', '_rank',
                    'futil', 'mvn',
                    '_nd_image',
                    'numpyio',
                    '_superlu', '_arpack', '_iterative', '_umfpack',
                    'interpnd',
                    'mio_utils', 'mio5_utils', 'streams',
                    '_min_spanning_tree', '_shortest_path', '_tools', '_traversal'
                    ]:
            text = re.sub(r'^(\s*)import %s' % mod,
                          r'\1from . import %s' % mod,
                          text, flags=re.M)
            text = re.sub(r'^(\s*)from %s import' % mod,
                          r'\1from .%s import' % mod,
                          text, flags=re.M)
        #text = text.replace('from matrixlib', 'from .matrixlib')
        f = open(filename, 'w', encoding='utf-8')
        f.write(text)
        f.close()