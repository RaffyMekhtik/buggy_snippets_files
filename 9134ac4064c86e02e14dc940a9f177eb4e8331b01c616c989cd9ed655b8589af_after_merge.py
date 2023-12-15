def command_result(identifier, send_error=protobuf.SendError.NoError):
    """Playback command request."""
    message = create(protobuf.SEND_COMMAND_RESULT_MESSAGE, identifier=identifier)
    inner = message.inner()
    inner.sendError = send_error
    inner.handlerReturnStatus = protobuf.HandlerReturnStatus.Success
    return message