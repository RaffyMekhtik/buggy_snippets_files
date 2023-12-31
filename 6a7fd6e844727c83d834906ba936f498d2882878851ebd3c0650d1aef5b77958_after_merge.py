def otool_analysis(tools_dir, bin_name, bin_path, bin_dir):
    """OTOOL Analysis of Binary"""
    try:
        otool_dict = {
            "libs": [],
            "anal": []
        }
        logger.info("Running Object Analysis of Binary : " + bin_name)
        otool_dict["libs"] = get_otool_out(
            tools_dir, "libs", bin_path, bin_dir)
        # PIE
        pie_dat = get_otool_out(tools_dir, "header", bin_path, bin_dir)
        if b"PIE" in pie_dat:
            pie_flag = {
                "issue": "fPIE -pie flag is Found",
                "status": SECURE,
                "description": """App is compiled with Position Independent Executable (PIE) flag. 
                    This enables Address Space Layout Randomization (ASLR), a memory protection
                    mechanism for exploit mitigation."""
            }
        else:
            pie_flag = {
                "issue": "fPIE -pie flag is not Found",
                "status": IN_SECURE,
                "description": """with Position Independent Executable (PIE) flag. So Address Space Layout 
                    Randomization (ASLR) is missing. ASLR is a memory protection mechanism for exploit mitigation."""
            }
        # Stack Smashing Protection & ARC
        dat = get_otool_out(tools_dir, "symbols", bin_path, bin_dir)
        if b"stack_chk_guard" in dat:
            ssmash = {"issue": "fstack-protector-all flag is Found",
                      "status": SECURE,
                      "description": """App is compiled with Stack Smashing Protector (SSP) flag and is having protection against Stack
                Overflows/Stack Smashing Attacks."""
                      }
        else:
            ssmash = {"issue": "fstack-protector-all flag is not Found",
                      "status": IN_SECURE,
                      "description": """App is not compiled with Stack Smashing Protector (SSP) flag. It is vulnerable to
                Stack Overflows/Stack Smashing Attacks."""
                      }
        # ARC
        if b"_objc_release" in dat:
            arc_flag = {"issue": "fobjc-arc flag is Found",
                        "status": SECURE,
                        "description": """App is compiled with Automatic Reference Counting (ARC) flag. ARC is a compiler feature 
                that provides automatic memory management of Objective-C objects and is an
                exploit mitigation mechanism against memory corruption vulnerabilities."""
                        }
        else:
            arc_flag = {"issue": "fobjc-arc flag is not Found",
                        "status": IN_SECURE,
                        "description": """App is not compiled with Automatic Reference Counting (ARC) flag. ARC is a compiler feature that
                provides automatic memory management of Objective-C objects and protects from
                memory corruption vulnerabilities."""
                        }

        banned_apis = {}
        baned = re.findall(
            b"_alloca|_gets|_memcpy|_printf|_scanf|_sprintf|_sscanf|_strcat|StrCat|_strcpy|" +
            b"StrCpy|_strlen|StrLen|_strncat|StrNCat|_strncpy|StrNCpy|_strtok|_swprintf|_vsnprintf|" +
            b"_vsprintf|_vswprintf|_wcscat|_wcscpy|_wcslen|_wcsncat|_wcsncpy|_wcstok|_wmemcpy|" +
            b"_fopen|_chmod|_chown|_stat|_mktemp", dat)
        baned = list(set(baned))
        baned_s = b', '.join(baned)
        if len(baned_s) > 1:
            banned_apis = {"issue": "Binary make use of banned API(s)",
                           "status": IN_SECURE,
                           "description": "The binary may contain the following banned API(s) " + baned_s.decode('utf-8', 'ignore') + "."
                           }
        weak_cryptos = {}
        weak_algo = re.findall(
            b"kCCAlgorithmDES|kCCAlgorithm3DES||kCCAlgorithmRC2|kCCAlgorithmRC4|" +
            b"kCCOptionECBMode|kCCOptionCBCMode", dat)
        weak_algo = list(set(weak_algo))
        weak_algo_s = b', '.join(weak_algo)
        if len(weak_algo_s) > 1:
            weak_cryptos = {"issue": "Binary make use of some Weak Crypto API(s)",
                            "status": IN_SECURE,
                            "description": "The binary may use the following weak crypto API(s) " + weak_algo_s.decode('utf-8', 'ignore') + "."
                            }
        crypto = {}
        crypto_algo = re.findall(
            b"CCKeyDerivationPBKDF|CCCryptorCreate|CCCryptorCreateFromData|" +
            b"CCCryptorRelease|CCCryptorUpdate|CCCryptorFinal|CCCryptorGetOutputLength|" +
            b"CCCryptorReset|CCCryptorRef|kCCEncrypt|kCCDecrypt|kCCAlgorithmAES128|" +
            b"kCCKeySizeAES128|kCCKeySizeAES192|kCCKeySizeAES256|kCCAlgorithmCAST|" +
            b"SecCertificateGetTypeID|SecIdentityGetTypeID|SecKeyGetTypeID|SecPolicyGetTypeID|" +
            b"SecTrustGetTypeID|SecCertificateCreateWithData|SecCertificateCreateFromData|" +
            b"SecCertificateCopyData|SecCertificateAddToKeychain|SecCertificateGetData|" +
            b"SecCertificateCopySubjectSummary|SecIdentityCopyCertificate|" +
            b"SecIdentityCopyPrivateKey|SecPKCS12Import|SecKeyGeneratePair|SecKeyEncrypt|" +
            b"SecKeyDecrypt|SecKeyRawSign|SecKeyRawVerify|SecKeyGetBlockSize|" +
            b"SecPolicyCopyProperties|SecPolicyCreateBasicX509|SecPolicyCreateSSL|" +
            b"SecTrustCopyCustomAnchorCertificates|SecTrustCopyExceptions|" +
            b"SecTrustCopyProperties|SecTrustCopyPolicies|SecTrustCopyPublicKey|" +
            b"SecTrustCreateWithCertificates|SecTrustEvaluate|SecTrustEvaluateAsync|" +
            b"SecTrustGetCertificateCount|SecTrustGetCertificateAtIndex|SecTrustGetTrustResult|" +
            b"SecTrustGetVerifyTime|SecTrustSetAnchorCertificates|" +
            b"SecTrustSetAnchorCertificatesOnly|SecTrustSetExceptions|SecTrustSetPolicies|" +
            b"SecTrustSetVerifyDate|SecCertificateRef|" +
            b"SecIdentityRef|SecKeyRef|SecPolicyRef|SecTrustRef", dat)
        crypto_algo = list(set(crypto_algo))
        crypto_algo_s = b', '.join(crypto_algo)
        if len(crypto_algo_s) > 1:
            crypto = {"issue": "Binary make use of the following Crypto API(s)",
                      "status": "Info",
                      "description": "The binary may use the following crypto API(s) " + crypto_algo_s.decode('utf-8', 'ignore') + "."
                      }
        weak_hashes = {}
        weak_hash_algo = re.findall(
            b"CC_MD2_Init|CC_MD2_Update|CC_MD2_Final|CC_MD2|MD2_Init|" +
            b"MD2_Update|MD2_Final|CC_MD4_Init|CC_MD4_Update|CC_MD4_Final|CC_MD4|MD4_Init|" +
            b"MD4_Update|MD4_Final|CC_MD5_Init|CC_MD5_Update|CC_MD5_Final|CC_MD5|MD5_Init|" +
            b"MD5_Update|MD5_Final|MD5Init|MD5Update|MD5Final|CC_SHA1_Init|CC_SHA1_Update|" +
            b"CC_SHA1_Final|CC_SHA1|SHA1_Init|SHA1_Update|SHA1_Final", dat)
        weak_hash_algo = list(set(weak_hash_algo))
        weak_hash_algo_s = b', '.join(weak_hash_algo)
        if len(weak_hash_algo_s) > 1:
            weak_hashe = {"issue": "Binary make use of the following Weak HASH API(s)",
                          "status": IN_SECURE,
                          "description": "The binary may use the following weak hash API(s) " + weak_hash_algo_s.decode('utf-8', 'ignore') + "."
                          }
        hashes = {}
        hash_algo = re.findall(
            b"CC_SHA224_Init|CC_SHA224_Update|CC_SHA224_Final|CC_SHA224|" +
            b"SHA224_Init|SHA224_Update|SHA224_Final|CC_SHA256_Init|CC_SHA256_Update|" +
            b"CC_SHA256_Final|CC_SHA256|SHA256_Init|SHA256_Update|SHA256_Final|" +
            b"CC_SHA384_Init|CC_SHA384_Update|CC_SHA384_Final|CC_SHA384|SHA384_Init|" +
            b"SHA384_Update|SHA384_Final|CC_SHA512_Init|CC_SHA512_Update|CC_SHA512_Final|" +
            b"CC_SHA512|SHA512_Init|SHA512_Update|SHA512_Final", dat)
        hash_algo = list(set(hash_algo))
        hash_algo_s = b', '.join(hash_algo)
        if len(hash_algo_s) > 1:
            hashes = {"issue": "Binary make use of the following HASH API(s)",
                      "status": INFO,
                      "description": "The binary may use the following hash API(s) " + hash_algo_s.decode('utf-8', 'ignore') + "."
                      }
        randoms = {}
        rand_algo = re.findall(b"_srand|_random", dat)
        rand_algo = list(set(rand_algo))
        rand_algo_s = b', '.join(rand_algo)
        if len(rand_algo_s) > 1:
            randoms = {"issue": "Binary make use of the insecure Random Function(s)",
                       "status": IN_SECURE,
                       "description": "The binary may use the following insecure Random Function(s) " + rand_algo_s.decode('utf-8', 'ignore') + "."
                       }
        logging = {}
        log = re.findall(b"_NSLog", dat)
        log = list(set(log))
        log_s = b', '.join(log)
        if len(log_s) > 1:
            logging = {"issue": "Binary make use of Logging Function",
                       "status": INFO,
                       "description": "The binary may use NSLog function for logging."
                       }
        malloc = {}

        mal = re.findall(b"_malloc", dat)
        mal = list(set(mal))
        mal_s = b', '.join(mal)
        if len(mal_s) > 1:
            malloc = {"issue": "Binary make use of malloc Function",
                      "status": IN_SECURE,
                      "description": "The binary may use malloc function instead of calloc."
                      }
        debug = {}

        ptrace = re.findall(b"_ptrace", dat)
        ptrace = list(set(ptrace))
        ptrace_s = b', '.join(ptrace)
        if len(ptrace_s) > 1:
            debug = {"issue": "Binary calls ptrace Function for anti-debugging.",
                     "status": WARNING,
                     "description": """The binary may use ptrace function. It can be used to detect and prevent debuggers. 
                            Ptrace is not a public API and Apps that use non-public APIs will be rejected from AppStore. """
                     }
        otool_dict["anal"] = [pie_flag, ssmash, arc_flag, banned_apis, weak_cryptos,
                              crypto, weak_hashes, hashes, randoms, logging, malloc, debug]
        return otool_dict
    except:
        PrintException("Performing Object Analysis of Binary")