def present(
    name,
    tag=None,
    build=None,
    load=None,
    force=False,
    insecure_registry=False,
    client_timeout=salt.utils.docker.CLIENT_TIMEOUT,
    dockerfile=None,
    sls=None,
    base="opensuse/python",
    saltenv="base",
    pillarenv=None,
    pillar=None,
    **kwargs
):
    """
    .. versionchanged:: 2018.3.0
        The ``tag`` argument has been added. It is now required unless pulling
        from a registry.

    Ensure that an image is present. The image can either be pulled from a
    Docker registry, built from a Dockerfile, loaded from a saved image, or
    built by running SLS files against a base image.

    If none of the ``build``, ``load``, or ``sls`` arguments are used, then Salt
    will pull from the :ref:`configured registries <docker-authentication>`. If
    the specified image already exists, it will not be pulled unless ``force``
    is set to ``True``. Here is an example of a state that will pull an image
    from the Docker Hub:

    .. code-block:: yaml

        myuser/myimage:
          docker_image.present:
            - tag: mytag

    tag
        Tag name for the image. Required when using ``build``, ``load``, or
        ``sls`` to create the image, but optional if pulling from a repository.

        .. versionadded:: 2018.3.0

    build
        Path to directory on the Minion containing a Dockerfile

        .. code-block:: yaml

            myuser/myimage:
              docker_image.present:
                - build: /home/myuser/docker/myimage
                - tag: mytag

            myuser/myimage:
              docker_image.present:
                - build: /home/myuser/docker/myimage
                - tag: mytag
                - dockerfile: Dockerfile.alternative

        The image will be built using :py:func:`docker.build
        <salt.modules.dockermod.build>` and the specified image name and tag
        will be applied to it.

        .. versionadded:: 2016.11.0
        .. versionchanged:: 2018.3.0
            The ``tag`` must be manually specified using the ``tag`` argument.

    load
        Loads a tar archive created with :py:func:`docker.save
        <salt.modules.dockermod.save>` (or the ``docker save`` Docker CLI
        command), and assigns it the specified repo and tag.

        .. code-block:: yaml

            myuser/myimage:
              docker_image.present:
                - load: salt://path/to/image.tar
                - tag: mytag

        .. versionchanged:: 2018.3.0
            The ``tag`` must be manually specified using the ``tag`` argument.

    force : False
        Set this parameter to ``True`` to force Salt to pull/build/load the
        image even if it is already present.

    client_timeout
        Timeout in seconds for the Docker client. This is not a timeout for
        the state, but for receiving a response from the API.

    dockerfile
        Allows for an alternative Dockerfile to be specified.  Path to alternative
        Dockefile is relative to the build path for the Docker container.

        .. versionadded:: 2016.11.0

    sls
        Allow for building of image with :py:func:`docker.sls_build
        <salt.modules.dockermod.sls_build>` by specifying the SLS files with
        which to build. This can be a list or comma-seperated string.

        .. code-block:: yaml

            myuser/myimage:
              docker_image.present:
                - tag: latest
                - sls:
                    - webapp1
                    - webapp2
                - base: centos
                - saltenv: base

        .. versionadded: 2017.7.0
        .. versionchanged:: 2018.3.0
            The ``tag`` must be manually specified using the ``tag`` argument.

    base
        Base image with which to start :py:func:`docker.sls_build
        <salt.modules.dockermod.sls_build>`

        .. versionadded:: 2017.7.0

    saltenv
        Specify the environment from which to retrieve the SLS indicated by the
        `mods` parameter.

        .. versionadded:: 2017.7.0
        .. versionchanged:: 2018.3.0
            Now uses the effective saltenv if not explicitly passed. In earlier
            versions, ``base`` was assumed as a default.

    pillarenv
        Specify a Pillar environment to be used when applying states. This
        can also be set in the minion config file using the
        :conf_minion:`pillarenv` option. When neither the
        :conf_minion:`pillarenv` minion config option nor this CLI argument is
        used, all Pillar environments will be merged together.

        .. versionadded:: 2018.3.0

    pillar
        Custom Pillar values, passed as a dictionary of key-value pairs

        .. note::
            Values passed this way will override Pillar values set via
            ``pillar_roots`` or an external Pillar source.

        .. versionadded:: 2018.3.0
    """
    ret = {"name": name, "changes": {}, "result": False, "comment": ""}

    if not isinstance(name, six.string_types):
        name = six.text_type(name)

    # At most one of the args that result in an image being built can be used
    num_build_args = len([x for x in (build, load, sls) if x is not None])
    if num_build_args > 1:
        ret["comment"] = "Only one of 'build', 'load', or 'sls' is permitted."
        return ret
    elif num_build_args == 1:
        # If building, we need the tag to be specified
        if not tag:
            ret["comment"] = (
                "The 'tag' argument is required if any one of 'build', "
                "'load', or 'sls' is used."
            )
            return ret
        if not isinstance(tag, six.string_types):
            tag = six.text_type(tag)
        full_image = ":".join((name, tag))
    else:
        if tag:
            name = "{0}:{1}".format(name, tag)
        full_image = name

    try:
        image_info = __salt__["docker.inspect_image"](full_image)
    except CommandExecutionError as exc:
        msg = exc.__str__()
        if "404" in msg:
            # Image not present
            image_info = None
        else:
            ret["comment"] = msg
            return ret

    if image_info is not None:
        # Specified image is present
        if not force:
            ret["result"] = True
            ret["comment"] = "Image {0} already present".format(full_image)
            return ret

    if build or sls:
        action = "built"
    elif load:
        action = "loaded"
    else:
        action = "pulled"

    if __opts__["test"]:
        ret["result"] = None
        if (image_info is not None and force) or image_info is None:
            ret["comment"] = "Image {0} will be {1}".format(full_image, action)
            return ret

    if build:
        # Get the functions default value and args
        argspec = salt.utils.args.get_function_argspec(__salt__["docker.build"])
        # Map any if existing args from kwargs into the build_args dictionary
        build_args = dict(list(zip(argspec.args, argspec.defaults)))
        for k in build_args:
            if k in kwargs.get("kwargs", {}):
                build_args[k] = kwargs.get("kwargs", {}).get(k)
        try:
            # map values passed from the state to the build args
            build_args["path"] = build
            build_args["repository"] = name
            build_args["tag"] = tag
            build_args["dockerfile"] = dockerfile
            image_update = __salt__["docker.build"](**build_args)
        except Exception as exc:  # pylint: disable=broad-except
            ret["comment"] = "Encountered error building {0} as {1}: {2}".format(
                build, full_image, exc
            )
            return ret
        if image_info is None or image_update["Id"] != image_info["Id"][:12]:
            ret["changes"] = image_update

    elif sls:
        _locals = locals()
        sls_build_kwargs = {
            k: _locals[k]
            for k in ("saltenv", "pillarenv", "pillar")
            if _locals[k] is not None
        }
        try:
            image_update = __salt__["docker.sls_build"](
                repository=name, tag=tag, base=base, mods=sls, **sls_build_kwargs
            )
        except Exception as exc:  # pylint: disable=broad-except
            ret[
                "comment"
            ] = "Encountered error using SLS {0} for building {1}: {2}".format(
                sls, full_image, exc
            )
            return ret
        if image_info is None or image_update["Id"] != image_info["Id"][:12]:
            ret["changes"] = image_update

    elif load:
        try:
            image_update = __salt__["docker.load"](path=load, repository=name, tag=tag)
        except Exception as exc:  # pylint: disable=broad-except
            ret["comment"] = "Encountered error loading {0} as {1}: {2}".format(
                load, full_image, exc
            )
            return ret
        if image_info is None or image_update.get("Layers", []):
            ret["changes"] = image_update

    else:
        try:
            image_update = __salt__["docker.pull"](
                name, insecure_registry=insecure_registry, client_timeout=client_timeout
            )
        except Exception as exc:  # pylint: disable=broad-except
            ret["comment"] = "Encountered error pulling {0}: {1}".format(
                full_image, exc
            )
            return ret
        if (
            image_info is not None
            and image_info["Id"][:12]
            == image_update.get("Layers", {}).get("Already_Pulled", [None])[0]
        ):
            # Image was pulled again (because of force) but was also
            # already there. No new image was available on the registry.
            pass
        elif image_info is None or image_update.get("Layers", {}).get("Pulled"):
            # Only add to the changes dict if layers were pulled
            ret["changes"] = image_update

    error = False

    try:
        __salt__["docker.inspect_image"](full_image)
    except CommandExecutionError as exc:
        msg = exc.__str__()
        if "404" not in msg:
            error = "Failed to inspect image '{0}' after it was {1}: {2}".format(
                full_image, action, msg
            )

    if error:
        ret["comment"] = error
    else:
        ret["result"] = True
        if not ret["changes"]:
            ret["comment"] = "Image '{0}' was {1}, but there were no changes".format(
                name, action
            )
        else:
            ret["comment"] = "Image '{0}' was {1}".format(full_image, action)
    return ret