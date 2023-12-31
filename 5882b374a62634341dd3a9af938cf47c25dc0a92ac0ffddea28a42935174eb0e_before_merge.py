    def save_datasource(self, name, source_type, source, file_path=None):
        if source_type == 'file' and (file_path is None):
            raise Exception('`file_path` argument required when source_type == "file"')

        for i in range(1, 1000):
            if name in [x['name'] for x in self.get_datasources()]:
                previous_index = i - 1
                name = name.replace(f'__{previous_index}__', '')
                name = f'{name}__{i}__'
            else:
                break

        ds_meta_dir = os.path.join(self.dir, name)
        os.mkdir(ds_meta_dir)

        ds_dir = os.path.join(ds_meta_dir, 'datasource')
        os.mkdir(ds_dir)

        if source_type == 'file':
            try:
                source = os.path.join(ds_dir, source)
                os.replace(file_path, source)
                ds = FileDS(source)
            except Exception:
                shutil.rmtree(ds_meta_dir)
                raise

            picklable = {
                'class': 'FileDS',
                'args': [source],
                'kwargs': {}
            }
        elif source_type in self.config['integrations']:
            integration = self.config['integrations'][source_type]
            dsClass = None
            picklable = {
                'args': [],
                'kwargs': {
                    'query': source,
                    'user': integration['user'],
                    'password': integration['password'],
                    'host': integration['host'],
                    'port': integration['port']
                }
            }
            if integration['type'] == 'clickhouse':
                dsClass = ClickhouseDS
                picklable['class'] = 'ClickhouseDS'
            elif integration['type'] == 'mariadb':
                dsClass = MariaDS
                picklable['class'] = 'MariaDS'
            elif integration['type'] == 'mysql':
                dsClass = MySqlDS
                picklable['class'] = 'MySqlDS'
            elif integration['type'] == 'postgres':
                dsClass = PostgresDS
                picklable['class'] = 'PostgresDS'
            else:
                raise ValueError(f'Unknown DS source_type: {source_type}')
            try:
                ds = dsClass(
                    query=source,
                    user=integration['user'],
                    password=integration['password'],
                    host=integration['host'],
                    port=integration['port']
                )
            except Exception:
                shutil.rmtree(ds_meta_dir)
                raise
        else:
            # This probably only happens for urls
            print('Create URL data source !')
            try:
                ds = FileDS(source)
            except Exception:
                shutil.rmtree(ds_meta_dir)
                raise
            picklable = {
                'class': 'FileDS',
                'args': [source],
                'kwargs': {}
            }

        df = ds.df

        df_with_types = cast_df_columns_types(df, self.get_analysis(df)['data_analysis_v2'])
        create_sqlite_db(os.path.join(ds_dir, 'sqlite.db'), df_with_types)

        with open(os.path.join(ds_dir, 'ds.pickle'), 'wb') as fp:
            pickle.dump(picklable, fp)

        with open(os.path.join(ds_dir, 'metadata.json'), 'w') as fp:
            meta = {
                'name': name,
                'source_type': source_type,
                'source': source,
                'created_at': str(datetime.datetime.now()).split('.')[0],
                'updated_at': str(datetime.datetime.now()).split('.')[0],
                'row_count': len(df),
                'columns': [dict(name=x) for x in list(df.keys())]
            }
            json.dump(meta, fp)

        return self.get_datasource_obj(name, raw=True), name