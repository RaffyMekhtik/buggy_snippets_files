    def fqscreen_simple_plot(self):
        """ Makes a simple bar plot with summed alignment counts for
        each species, stacked. """

        # First, sum the different types of alignment counts
        data = OrderedDict()
        cats = OrderedDict()
        for s_name in self.fq_screen_data:
            data[s_name] = OrderedDict()
            sum_alignments = 0
            for org in self.fq_screen_data[s_name]:
                if org == 'total_reads':
                    continue
                try:
                    data[s_name][org] = self.fq_screen_data[s_name][org]['counts']['one_hit_one_library']
                except KeyError:
                    log.error("No counts found for '{}' ('{}'). Could be malformed or very old FastQ Screen results.".format(org, s_name))
                    continue
                try:
                    data[s_name][org] += self.fq_screen_data[s_name][org]['counts']['multiple_hits_one_library']
                except KeyError:
                    pass
                sum_alignments += data[s_name][org]
                if org not in cats and org != 'No hits':
                    cats[org] = { 'name': org }

            # Calculate hits in multiple genomes
            if 'total_reads' in self.fq_screen_data[s_name]:
                data[s_name]['Multiple Genomes'] = self.fq_screen_data[s_name]['total_reads'] - sum_alignments

        # Strip empty dicts
        data = [data[s_name] for s_name in data if len(data[s_name]) > 0]

        pconfig = {
            'id': 'fastq_screen',
            'title': 'FastQ Screen',
            'cpswitch_c_active': False
        }
        cats['Multiple Genomes'] = { 'name': 'Multiple Genomes', 'color': '#820000' }
        cats['No hits'] = { 'name': 'No hits', 'color': '#cccccc' }

        return bargraph.plot(data, cats, pconfig)