    def update_to(self, fraction):
        try:
            if self.json and self.enabled:
                sys.stdout.write('{"fetch":"%s","finished":false,"maxval":1,"progress":%f}\n\0'
                                 % (self.description, fraction))
            elif self.enabled:
                self.pbar.update(fraction - self.pbar.n)
        except EnvironmentError as e:
            if e.errno in (EPIPE, ESHUTDOWN):
                self.enabled = False
            else:
                raise