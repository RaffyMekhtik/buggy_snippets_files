    def train(cls, wr_path, corpus_file, out_name, size=100, window=15, symmetric=1, min_count=5, max_vocab_size=0,
              sgd_num=100, lrate=0.001, period=10, iter=90, epsilon=0.75, dump_period=10, reg=0, alpha=100,
              beta=99, loss='hinge', memory=4.0, cleanup_files=False, sorted_vocab=1, ensemble=0):
        """
        The word and context embedding files are generated by wordrank binary and are saved in "out_name" directory
        which is created inside wordrank directory. The vocab and cooccurence files are generated using glove code
        available inside the wordrank directory. These files are used by the wordrank binary for training.

        `wr_path` is the path to the Wordrank directory.
        `corpus_file` is the filename of the text file to be used for training the Wordrank model.
        Expects file to contain space-separated tokens in a single line
        `out_name` is name of the directory which will be created (in wordrank folder) to save embeddings and training data.
        It will contain following contents:

            Word Embeddings saved after every dump_period and stored in a file model_word_current\ iter.txt
            Context Embeddings saved after every dump_period and stored in a file model_context_current\ iter.txt
            A meta directory which contain: 'vocab.txt' - vocab words, 'wiki.toy' - word-word coccurence values, 'meta' - vocab and coccurence lengths

        `size` is the dimensionality of the feature vectors.
        `window` is the number of context words to the left (and to the right, if symmetric = 1).
        `symmetric` if 0, only use left context words, else use left and right both.
        `min_count` = ignore all words with total frequency lower than this.
        `max_vocab_size` upper bound on vocabulary size, i.e. keep the <int> most frequent words. Default is 0 for no limit.
        `sgd_num` number of SGD taken for each data point.
        `lrate` is the learning rate (too high diverges, give Nan).
        `period` is the period of xi variable updates
        `iter` = number of iterations (epochs) over the corpus.
        `epsilon` is the power scaling value for weighting function.
        `dump_period` is the period after which embeddings should be dumped.
        `reg` is the value of regularization parameter.
        `alpha` is the alpha parameter of gamma distribution.
        `beta` is the beta parameter of gamma distribution.
        `loss` = name of the loss (logistic, hinge).
        `memory` = soft limit for memory consumption, in GB.
        `cleanup_files` if True, delete directory and files used by this wrapper, setting to False can be useful for debugging
        `sorted_vocab` = if 1 (default), sort the vocabulary by descending frequency before assigning word indexes.
        `ensemble` = 0 (default), use ensemble of word and context vectors
        """

        meta_data_path = 'matrix.meta'
        vocab_file = 'vocab.txt'
        temp_vocab_file = 'tempvocab.txt'
        cooccurrence_file = 'cooccurrence'
        cooccurrence_shuf_file = 'wiki.toy'
        meta_file = 'meta'

        # prepare training data (cooccurrence matrix and vocab)
        model_dir = os.path.join(wr_path, out_name)
        meta_dir = os.path.join(model_dir, 'meta')
        os.makedirs(meta_dir)
        logger.info("Dumped data will be stored in '%s'", model_dir)
        copyfile(corpus_file, os.path.join(meta_dir, corpus_file.split('/')[-1]))
        os.chdir(meta_dir)

        cmd_vocab_count = ['../../glove/vocab_count', '-min-count', str(min_count), '-max-vocab', str(max_vocab_size)]
        cmd_cooccurence_count = ['../../glove/cooccur', '-memory', str(memory), '-vocab-file', temp_vocab_file, '-window-size', str(window), '-symmetric', str(symmetric)]
        cmd_shuffle_cooccurences = ['../../glove/shuffle', '-memory', str(memory)]
        cmd_del_vocab_freq = ['cut', '-d', " ", '-f', '1', temp_vocab_file]

        commands = [cmd_vocab_count, cmd_cooccurence_count, cmd_shuffle_cooccurences]
        input_fnames = [corpus_file.split('/')[-1], corpus_file.split('/')[-1], cooccurrence_file]
        output_fnames = [temp_vocab_file, cooccurrence_file, cooccurrence_shuf_file]

        logger.info("Prepare training data (%s) using glove code", ", ".join(input_fnames))
        for command, input_fname, output_fname in zip(commands, input_fnames, output_fnames):
            with smart_open(input_fname, 'rb') as r:
                with smart_open(output_fname, 'wb') as w:
                    utils.check_output(w, args=command, stdin=r)

        logger.info("Deleting frequencies from vocab file")
        with smart_open(vocab_file, 'wb') as w:
            utils.check_output(w, args=cmd_del_vocab_freq)

        with smart_open(vocab_file, 'rb') as f:
            numwords = sum(1 for line in f)
        with smart_open(cooccurrence_shuf_file, 'rb') as f:
            numlines = sum(1 for line in f)
        with smart_open(meta_file, 'wb') as f:
            meta_info = "{0} {1}\n{2} {3}\n{4} {5}".format(numwords, numwords, numlines, cooccurrence_shuf_file, numwords, vocab_file)
            f.write(meta_info.encode('utf-8'))
            
        if iter % dump_period == 0:
            iter += 1
        else:
            logger.warning(
                'Resultant embedding will be from %d iterations rather than the input %d iterations, '
                'as wordrank dumps the embedding only at dump_period intervals. '
                'Input an appropriate combination of parameters (iter, dump_period) such that '
                '"iter mod dump_period" is zero.', iter - (iter % dump_period), iter
                )

        wr_args = {
            'path': 'meta',
            'nthread': multiprocessing.cpu_count(),
            'sgd_num': sgd_num,
            'lrate': lrate,
            'period': period,
            'iter': iter,
            'epsilon': epsilon,
            'dump_prefix': 'model',
            'dump_period': dump_period,
            'dim': size,
            'reg': reg,
            'alpha': alpha,
            'beta': beta,
            'loss': loss
        }

        os.chdir('..')
        # run wordrank executable with wr_args
        cmd = ['mpirun', '-np', '1', '../wordrank']
        for option, value in wr_args.items():
            cmd.append('--%s' % option)
            cmd.append(str(value))
        logger.info("Running wordrank binary")
        output = utils.check_output(args=cmd)

        # use embeddings from max. iteration's dump
        max_iter_dump = iter - (iter % dump_period)
        copyfile('model_word_%d.txt' % max_iter_dump, 'wordrank.words')
        copyfile('model_context_%d.txt' % max_iter_dump, 'wordrank.contexts')
        model = cls.load_wordrank_model('wordrank.words', os.path.join('meta', vocab_file), 'wordrank.contexts', sorted_vocab, ensemble)
        os.chdir('../..')

        if cleanup_files:
            rmtree(model_dir)
        return model