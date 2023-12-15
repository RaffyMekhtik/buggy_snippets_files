    def train(
        self,
        base_path: Union[Path, str],
        sequence_length: int,
        learning_rate: float = 20,
        mini_batch_size: int = 100,
        anneal_factor: float = 0.25,
        patience: int = 10,
        clip=0.25,
        max_epochs: int = 1000,
        checkpoint: bool = False,
        grow_to_sequence_length: int = 0,
        num_workers: int = 2,
        use_amp: bool = False,
        amp_opt_level: str = "O1",
        **kwargs,
    ):

        if use_amp:
            if sys.version_info < (3, 0):
                raise RuntimeError("Apex currently only supports Python 3. Aborting.")
            if amp is None:
                raise RuntimeError(
                    "Failed to import apex. Please install apex from https://www.github.com/nvidia/apex "
                    "to enable mixed-precision training."
                )

        # cast string to Path
        if type(base_path) is str:
            base_path = Path(base_path)

        add_file_handler(log, base_path / "training.log")

        number_of_splits: int = len(self.corpus.train)

        val_data = self._batchify(self.corpus.valid, mini_batch_size)

        # error message if the validation dataset is too small
        if val_data.size(0) == 1:
            raise RuntimeError(
                f"ERROR: Your validation dataset is too small. For your mini_batch_size, the data needs to "
                f"consist of at least {mini_batch_size * 2} characters!"
            )

        base_path.mkdir(parents=True, exist_ok=True)
        loss_txt = base_path / "loss.txt"
        savefile = base_path / "best-lm.pt"

        try:
            epoch = self.epoch
            best_val_loss = self.loss
            optimizer = self.optimizer(
                self.model.parameters(), lr=learning_rate, **kwargs
            )
            if self.optimizer_state is not None:
                optimizer.load_state_dict(self.optimizer_state)

            if isinstance(optimizer, (AdamW, SGDW)):
                scheduler: ReduceLRWDOnPlateau = ReduceLRWDOnPlateau(
                    optimizer, verbose=True, factor=anneal_factor, patience=patience
                )
            else:
                scheduler: ReduceLROnPlateau = ReduceLROnPlateau(
                    optimizer, verbose=True, factor=anneal_factor, patience=patience
                )

            if use_amp:
                self.model, optimizer = amp.initialize(
                    self.model, optimizer, opt_level=amp_opt_level
                )

            training_generator = DataLoader(
                self.corpus.train, shuffle=False, num_workers=num_workers
            )

            for epoch in range(self.epoch, max_epochs):
                epoch_start_time = time.time()
                # Shuffle training files randomly after serially iterating through corpus one
                if epoch > 0:
                    training_generator = DataLoader(
                        self.corpus.train, shuffle=True, num_workers=num_workers
                    )
                    self.model.save_checkpoint(
                        base_path / f"epoch_{epoch}.pt",
                        optimizer,
                        epoch,
                        0,
                        best_val_loss,
                    )

                # iterate through training data, starting at self.split (for checkpointing)
                for curr_split, train_slice in enumerate(
                    training_generator, self.split
                ):

                    if sequence_length < grow_to_sequence_length:
                        sequence_length += 1
                    log.info(f"Sequence length is {sequence_length}")

                    split_start_time = time.time()
                    # off by one for printing
                    curr_split += 1
                    train_data = self._batchify(train_slice.flatten(), mini_batch_size)

                    log.info(
                        "Split %d" % curr_split
                        + "\t - ({:%H:%M:%S})".format(datetime.datetime.now())
                    )

                    for group in optimizer.param_groups:
                        learning_rate = group["lr"]

                    # go into train mode
                    self.model.train()

                    # reset variables
                    hidden = self.model.init_hidden(mini_batch_size)

                    # not really sure what this does
                    ntokens = len(self.corpus.dictionary)

                    total_loss = 0
                    start_time = time.time()

                    for batch, i in enumerate(
                        range(0, train_data.size(0) - 1, sequence_length)
                    ):
                        data, targets = self._get_batch(train_data, i, sequence_length)

                        if not data.is_cuda and cuda.is_available():
                            log.info(
                                "Batch %d is not on CUDA, training will be very slow"
                                % (batch)
                            )
                            raise Exception("data isnt on cuda")

                        self.model.zero_grad()
                        optimizer.zero_grad()

                        # do the forward pass in the model
                        output, rnn_output, hidden = self.model.forward(data, hidden)

                        # try to predict the targets
                        loss = self.loss_function(output.view(-1, ntokens), targets)
                        # Backward
                        if use_amp:
                            with amp.scale_loss(loss, optimizer) as scaled_loss:
                                scaled_loss.backward()
                        else:
                            loss.backward()

                        # `clip_grad_norm` helps prevent the exploding gradient problem in RNNs / LSTMs.
                        torch.nn.utils.clip_grad_norm_(self.model.parameters(), clip)

                        optimizer.step()

                        total_loss += loss.data

                        # We detach the hidden state from how it was previously produced.
                        # If we didn't, the model would try backpropagating all the way to start of the dataset.
                        hidden = self._repackage_hidden(hidden)

                        # explicitly remove loss to clear up memory
                        del loss, output, rnn_output

                        if batch % self.log_interval == 0 and batch > 0:
                            cur_loss = total_loss.item() / self.log_interval
                            elapsed = time.time() - start_time
                            log.info(
                                "| split {:3d} /{:3d} | {:5d}/{:5d} batches | ms/batch {:5.2f} | "
                                "loss {:5.2f} | ppl {:8.2f}".format(
                                    curr_split,
                                    number_of_splits,
                                    batch,
                                    len(train_data) // sequence_length,
                                    elapsed * 1000 / self.log_interval,
                                    cur_loss,
                                    math.exp(cur_loss),
                                )
                            )
                            total_loss = 0
                            start_time = time.time()

                    log.info(
                        "%d seconds for train split %d"
                        % (time.time() - split_start_time, curr_split)
                    )

                    ###############################################################################
                    self.model.eval()

                    val_loss = self.evaluate(val_data, mini_batch_size, sequence_length)
                    scheduler.step(val_loss)

                    log.info("best loss so far {:5.2f}".format(best_val_loss))

                    log.info(self.model.generate_text())

                    if checkpoint:
                        self.model.save_checkpoint(
                            base_path / "checkpoint.pt",
                            optimizer,
                            epoch,
                            curr_split,
                            best_val_loss,
                        )

                    # Save the model if the validation loss is the best we've seen so far.
                    if val_loss < best_val_loss:
                        self.model.best_score = best_val_loss
                        self.model.save(savefile)
                        best_val_loss = val_loss

                    ###############################################################################
                    # print info
                    ###############################################################################
                    log.info("-" * 89)

                    summary = (
                        "| end of split {:3d} /{:3d} | epoch {:3d} | time: {:5.2f}s | valid loss {:5.2f} | "
                        "valid ppl {:8.2f} | learning rate {:3.4f}".format(
                            curr_split,
                            number_of_splits,
                            epoch + 1,
                            (time.time() - split_start_time),
                            val_loss,
                            math.exp(val_loss),
                            learning_rate,
                        )
                    )

                    with open(loss_txt, "a") as myfile:
                        myfile.write("%s\n" % summary)

                    log.info(summary)
                    log.info("-" * 89)

                log.info("Epoch time: %.2f" % (time.time() - epoch_start_time))

        except KeyboardInterrupt:
            log.info("-" * 89)
            log.info("Exiting from training early")

        ###############################################################################
        # final testing
        ###############################################################################
        test_data = self._batchify(self.corpus.test, mini_batch_size)
        test_loss = self.evaluate(test_data, mini_batch_size, sequence_length)

        summary = "TEST: valid loss {:5.2f} | valid ppl {:8.2f}".format(
            test_loss, math.exp(test_loss)
        )
        with open(loss_txt, "a") as myfile:
            myfile.write("%s\n" % summary)

        log.info(summary)
        log.info("-" * 89)