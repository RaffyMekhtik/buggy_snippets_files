    def parse(intent: List[Union[Clause, str]]) -> List[Clause]:
        """
        Given the string description from a list of input Clauses (intent),
        assign the appropriate clause.attribute, clause.filter_op, and clause.value.

        Parameters
        ----------
        intent : List[Clause]
                Underspecified list of lux.Clause objects.

        Returns
        -------
        List[Clause]
                Parsed list of lux.Clause objects.
        """
        if type(intent) != list:
            raise TypeError(
                "Input intent must be a list consisting of string descriptions or lux.Clause objects."
                "\nSee more at: https://lux-api.readthedocs.io/en/latest/source/guide/intent.html"
            )
        import re

        # intent = ldf.get_context()
        new_context = []
        # checks for and converts users' string inputs into lux specifications
        for clause in intent:
            valid_values = []
            if isinstance(clause, list):
                valid_values = []
                for v in clause:
                    # and v in list(ldf.columns): #TODO: Move validation check to Validator
                    if type(v) is str:
                        valid_values.append(v)
                temp_spec = Clause(attribute=valid_values)
                new_context.append(temp_spec)
            elif isinstance(clause, str):
                # case where user specifies a filter
                if "=" in clause:
                    eqInd = clause.index("=")
                    var = clause[0:eqInd]
                    if "|" in clause:
                        values = clause[eqInd + 1 :].split("|")
                        for v in values:
                            # if v in ldf.unique_values[var]: #TODO: Move validation check to Validator
                            valid_values.append(v)
                    else:
                        valid_values = clause[eqInd + 1 :]
                    # if var in list(ldf.columns): #TODO: Move validation check to Validator
                    temp_spec = Clause(attribute=var, filter_op="=", value=valid_values)
                    new_context.append(temp_spec)
                # case where user specifies a variable
                else:
                    if "|" in clause:
                        values = clause.split("|")
                        for v in values:
                            # if v in list(ldf.columns): #TODO: Move validation check to Validator
                            valid_values.append(v)
                    else:
                        valid_values = clause
                    temp_spec = Clause(attribute=valid_values)
                    new_context.append(temp_spec)
            elif type(clause) is Clause:
                new_context.append(clause)
        intent = new_context
        # ldf._intent = new_context

        for clause in intent:
            if clause.description:
                # TODO: Move validation check to Validator
                # if ((clause.description in list(ldf.columns)) or clause.description == "?"):# if clause.description in the list of attributes
                # clause.description contain ">","<". or "="
                if type(clause.description) == str and any(
                    ext in [">", "<", "=", "!="] for ext in clause.description
                ):
                    # then parse it and assign to clause.attribute, clause.filter_op, clause.values
                    clause.filter_op = re.findall(r"/.*/|>|=|<|>=|<=|!=", clause.description)[0]
                    split_description = clause.description.split(clause.filter_op)
                    clause.attribute = split_description[0]
                    clause.value = split_description[1]
                    if re.match(r"^-?\d+(?:\.\d+)?$", clause.value):
                        clause.value = float(clause.value)
                elif type(clause.description) == str:
                    clause.attribute = clause.description
                elif type(clause.description) == list:
                    clause.attribute = clause.description
                else:  # then it is probably a value
                    clause.value = clause.description
        return intent