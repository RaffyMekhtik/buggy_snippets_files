async def parse_apiai(opsdroid, message, config):
    """Parse a message against all apiai skills."""
    # pylint: disable=broad-except
    # We want to catch all exceptions coming from a skill module and not
    # halt the application. If a skill throws an exception it just doesn't
    # give a response to the user, so an error response should be given.
    if 'access-token' in config:

        result = await call_apiai(message, config)

        if result["status"]["code"] >= 300:
            _LOGGER.error("api.ai error - " +
                          str(result["status"]["code"]) + " " +
                          result["status"]["errorType"])
            return

        if "min-score" in config and \
                result["result"]["score"] < config["min-score"]:
            _LOGGER.debug("api.ai score lower than min-score")
            return

        if result:
            for skill in opsdroid.skills:

                if "apiai_action" in skill or "apiai_intent" in skill:
                    if ("action" in result["result"] and
                            skill["apiai_action"] in
                            result["result"]["action"]) \
                            or ("intentName" in result["result"] and
                                skill["apiai_intent"] in
                                result["result"]["intentName"]):
                        message.apiai = result
                        try:
                            await skill["skill"](opsdroid, skill["config"],
                                                 message)
                        except Exception:
                            await message.respond(
                                "Whoops there has been an error")
                            await message.respond(
                                "Check the log for details")
                            _LOGGER.exception("Exception when parsing '" +
                                              message.text +
                                              "' against skill '" +
                                              result["result"]["action"] + "'")