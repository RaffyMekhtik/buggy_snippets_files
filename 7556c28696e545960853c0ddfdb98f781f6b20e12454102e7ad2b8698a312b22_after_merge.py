def tika_convert_files_to_dicts(
        dir_path: str,
        clean_func: Optional[Callable] = None,
        split_paragraphs: bool = False,
        merge_short: bool = True,
        merge_lowercase: bool = True
) -> List[dict]:
    """
    Convert all files(.txt, .pdf) in the sub-directories of the given path to Python dicts that can be written to a
    Document Store.

    :param merge_lowercase: allow conversion of merged paragraph to lowercase
    :param merge_short: allow merging of short paragraphs
    :param dir_path: path for the documents to be written to the DocumentStore
    :param clean_func: a custom cleaning function that gets applied to each doc (input: str, output:str)
    :param split_paragraphs: split text in paragraphs.

    :return: None
    """
    converter = TikaConverter(remove_header_footer=True)
    paths = [p for p in Path(dir_path).glob("**/*")]
    allowed_suffixes = [".pdf", ".txt"]
    file_paths: List[Path] = []

    for path in paths:
        file_suffix = path.suffix.lower()
        if file_suffix in allowed_suffixes:
            file_paths.append(path)
        elif not path.is_dir():
            logger.warning('Skipped file {0} as type {1} is not supported here. '
                           'See haystack.file_converter for support of more file types'.format(path, file_suffix))

    documents = []
    for path in file_paths:
        logger.info('Converting {}'.format(path))
        document = converter.convert(path)
        meta = document["meta"] or {}
        meta["name"] = path.name
        text = document["text"]
        pages = text.split("\f")

        if split_paragraphs:
            if pages:
                paras = pages[0].split("\n\n")
                # pop the last paragraph from the first page
                last_para = paras.pop(-1) if paras else ''
                for page in pages[1:]:
                    page_paras = page.split("\n\n")
                    # merge the last paragraph in previous page to the first paragraph in this page
                    if page_paras:
                        page_paras[0] = last_para + ' ' + page_paras[0]
                        last_para = page_paras.pop(-1)
                        paras += page_paras
                if last_para:
                    paras.append(last_para)
                if paras:
                    last_para = ''
                    for para in paras:
                        para = para.strip()
                        if not para: continue
                        # merge paragraphs to improve qa
                        # merge this paragraph if less than 10 characters or 2 words
                        # or this paragraph starts with a lower case and last paragraph does not end with a punctuation
                        if merge_short and len(para) < 10 or len(re.findall('\s+', para)) < 2 \
                            or merge_lowercase and para and para[0].islower() and last_para and last_para[-1] not in '.?!"\'\]\)':
                            last_para += ' ' + para
                        else:
                            if last_para:
                                documents.append({"text": last_para, "meta": meta})
                            last_para = para
                    # don't forget the last one
                    if last_para:
                        documents.append({"text": last_para, "meta": meta})
        else:
            if clean_func:
                text = clean_func(text)
            documents.append({"text": text, "meta": meta})

    return documents