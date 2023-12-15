def get_transfer_from_task(
    secrethash: SecretHash, transfer_task: TransferTask
) -> Optional[LockedTransferType]:
    transfer: LockedTransferType
    if isinstance(transfer_task, InitiatorTask):
        if secrethash in transfer_task.manager_state.initiator_transfers:
            transfer = transfer_task.manager_state.initiator_transfers[secrethash].transfer
        else:
            return None
    elif isinstance(transfer_task, MediatorTask):
        pairs = transfer_task.mediator_state.transfers_pair
        if pairs:
            transfer = pairs[-1].payer_transfer
        elif transfer_task.mediator_state.waiting_transfer:
            transfer = transfer_task.mediator_state.waiting_transfer.transfer
    elif isinstance(transfer_task, TargetTask):
        transfer = transfer_task.target_state.transfer
    else:  # pragma: no unittest
        raise ValueError("get_transfer_from_task for a non TransferTask argument")

    return transfer