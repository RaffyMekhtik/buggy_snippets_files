def _get_tree_infos_from_onnx_ml_operator(model):
    """
    Function used to extract the parameters from a ONNXML TreeEnsemble model.
    """
    tree_infos = []
    left = right = features = values = threshold = None
    tree_ids = target_node_ids = target_tree_ids = modes = None
    classes = post_transform = None

    # The list of attributes is a merge between the classifier and regression operators.
    # The operators descriptions can be found here
    # https://github.com/onnx/onnx/blob/master/docs/Operators-ml.md#aionnxmltreeensembleclassifier and
    # here https://github.com/onnx/onnx/blob/master/docs/Operators-ml.md#aionnxmltreeensembleregressor
    for attr in model.origin.attribute:
        if attr.name == "nodes_falsenodeids":
            right = attr.ints
        elif attr.name == "nodes_truenodeids":
            left = attr.ints
        elif attr.name == "nodes_featureids":
            features = attr.ints
        elif attr.name == "nodes_values":
            threshold = attr.floats
        elif attr.name == "class_weights" or attr.name == "target_weights":
            values = attr.floats
        elif attr.name == "class_nodeids" or attr.name == "target_nodeids":
            target_node_ids = attr.ints
        elif attr.name == "class_treeids" or attr.name == "target_treeids":
            target_tree_ids = attr.ints
        elif attr.name == "nodes_treeids":
            tree_ids = attr.ints
        elif attr.name == "classlabels_int64s":
            classes = attr.ints
        elif attr.name == "classlabels_strings ":
            if len(attr.strings) > 0:
                raise AssertionError("String class labels not supported yet.")
        elif attr.name == "post_transform":
            post_transform = attr.s.decode("utf-8")
            if post_transform not in ["NONE", "LOGISTIC", "SOFTMAX"]:
                raise AssertionError("Post transform {} not supported".format(post_transform))
        elif attr.name == "nodes_modes":
            modes = attr.strings
            for mode in modes:
                if (not mode == b"BRANCH_LEQ") and (not mode == b"LEAF"):
                    raise AssertionError("Modality {} not supported".format(mode))

    is_decision_tree = post_transform == "NONE"
    # Order values based on target node and tree ids.
    new_values = []
    n_classes = 1 if classes is None or not is_decision_tree else len(classes)
    j = 0
    for i in range(max(target_tree_ids) + 1):
        k = j
        while k < len(target_tree_ids) and target_tree_ids[k] == i:
            k += 1
        target_ids = target_node_ids[j:k]
        target_ids_zipped = dict(zip(target_ids, range(len(target_ids))))
        for key in sorted(target_ids_zipped):
            if is_decision_tree and n_classes > 2:  # For multiclass we have 2d arrays.
                tmp_values = []
                for c in range(n_classes):
                    tmp_values.append(values[j + c + (target_ids_zipped[key] - (n_classes - 1))])
                new_values.append(tmp_values)
            else:
                new_values.append(values[j + target_ids_zipped[key]])
        j = k

    values = new_values
    i = 0
    prev_id = 0
    count = 0
    l_count = 0
    for n, id in enumerate(tree_ids):
        if id == i:
            if modes[n] == b"LEAF":
                left[n] = -1
                right[n] = -1
                threshold[n] = -1
        else:
            t_left = left[prev_id:count]
            t_right = right[prev_id:count]
            t_features = features[prev_id:count]
            t_threshold = threshold[prev_id:count]
            t_values = np.zeros((len(t_left), n_classes)) if is_decision_tree else np.zeros(len(t_left))
            if len(t_left) == 1:
                # Model creating trees with just a single leaf node. We transform it
                # to a model with one internal node.
                t_left = [1, -1, -1]
                t_right = [2, -1, -1]
                t_features = [0, 0, 0]
                t_threshold = [0, -1, -1]
                if l_count < len(values):
                    t_values[0] = values[l_count]
                    l_count += 1
            else:
                for j in range(len(t_left)):
                    if t_threshold[j] == -1 and l_count < len(values):
                        t_values[j] = values[l_count]
                        l_count += 1
            if t_values.shape[0] == 1:
                # Model creating trees with just a single leaf node. We fix the values here.
                n_classes = t_values.shape[1]
                t_values = np.array([np.array([0.0]), t_values[0], t_values[0]])
                t_values.reshape(3, n_classes)
            if is_decision_tree and n_classes == 2:  # We need to fix the probabilities in this case.
                for k in range(len(t_left)):
                    prob = (1 / (max(tree_ids) + 1)) - t_values[k][1]
                    t_values[k][0] = prob

            tree_infos.append(
                TreeParameters(t_left, t_right, t_features, t_threshold, np.array(t_values).reshape(-1, n_classes))
            )
            prev_id = count
            i += 1
        count += 1

    t_left = left[prev_id:count]
    t_right = right[prev_id:count]
    t_features = features[prev_id:count]
    t_threshold = threshold[prev_id:count]
    t_values = np.zeros((len(t_left), n_classes)) if is_decision_tree else np.zeros(len(t_left))
    if len(t_left) == 1:
        # Model creating trees with just a single leaf node. We transform it
        # to a model with one internal node.
        t_left = [1, -1, -1]
        t_right = [2, -1, -1]
        t_features = [0, 0, 0]
        t_threshold = [0, -1, -1]
        if l_count < len(values):
            t_values[0] = values[l_count]
            l_count += 1
    else:
        for j in range(len(t_left)):
            if t_threshold[j] == -1 and l_count < len(values):
                t_values[j] = values[l_count]
                l_count += 1
    if t_values.shape[0] == 1:
        # Model creating trees with just a single leaf node. We fix the values here.
        n_classes = t_values.shape[1]
        t_values = np.array([np.array([0.0]), t_values[0], t_values[0]])
        t_values.reshape(3, n_classes)
    if is_decision_tree and n_classes == 2:  # We need to fix the probabilities in this case.
        for k in range(len(t_left)):
            prob = (1 / (max(tree_ids) + 1)) - t_values[k][1]
            t_values[k][0] = prob
    tree_infos.append(TreeParameters(t_left, t_right, t_features, t_threshold, np.array(t_values).reshape(-1, n_classes)))
    return tree_infos, classes, post_transform