    def wrapper(*args, **kwargs):
        queue = Queue()
        proc = Process(target=inner_f, args=(queue, func, *args), kwargs=kwargs)
        proc.start()
        proc.join(TPU_CHECK_TIMEOUT)
        try:
            return queue.get_nowait()
        except q.Empty:
            traceback.print_exc()
            return False