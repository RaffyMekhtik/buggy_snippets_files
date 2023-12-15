    def __gather_minions(self):
        '''
        Return a list of minions to use for the batch run
        '''
        args = [self.opts['tgt'],
                'test.ping',
                [],
                self.opts['timeout'],
                ]

        selected_target_option = self.opts.get('selected_target_option', None)
        if selected_target_option is not None:
            args.append(selected_target_option)
        else:
            args.append(self.opts.get('expr_form', 'glob'))

        ping_gen = self.local.cmd_iter(*args, **self.eauth)

        # Broadcast to targets
        fret = set()
        try:
            for ret in ping_gen:
                m = next(six.iterkeys(ret))
                if m is not None:
                    fret.add(m)
        except StopIteration:
            if not self.quiet:
                print_cli('No minions matched the target.')
        return list(fret), ping_gen