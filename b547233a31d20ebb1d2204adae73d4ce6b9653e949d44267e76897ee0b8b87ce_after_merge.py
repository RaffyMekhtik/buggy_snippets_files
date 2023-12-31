    def _get_unique_task_id(
        task_id: str, dag: Optional[DAG] = None, task_group: Optional[TaskGroup] = None
    ) -> str:
        """
        Generate unique task id given a DAG (or if run in a DAG context)
        Ids are generated by appending a unique number to the end of
        the original task id.

        Example:
          task_id
          task_id__1
          task_id__2
          ...
          task_id__20
        """
        dag = dag or DagContext.get_current_dag()
        if not dag:
            return task_id

        # We need to check if we are in the context of TaskGroup as the task_id may
        # already be altered
        task_group = task_group or TaskGroupContext.get_current_task_group(dag)
        tg_task_id = task_group.child_id(task_id) if task_group else task_id

        if tg_task_id not in dag.task_ids:
            return task_id
        core = re.split(r'__\d+$', task_id)[0]
        suffixes = sorted(
            [
                int(re.split(r'^.+__', task_id)[1])
                for task_id in dag.task_ids
                if re.match(rf'^{core}__\d+$', task_id)
            ]
        )
        if not suffixes:
            return f'{core}__1'
        return f'{core}__{suffixes[-1] + 1}'