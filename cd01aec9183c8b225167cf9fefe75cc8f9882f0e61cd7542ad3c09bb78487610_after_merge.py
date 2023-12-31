def init_events(bot, cli_flags):
    @bot.event
    async def on_connect():
        if bot.uptime is None:
            print("Connected to Discord. Getting ready...")

    @bot.event
    async def on_ready():
        if bot.uptime is not None:
            return

        bot.uptime = datetime.datetime.utcnow()
        packages = []

        if cli_flags.no_cogs is False:
            packages.extend(await bot.db.packages())

        if cli_flags.load_cogs:
            packages.extend(cli_flags.load_cogs)

        if packages:
            to_remove = []
            print("Loading packages...")
            for package in packages:
                try:
                    spec = await bot.cog_mgr.find_cog(package)
                    await bot.load_extension(spec)
                except Exception as e:
                    log.exception("Failed to load package {}".format(package), exc_info=e)
                    await bot.remove_loaded_package(package)
                    to_remove.append(package)
            for package in to_remove:
                packages.remove(package)
            if packages:
                print("Loaded packages: " + ", ".join(packages))

        if bot.rpc_enabled:
            await bot.rpc.initialize()

        guilds = len(bot.guilds)
        users = len(set([m for m in bot.get_all_members()]))

        try:
            data = await bot.application_info()
            invite_url = discord.utils.oauth_url(data.id)
        except:
            invite_url = "Could not fetch invite url"

        prefixes = cli_flags.prefix or (await bot.db.prefix())
        lang = await bot.db.locale()
        red_version = __version__
        red_pkg = pkg_resources.get_distribution("Red-DiscordBot")
        dpy_version = discord.__version__

        INFO = [
            str(bot.user),
            "Prefixes: {}".format(", ".join(prefixes)),
            "Language: {}".format(lang),
            "Red Bot Version: {}".format(red_version),
            "Discord.py Version: {}".format(dpy_version),
            "Shards: {}".format(bot.shard_count),
        ]

        if guilds:
            INFO.extend(("Servers: {}".format(guilds), "Users: {}".format(users)))
        else:
            print("Ready. I'm not in any server yet!")

        INFO.append("{} cogs with {} commands".format(len(bot.cogs), len(bot.commands)))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://pypi.python.org/pypi/red-discordbot/json") as r:
                    data = await r.json()
            if StrictVersion(data["info"]["version"]) > StrictVersion(red_version):
                INFO.append(
                    "Outdated version! {} is available "
                    "but you're using {}".format(data["info"]["version"], red_version)
                )
                owner = discord.utils.get(bot.get_all_members(), id=bot.owner_id)
                await owner.send(
                    "Your Red instance is out of date! {} is the current "
                    "version, however you are using {}!".format(
                        data["info"]["version"], red_version
                    )
                )
        except:
            pass
        INFO2 = []

        sentry = await bot.db.enable_sentry()
        mongo_enabled = storage_type() != "JSON"
        reqs_installed = {"voice": None, "docs": None, "test": None}
        for key in reqs_installed.keys():
            reqs = [x.name for x in red_pkg._dep_map[key]]
            try:
                pkg_resources.require(reqs)
            except DistributionNotFound:
                reqs_installed[key] = False
            else:
                reqs_installed[key] = True

        options = (
            ("Error Reporting", sentry),
            ("MongoDB", mongo_enabled),
            ("Voice", reqs_installed["voice"]),
            ("Docs", reqs_installed["docs"]),
            ("Tests", reqs_installed["test"]),
        )

        on_symbol, off_symbol, ascii_border = _get_startup_screen_specs()

        for option, enabled in options:
            enabled = on_symbol if enabled else off_symbol
            INFO2.append("{} {}".format(enabled, option))

        print(Fore.RED + INTRO)
        print(Style.RESET_ALL)
        print(bordered(INFO, INFO2, ascii_border=ascii_border))

        if invite_url:
            print("\nInvite URL: {}\n".format(invite_url))

        bot.color = discord.Colour(await bot.db.color())
        try:
            import Levenshtein
        except ImportError:
            log.info(
                "python-Levenshtein is not installed, fuzzy string matching will be a bit slower."
            )

    @bot.event
    async def on_error(event_method, *args, **kwargs):
        sentry_log.exception("Exception in {}".format(event_method))

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help()
        elif isinstance(error, commands.ConversionFailure):
            if error.args:
                await ctx.send(error.args[0])
            else:
                await ctx.send_help()
        elif isinstance(error, commands.BadArgument):
            await ctx.send_help()
        elif isinstance(error, commands.DisabledCommand):
            disabled_message = await bot.db.disabled_command_msg()
            if disabled_message:
                await ctx.send(disabled_message.replace("{command}", ctx.invoked_with))
        elif isinstance(error, commands.CommandInvokeError):
            log.exception(
                "Exception in command '{}'" "".format(ctx.command.qualified_name),
                exc_info=error.original,
            )
            if should_log_sentry(error):
                sentry_log.exception(
                    "Exception in command '{}'" "".format(ctx.command.qualified_name),
                    exc_info=error.original,
                )

            message = (
                "Error in command '{}'. Check your console or "
                "logs for details."
                "".format(ctx.command.qualified_name)
            )
            exception_log = "Exception in command '{}'\n" "".format(ctx.command.qualified_name)
            exception_log += "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            bot._last_exception = exception_log
            if not hasattr(ctx.cog, "_{0.command.cog_name}__error".format(ctx)):
                await ctx.send(inline(message))
        elif isinstance(error, commands.CommandNotFound):
            fuzzy_commands = await fuzzy_command_search(ctx)
            if not fuzzy_commands:
                pass
            elif await ctx.embed_requested():
                await ctx.send(embed=await format_fuzzy_results(ctx, fuzzy_commands, embed=True))
            else:
                await ctx.send(await format_fuzzy_results(ctx, fuzzy_commands, embed=False))
        elif isinstance(error, commands.CheckFailure):
            pass
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("That command is not available in DMs.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                "This command is on cooldown. Try again in {:.2f}s".format(error.retry_after)
            )
        else:
            log.exception(type(error).__name__, exc_info=error)
            try:
                sentry_error = error.original
            except AttributeError:
                sentry_error = error

            if should_log_sentry(sentry_error):
                sentry_log.exception("Unhandled command error.", exc_info=sentry_error)

    @bot.event
    async def on_message(message):
        bot.counter["messages_read"] += 1
        await bot.process_commands(message)
        discord_now = message.created_at
        if (
            not bot.checked_time_accuracy
            or (discord_now - timedelta(minutes=60)) > bot.checked_time_accuracy
        ):
            system_now = datetime.datetime.utcnow()
            diff = abs((discord_now - system_now).total_seconds())
            if diff > 60:
                log.warn(
                    "Detected significant difference (%d seconds) in system clock to discord's clock."
                    " Any time sensitive code may fail.",
                    diff,
                )
            bot.checked_time_accuracy = discord_now

    @bot.event
    async def on_resumed():
        bot.counter["sessions_resumed"] += 1

    @bot.event
    async def on_command(command):
        bot.counter["processed_commands"] += 1

    @bot.event
    async def on_command_add(command: commands.Command):
        disabled_commands = await bot.db.disabled_commands()
        if command.qualified_name in disabled_commands:
            command.enabled = False
        for guild in bot.guilds:
            disabled_commands = await bot.db.guild(guild).disabled_commands()
            if command.qualified_name in disabled_commands:
                command.disable_in(guild)

    async def _guild_added(guild: discord.Guild):
        disabled_commands = await bot.db.guild(guild).disabled_commands()
        for command_name in disabled_commands:
            command_obj = bot.get_command(command_name)
            if command_obj is not None:
                command_obj.disable_in(guild)

    @bot.event
    async def on_guild_join(guild: discord.Guild):
        await _guild_added(guild)

    @bot.event
    async def on_guild_available(guild: discord.Guild):
        # We need to check guild-disabled commands here since some cogs
        # are loaded prior to `on_ready`.
        await _guild_added(guild)

    @bot.event
    async def on_guild_leave(guild: discord.Guild):
        # Clean up any unneeded checks
        disabled_commands = await bot.db.guild(guild).disabled_commands()
        for command_name in disabled_commands:
            command_obj = bot.get_command(command_name)
            if command_obj is not None:
                command_obj.enable_in(guild)