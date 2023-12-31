def code_analysis(app_dir, perms, typ):
    """Perform the code analysis."""
    try:
        logger.info("Static Android Code Analysis Started")
        api_rules = android_apis.APIS
        code_rules = android_rules.RULES
        code_findings = {}
        api_findings = {}
        email_n_file = []
        url_n_file = []
        url_list = []
        domains = {}

        if typ == "apk":
            java_src = os.path.join(app_dir, 'java_source/')
        elif typ == "studio":
            java_src = os.path.join(app_dir, 'app/src/main/java/')
        elif typ == "eclipse":
            java_src = os.path.join(app_dir, 'src/')
        logger.info("Code Analysis Started on - " + java_src)
        # pylint: disable=unused-variable
        # Needed by os.walk
        for dir_name, sub_dir, files in os.walk(java_src):
            for jfile in files:
                jfile_path = os.path.join(java_src, dir_name, jfile)
                if "+" in jfile:
                    p_2 = os.path.join(java_src, dir_name,
                                       jfile.replace("+", "x"))
                    shutil.move(jfile_path, p_2)
                    jfile_path = p_2
                repath = dir_name.replace(java_src, '')
                if (
                        jfile.endswith('.java') and
                        any(re.search(cls, repath)
                            for cls in settings.SKIP_CLASSES) is False
                ):
                    dat = ''
                    with io.open(
                        jfile_path,
                        mode='r',
                        encoding="utf8",
                        errors="ignore"
                    ) as file_pointer:
                        dat = file_pointer.read()

                    # Code Analysis
                    # print "[INFO] Doing Code Analysis on - " + jfile_path
                    relative_java_path = jfile_path.replace(java_src, '')
                    code_rule_matcher(
                        code_findings, list(perms.keys()), dat, relative_java_path, code_rules)
                    # API Check
                    api_rule_matcher(api_findings, list(perms.keys()),
                                     dat, relative_java_path, api_rules)
                     # Extract URLs and Emails
                    urls, urls_nf, emails_nf = url_n_email_extract(dat, relative_java_path)
                    url_list.extend(urls)
                    url_n_file.extend(urls_nf)
                    email_n_file.extend(emails_nf)
        # Domain Extraction and Malware Check
        logger.info("Performing Malware Check on extracted Domains")
        domains = malware_check(list(set(url_list)))
        logger.info("Finished Code Analysis, Email and URL Extraction")
        code_an_dic = {
            'api': api_findings,
            'findings': code_findings,
            'urls': url_n_file,
            'domains': domains,
            'emails': email_n_file,
        }
        return code_an_dic
    except:
        PrintException("[ERROR] Performing Code Analysis")