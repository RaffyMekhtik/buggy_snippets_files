    def __init__(self, trigger, message=None):
        params = {x.name: x.value() for x in trigger.parameters().values()}
        trigger_name = trigger.__trigger_name__ if trigger else 'unset'
        gate_name = trigger.gate_cls.__gate_name__ if trigger and trigger.gate_cls else 'unset'
        msg = 'Trigger evaluation failed for gate {} and trigger {}, with parameters: ({}) due to: {}'.format(
            gate_name, trigger_name, params, message)

        super().__init__(msg)
        self.trigger = trigger
        self.gate = trigger.gate_cls