def create_project(parser, options, args):
    # Validate args
    if len(args) < 2:
        parser.error("Please specify a name for your wagtail installation")
    elif len(args) > 2:
        parser.error("Too many arguments")

    project_name = args[1]

    # Make sure given name is not already in use by another python package/module.
    try:
        __import__(project_name)
    except ImportError:
        pass
    else:
        parser.error("'%s' conflicts with the name of an existing "
                     "Python module and cannot be used as a project "
                     "name. Please try another name." % project_name)

    # Make sure directory does not already exist
    if os.path.exists(project_name):
        print('A directory called %(project_name)s already exists. \
            Please choose another name for your wagtail project or remove the existing directory.' % {'project_name': project_name})
        sys.exit(errno.EEXIST)

    print("Creating a wagtail project called %(project_name)s" % {'project_name': project_name})

    # Create the project from the wagtail template using startapp

    # First find the path to wagtail
    import wagtail
    wagtail_path = os.path.dirname(wagtail.__file__)
    template_path = os.path.join(wagtail_path, 'project_template')

    # Call django-admin startproject
    utility = ManagementUtility([
        'django-admin.py', 'startproject',
        '--template=' + template_path,
        '--name=Vagrantfile', '--ext=html,rst',
        project_name
    ])
    utility.execute()

    print("Success! %(project_name)s is created" % {'project_name': project_name})