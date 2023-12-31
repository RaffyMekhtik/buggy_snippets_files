def ursula(click_config,
           action,
           dev,
           quiet,
           dry_run,
           force,
           lonely,
           network,
           teacher_uri,
           enode,
           min_stake,
           rest_host,
           rest_port,
           db_filepath,
           checksum_address,
           withdraw_address,
           federated_only,
           poa,
           config_root,
           config_file,
           provider_uri,
           geth,
           recompile_solidity,
           no_registry,
           registry_filepath,
           value,
           duration,
           index,
           list_,
           divide
           ) -> None:
    """
    Manage and run an "Ursula" PRE node.

    \b
    Actions
    -------------------------------------------------
    \b
    init              Create a new Ursula node configuration.
    view              View the Ursula node's configuration.
    run               Run an "Ursula" node.
    save-metadata     Manually write node metadata to disk without running
    forget            Forget all known nodes.
    destroy           Delete Ursula node configuration.
    stake             Manage stakes for this node.
    confirm-activity  Manually confirm-activity for the current period.
    collect-reward    Withdraw staking reward.

    """

    # Validate
    if federated_only and geth:
        raise click.BadOptionUsage(option_name="--geth", message="Federated only cannot be used with the --geth flag")

    if click_config.debug and quiet:
        raise click.BadOptionUsage(option_name="quiet", message="--debug and --quiet cannot be used at the same time.")

    #
    # Boring Setup Stuff
    #

    # Stage integrated ethereum node process TODO: Only devnet for now
    ETH_NODE = NO_BLOCKCHAIN_CONNECTION.bool_value(False)
    if geth:
        ETH_NODE = NuCypherGethDevnetProcess(config_root=config_root)
        provider_uri = ETH_NODE.provider_uri

    if not click_config.json_ipc and not click_config.quiet:
        click.secho(URSULA_BANNER.format(checksum_address or ''))

    #
    # Pre-Launch Warnings
    #

    if not click_config.quiet:
        if dev:
            click.secho("WARNING: Running in Development mode", fg='yellow')
        if force:
            click.secho("WARNING: Force is enabled", fg='yellow')

    #
    # Unauthenticated & Un-configured Ursula Configuration
    #

    if action == "init":
        """Create a brand-new persistent Ursula"""

        if dev:
            raise click.BadArgumentUsage("Cannot create a persistent development character")

        if not config_root:                         # Flag
            config_root = click_config.config_file  # Envvar

        # Attempts to automatically get the external IP from ifconfig.me
        # If the request fails, it falls back to the standard process.
        if not rest_host:
            rest_host = actions.determine_external_ip_address(force=force)

        new_password = click_config.get_password(confirm=True)

        ursula_config = UrsulaConfiguration.generate(password=new_password,
                                                     config_root=config_root,
                                                     rest_host=rest_host,
                                                     rest_port=rest_port,
                                                     db_filepath=db_filepath,
                                                     domains={network} if network else None,
                                                     federated_only=federated_only,
                                                     checksum_public_address=checksum_address,
                                                     download_registry=federated_only or no_registry,
                                                     registry_filepath=registry_filepath,
                                                     provider_process=ETH_NODE,
                                                     provider_uri=provider_uri,
                                                     poa=poa)

        painting.paint_new_installation_help(new_configuration=ursula_config,
                                             config_root=config_root,
                                             config_file=config_file,
                                             federated_only=federated_only)
        return

    #
    # Generate Configuration
    #

    # Development Configuration
    if dev:

        # TODO: Spawn POA development blockchain with geth --dev
        # dev_geth_process = NuCypherGethDevProcess()
        # dev_geth_process.deploy()
        # dev_geth_process.start()
        # ETH_NODE = dev_geth_process
        # provider_uri = ETH_NODE.provider_uri

        ursula_config = UrsulaConfiguration(dev_mode=True,
                                            domains={TEMPORARY_DOMAIN},
                                            poa=poa,
                                            registry_filepath=registry_filepath,
                                            provider_process=ETH_NODE,
                                            provider_uri=provider_uri,
                                            checksum_public_address=checksum_address,
                                            federated_only=federated_only,
                                            rest_host=rest_host,
                                            rest_port=rest_port,
                                            db_filepath=db_filepath)
    # Production Configurations
    else:

        # Domains -> bytes | or default
        domains = set(bytes(network, encoding='utf-8')) if network else None

        # Load Ursula from Configuration File
        try:
            ursula_config = UrsulaConfiguration.from_configuration_file(filepath=config_file,
                                                                        domains=domains,
                                                                        registry_filepath=registry_filepath,
                                                                        provider_process=ETH_NODE,
                                                                        provider_uri=provider_uri,
                                                                        rest_host=rest_host,
                                                                        rest_port=rest_port,
                                                                        db_filepath=db_filepath,
                                                                        poa=poa,
                                                                        federated_only=federated_only)
        except FileNotFoundError:
            return actions.handle_missing_configuration_file(character_config_class=UrsulaConfiguration,
                                                             config_file=config_file)
        except Exception as e:
            if click_config.debug:
                raise
            else:
                click.secho(str(e), fg='red', bold=True)
                raise click.Abort

    #
    # Configured Pre-Authentication Actions
    #

    # Handle destruction *before* network bootstrap and character initialization below
    if action == "destroy":
        """Delete all configuration files from the disk"""
        if dev:
            message = "'nucypher ursula destroy' cannot be used in --dev mode - There is nothing to destroy."
            raise click.BadOptionUsage(option_name='--dev', message=message)
        return actions.destroy_configuration(character_config=ursula_config, force=force)

    #
    # Connect to Blockchain
    #

    if not ursula_config.federated_only:
        click_config.connect_to_blockchain(character_configuration=ursula_config,
                                           recompile_contracts=recompile_solidity)

    click_config.ursula_config = ursula_config  # Pass Ursula's config onto staking sub-command

    #
    # Authenticate
    #

    if dev:
        # Development accounts are always unlocked and use one-time random keys.
        password = None
    else:
        password = click_config.get_password()
        click_config.unlock_keyring(character_configuration=ursula_config, password=password)

    #
    # Launch Warnings
    #

    if ursula_config.federated_only:
        click_config.emit(message="WARNING: Running in Federated mode", color='yellow')

    #
    # Seed
    #

    teacher_nodes = actions.load_seednodes(teacher_uris=[teacher_uri] if teacher_uri else None,
                                           min_stake=min_stake,
                                           federated_only=ursula_config.federated_only,
                                           network_domains=ursula_config.domains,
                                           network_middleware=click_config.middleware)

    # Add ETH Bootnode or Peer
    if enode:
        if geth:
            ursula_config.blockchain.interface.w3.geth.admin.addPeer(enode)
            click.secho(f"Added ethereum peer {enode}")
        else:
            raise NotImplemented  # TODO: other backends

    #
    # Produce
    #

    URSULA = ursula_config(password=password, known_nodes=teacher_nodes, lonely=lonely)
    del password  # ... under the rug

    #
    # Authenticated Action Switch
    #

    if action == 'run':
        """Seed, Produce, Run!"""

        # GO!
        try:

            click_config.emit(
                message="Starting Ursula on {}".format(URSULA.rest_interface),
                color='green',
                bold=True)

            # Ursula Deploy Warnings
            click_config.emit(
                message="Connecting to {}".format(','.join(str(d, encoding='utf-8') for d in ursula_config.domains)),
                color='green',
                bold=True)

            if not URSULA.federated_only and URSULA.stakes:
                click_config.emit(
                    message=f"Staking {str(URSULA.current_stake)} ~ Keep Ursula Online!",
                    color='blue',
                    bold=True)

            if not click_config.debug:
                stdio.StandardIO(UrsulaCommandProtocol(ursula=URSULA))

            if dry_run:
                return  # <-- ABORT - (Last Chance)

            # Run - Step 3
            node_deployer = URSULA.get_deployer()
            node_deployer.addServices()
            node_deployer.catalogServers(node_deployer.hendrix)
            node_deployer.run()   # <--- Blocking Call (Reactor)

        # Handle Crash
        except Exception as e:
            ursula_config.log.critical(str(e))
            click_config.emit(
                message="{} {}".format(e.__class__.__name__, str(e)),
                color='red',
                bold=True)
            raise  # Crash :-(

        # Graceful Exit / Crash
        finally:
            click_config.emit(message="Stopping Ursula", color='green')
            ursula_config.cleanup()
            click_config.emit(message="Ursula Stopped", color='red')
        return

    elif action == "save-metadata":
        """Manually save a node self-metadata file"""
        metadata_path = ursula.write_node_metadata(node=URSULA)
        return click_config.emit(message="Successfully saved node metadata to {}.".format(metadata_path), color='green')

    elif action == "view":
        """Paint an existing configuration to the console"""

        if not URSULA.federated_only:
            click.secho("BLOCKCHAIN ----------\n")
            painting.paint_contract_status(click_config=click_config, ursula_config=ursula_config)
            current_block = URSULA.blockchain.interface.w3.eth.blockNumber
            click.secho(f'Block # {current_block}')
            click.secho(f'NU Balance: {URSULA.token_balance}')
            click.secho(f'ETH Balance: {URSULA.eth_balance}')
            click.secho(f'Current Gas Price {URSULA.blockchain.interface.w3.eth.gasPrice}')

            # TODO: Verbose status
            # click.secho(f'{URSULA.blockchain.interface.w3.eth.getBlock(current_block)}')

        click.secho("CONFIGURATION --------")
        response = UrsulaConfiguration._read_configuration_file(filepath=config_file or ursula_config.config_file_location)
        return click_config.emit(response=response)

    elif action == "forget":
        actions.forget(configuration=ursula_config)
        return

    elif action == 'stake':

        # List Only
        if list_:
            if not URSULA.stakes:
                click.echo(f"There are no existing stakes for {URSULA.checksum_public_address}")
            painting.paint_stakes(stakes=URSULA.stakes)
            return

        # Divide Only
        if divide:
            """Divide an existing stake by specifying the new target value and end period"""

            # Validate
            if len(URSULA.stakes) == 0:
                click.secho("There are no active stakes for {}".format(URSULA.checksum_public_address))
                return

            # Selection
            if index is None:
                painting.paint_stakes(stakes=URSULA.stakes)
                index = click.prompt("Select a stake to divide", type=click.IntRange(min=0, max=len(URSULA.stakes)-1))

            # Lookup the stake
            current_stake = URSULA.stakes[index]

            # Value
            if not value:
                value = click.prompt(f"Enter target value (must be less than {str(current_stake.value)})", type=STAKE_VALUE)
            value = NU(value, 'NU')

            # Duration
            if not duration:
                extension = click.prompt("Enter number of periods to extend", type=STAKE_EXTENSION)
            else:
                extension = duration

            if not force:
                painting.paint_staged_stake_division(ursula=URSULA,
                                                     original_index=index,
                                                     original_stake=current_stake,
                                                     target_value=value,
                                                     extension=extension)

                click.confirm("Is this correct?", abort=True)

            modified_stake, new_stake = URSULA.divide_stake(stake_index=index,
                                                            target_value=value,
                                                            additional_periods=extension)

            if not quiet:
                click.secho('Successfully divided stake', fg='green')
                click.secho(f'Transaction Hash ........... {new_stake.receipt}')

            # Show the resulting stake list
            painting.paint_stakes(stakes=URSULA.stakes)

            return

        # Confirm new stake init
        if not force:
            click.confirm("Stage a new stake?", abort=True)

        # Validate balance
        balance = URSULA.token_balance
        if balance == 0:
            click.secho(f"{ursula.checksum_public_address} has 0 NU.")
            raise click.Abort
        if not quiet:
            click.echo(f"Current balance: {balance}")

        # Gather stake value
        if not value:
            min_locked = NU(URSULA.economics.minimum_allowed_locked, 'NuNit')
            value = click.prompt(f"Enter stake value", type=STAKE_VALUE, default=min_locked)
        else:
            value = NU(int(value), 'NU')

        # Duration
        if not quiet:
            message = f"Minimum duration: {URSULA.economics.minimum_allowed_locked} | " \
                      f"Maximum Duration: {URSULA.economics.maximum_allowed_locked}"
            click.echo(message)
        if not duration:
            duration = click.prompt("Enter stake duration in periods (1 Period = 24 Hours)", type=STAKE_DURATION)
        start_period = URSULA.miner_agent.get_current_period()
        end_period = start_period + duration

        # Review
        if not force:
            painting.paint_staged_stake(ursula=URSULA,
                                        stake_value=value,
                                        duration=duration,
                                        start_period=start_period,
                                        end_period=end_period)

            if not dev:
                actions.confirm_staged_stake(ursula=URSULA, value=value, duration=duration)

        # Last chance to bail
        if not force:
            click.confirm("Publish staged stake to the blockchain?", abort=True)

        stake = URSULA.initialize_stake(amount=int(value), lock_periods=duration)
        painting.paint_staking_confirmation(ursula=URSULA, transactions=stake.transactions)
        return

    elif action == 'confirm-activity':
        if not URSULA.stakes:
            click.secho("There are no active stakes for {}".format(URSULA.checksum_public_address))
            return
        URSULA.miner_agent.confirm_activity(node_address=URSULA.checksum_public_address)
        return

    elif action == 'collect-reward':
        """Withdraw staking reward to the specified wallet address"""
        if not force:
            click.confirm(f"Send {URSULA.calculate_reward()} to {URSULA.checksum_public_address}?")

        URSULA.collect_policy_reward(collector_address=withdraw_address or checksum_address)
        URSULA.collect_staking_reward()

    else:
        raise click.BadArgumentUsage("No such argument {}".format(action))