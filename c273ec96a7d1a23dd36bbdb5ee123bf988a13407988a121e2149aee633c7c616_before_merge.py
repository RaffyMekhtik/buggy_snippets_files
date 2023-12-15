def message(bot, update):
    """
    Example for an asynchronous handler. It's not guaranteed that replies will
    be in order when using @run_async.
    """

    sleep(2)  # IO-heavy operation here
    bot.sendMessage(update.message.chat_id, text='Echo: %s' %
                                                 update.message.text)