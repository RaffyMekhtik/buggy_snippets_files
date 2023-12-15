    def run(self, workspace):
        m = workspace.measurements
        values = []
        input_values = []
        has_image_measurement = any([operand.object == cpmeas.IMAGE
                                     for operand in self.get_operands()])
        all_image_measurements = all([operand.object == cpmeas.IMAGE
                                     for operand in self.get_operands()])
        all_object_names = list(set([operand.operand_objects.value
                                     for operand in self.get_operands()
                                     if operand.object != cpmeas.IMAGE]))
        all_operands = self.get_operands()
        
        for operand in all_operands:
            value = m.get_current_measurement(operand.object,operand.operand_measurement.value)
            # Copy the measurement (if it's right type) or else it gets altered by the operation
            if not np.isscalar(value):
                value = value.copy()
            # ensure that the data can be changed in-place by floating point ops
            value = value.astype(np.float)

            if isinstance(value, str) or isinstance(value, unicode):
                try:
                    value = float(value)
                except ValueError:
                    raise ValueError("Unable to use non-numeric value in measurement, %s"%operand.measurement.value)

            input_values.append(value)
            value *= operand.multiplicand.value
            value **= operand.exponent.value
            values.append(value)
        
        if ((not has_image_measurement) and 
            (self.operation.value not in (O_NONE)) and 
            len(values[0]) != len(values[1])):
            #
            # Try harder, broadcast using the results from relate objects
            #
            operand_object1 = self.operands[0].operand_objects.value
            operand_object2 = self.operands[1].operand_objects.value
            g = m.get_relationship_groups()
            
            for gg in g:
                if gg.relationship == R_PARENT:
                    #
                    # first is parent of second
                    #
                    if (gg.object_name1 == operand_object1 and
                        gg.object_name2 == operand_object2):
                        f0 = cpmeas.R_FIRST_OBJECT_NUMBER
                        f1 = cpmeas.R_SECOND_OBJECT_NUMBER
                    elif (gg.object_name1 == operand_object2 and
                          gg.object_name2 == operand_object1):
                        f1 = cpmeas.R_FIRST_OBJECT_NUMBER
                        f0 = cpmeas.R_SECOND_OBJECT_NUMBER
                    else:
                        continue
                    r = m.get_relationships(
                        gg.module_number, gg.relationship,
                        gg.object_name1, gg.object_name2,
                        image_numbers = [m.image_set_number])
                    r = r[(r[cpmeas.R_FIRST_IMAGE_NUMBER]==m.image_set_number) &
                          (r[cpmeas.R_SECOND_IMAGE_NUMBER]==m.image_set_number)]
                    i0 = r[f0] - 1
                    i1 = r[f1] - 1
                    #
                    # Use np.bincount to broadcast or sum. Then divide the counts
                    # by the sum to get count=0 -> Nan, count=1 -> value
                    # count > 1 -> mean
                    #
                    def bincount(indexes, weights=None, minlength=None):
                        '''Minlength was added to numpy at some point....'''
                        result = np.bincount(indexes, weights)
                        if minlength is not None and len(result) < minlength:
                            result = np.hstack(
                                [result, 
                                 (0 if weights is None else np.nan) * 
                                 np.zeros(minlength - len(result))])
                        return result
                    c0 = bincount(i0, minlength=len(values[0]))
                    c1 = bincount(i1, minlength=len(values[1]))
                    v1 = bincount(i0, values[1][i1], minlength=len(values[0])) / c0
                    v0 = bincount(i1, values[0][i0], minlength=len(values[1])) / c1
                    break
            else:
                logger.warning(
                    "Incompatable objects: %s has %d objects and %s has %d objects"%
                    (operand_object1, len(values[0]),
                     operand_object2, len(values[1])))
                #
                # Match up as best as we can, padding with Nans
                #
                if len(values[0]) < len(values[1]):
                    v0 = np.ones(len(values[1])) * np.nan
                    v0[:len(values[0])] = values[0]
                    v1 = values[1][:len(values[0])]
                else:
                    v1 = np.ones(len(values[0])) * np.nan
                    v1[:len(values[1])] = values[1]
                    v0 = values[0][:len(values[1])]
            result = [
                self.compute_operation(values[0], v1),
                self.compute_operation(v0, values[1])]
        else:
            result = self.compute_operation(values[0], 
                                            values[1] if len(values) > 1
                                            else None)
            if not all_image_measurements:
                result = [result] * len(all_object_names)
       
        feature = self.measurement_name()
        if all_image_measurements:
            m.add_image_measurement(feature, result)
        else:
            for object_name, r in zip(all_object_names, result):
                m.add_measurement(object_name, feature, r)
            result = result[0]
                
        if self.show_window:
            workspace.display_data.col_labels = (
                "Measurement name", "Measurement type", "Result")
            workspace.display_data.statistics = [
                (self.output_feature_name.value, 
                 "Image" if all_image_measurements else "Object", 
                 "%.2f"%np.mean(result))]