def train(args):
    # parameters from arguments
    class_dim = args.class_dim
    model_name = args.model
    checkpoint = args.checkpoint
    pretrained_model = args.pretrained_model
    with_memory_optimization = args.with_mem_opt
    model_save_dir = args.model_save_dir
    image_shape = [int(m) for m in args.image_shape.split(",")]

    assert model_name in model_list, "{} is not in lists: {}".format(args.model,
                                                                     model_list)

    image = fluid.layers.data(name='image', shape=image_shape, dtype='float32')
    label = fluid.layers.data(name='label', shape=[1], dtype='int64')

    # model definition
    model = models.__dict__[model_name]()

    if model_name is "GoogleNet":
        out0, out1, out2 = model.net(input=image, class_dim=class_dim)
        cost0 = fluid.layers.cross_entropy(input=out0, label=label)
        cost1 = fluid.layers.cross_entropy(input=out1, label=label)
        cost2 = fluid.layers.cross_entropy(input=out2, label=label)
        avg_cost0 = fluid.layers.mean(x=cost0)
        avg_cost1 = fluid.layers.mean(x=cost1)
        avg_cost2 = fluid.layers.mean(x=cost2)

        avg_cost = avg_cost0 + 0.3 * avg_cost1 + 0.3 * avg_cost2
        acc_top1 = fluid.layers.accuracy(input=out0, label=label, k=1)
        acc_top5 = fluid.layers.accuracy(input=out0, label=label, k=5)
    else:
        out = model.net(input=image, class_dim=class_dim)
        cost = fluid.layers.cross_entropy(input=out, label=label)

        avg_cost = fluid.layers.mean(x=cost)
        acc_top1 = fluid.layers.accuracy(input=out, label=label, k=1)
        acc_top5 = fluid.layers.accuracy(input=out, label=label, k=5)

    test_program = fluid.default_main_program().clone(for_test=True)

    # parameters from model and arguments
    params = model.params
    params["total_images"] = args.total_images
    params["lr"] = args.lr
    params["num_epochs"] = args.num_epochs
    params["learning_strategy"]["batch_size"] = args.batch_size
    params["learning_strategy"]["name"] = args.lr_strategy

    # initialize optimizer
    optimizer = optimizer_setting(params)
    opts = optimizer.minimize(avg_cost)

    if with_memory_optimization:
        fluid.memory_optimize(fluid.default_main_program())

    place = fluid.CUDAPlace(0) if args.use_gpu else fluid.CPUPlace()
    exe = fluid.Executor(place)
    exe.run(fluid.default_startup_program())

    if checkpoint is not None:
        fluid.io.load_persistables(exe, checkpoint)

    if pretrained_model:

        def if_exist(var):
            return os.path.exists(os.path.join(pretrained_model, var.name))

        fluid.io.load_vars(exe, pretrained_model, predicate=if_exist)

    train_batch_size = args.batch_size
    test_batch_size = 16
    train_reader = paddle.batch(reader.train(), batch_size=train_batch_size)
    test_reader = paddle.batch(reader.val(), batch_size=test_batch_size)
    feeder = fluid.DataFeeder(place=place, feed_list=[image, label])

    train_exe = fluid.ParallelExecutor(
        use_cuda=True if args.use_gpu else False, loss_name=avg_cost.name)

    fetch_list = [avg_cost.name, acc_top1.name, acc_top5.name]

    for pass_id in range(params["num_epochs"]):
        train_info = [[], [], []]
        test_info = [[], [], []]
        for batch_id, data in enumerate(train_reader()):
            t1 = time.time()
            loss, acc1, acc5 = train_exe.run(fetch_list, feed=feeder.feed(data))
            t2 = time.time()
            period = t2 - t1
            loss = np.mean(np.array(loss))
            acc1 = np.mean(np.array(acc1))
            acc5 = np.mean(np.array(acc5))
            train_info[0].append(loss)
            train_info[1].append(acc1)
            train_info[2].append(acc5)
            if batch_id % 10 == 0:
                print("Pass {0}, trainbatch {1}, loss {2}, \
                       acc1 {3}, acc5 {4} time {5}"
                                                   .format(pass_id, \
                       batch_id, loss, acc1, acc5, \
                       "%2.2f sec" % period))
                sys.stdout.flush()

        train_loss = np.array(train_info[0]).mean()
        train_acc1 = np.array(train_info[1]).mean()
        train_acc5 = np.array(train_info[2]).mean()
        cnt = 0
        for test_batch_id, data in enumerate(test_reader()):
            t1 = time.time()
            loss, acc1, acc5 = exe.run(test_program,
                                       fetch_list=fetch_list,
                                       feed=feeder.feed(data))
            t2 = time.time()
            period = t2 - t1
            loss = np.mean(loss)
            acc1 = np.mean(acc1)
            acc5 = np.mean(acc5)
            test_info[0].append(loss * len(data))
            test_info[1].append(acc1 * len(data))
            test_info[2].append(acc5 * len(data))
            cnt += len(data)
            if test_batch_id % 10 == 0:
                print("Pass {0},testbatch {1},loss {2}, \
                       acc1 {3},acc5 {4},time {5}"
                                                  .format(pass_id, \
                       test_batch_id, loss, acc1, acc5, \
                       "%2.2f sec" % period))
                sys.stdout.flush()

        test_loss = np.sum(test_info[0]) / cnt
        test_acc1 = np.sum(test_info[1]) / cnt
        test_acc5 = np.sum(test_info[2]) / cnt

        print("End pass {0}, train_loss {1}, train_acc1 {2}, train_acc5 {3}, "
              "test_loss {4}, test_acc1 {5}, test_acc5 {6}".format(pass_id, \
              train_loss, train_acc1, train_acc5, test_loss, test_acc1, \
              test_acc5))
        sys.stdout.flush()

        model_path = os.path.join(model_save_dir + '/' + model_name,
                                  str(pass_id))
        if not os.path.isdir(model_path):
            os.makedirs(model_path)
        fluid.io.save_persistables(exe, model_path)