    def __init__(self, backend, rsa_cdata, evp_pkey):
        self._backend = backend
        self._rsa_cdata = rsa_cdata
        self._evp_pkey = evp_pkey

        n = self._backend._ffi.new("BIGNUM **")
        self._backend._lib.RSA_get0_key(
            self._rsa_cdata,
            n,
            self._backend._ffi.NULL,
            self._backend._ffi.NULL,
        )
        self._backend.openssl_assert(n[0] != self._backend._ffi.NULL)
        self._key_size = self._backend._lib.BN_num_bits(n[0])