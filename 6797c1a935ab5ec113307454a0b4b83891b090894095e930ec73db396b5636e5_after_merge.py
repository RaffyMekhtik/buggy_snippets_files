def provision_tox(provision_venv, args):
    ensure_meta_env_up_to_date(provision_venv)
    with provision_venv.new_action("provision") as action:
        provision_args = [str(provision_venv.envconfig.envpython), "-m", "tox"] + args
        try:
            action.popen(provision_args, redirect=False, report_fail=False)
            return 0
        except InvocationError as exception:
            return exception.exit_code