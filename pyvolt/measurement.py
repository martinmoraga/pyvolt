from enum import Enum
import json
import numpy as np


class ElemType(Enum):
    Node = 1  # Node Voltage
    Branch = 2  # Complex Power flow at branch


class MeasType(Enum):
    V_mag = 1  # Node Voltage
    Sinj_real = 2  # Complex Power Injection at node
    Sinj_imag = 3  # Complex Power Injection at node
    S1_real = 4  # Active Power flow at branch, measured at initial node (S1.real)
    S1_imag = 5  # Reactive Power flow at branch, measured at initial node (S1.imag)
    I_mag = 6  # Branch Current
    Vpmu_mag = 7  # Node Voltage
    Vpmu_phase = 8  # Node Voltage
    Ipmu_mag = 9  # Branch Current
    Ipmu_phase = 10  # Branch Current
    S2_real = 11  # Active Power flow at branch, measured at final node (S2.real)
    S2_imag = 12  # Reactive Power flow at branch, measured at final node (S2.imag)
    Ipmu_inj_mag = 13 # Node current injection magnitude
    Ipmu_inj_phase = 14 # Node current injection phase


class Measurement:
    def __init__(self, element, element_type, meas_type, meas_value_ideal, unc):
        """
        Creates a measurement, which is used by the estimation module. Possible types of measurements are: v, p, q, i, Vpmu and Ipmu
        @element: pointer to the topology_node / topology_branch (object of class network.Node / network.Branch)
        @element_type: clarifies which type of element is considered (object of enum ElemType, e.g. ElemType.Node)
        @meas_type: clarifies which quantity is measured (object of enum MeasType, e.g. MeasType.V_mag)
        @meas_value_ideal: ideal measurement value (usually result of a powerflow calculation)
        @unc: measurement uncertainty in percent
        """

        if not isinstance(element_type, ElemType):
            raise Exception("elem_type must be an object of class ElemType")

        if not isinstance(meas_type, MeasType):
            raise Exception("meas_type must be an object of class MeasType")

        self.element = element
        self.element_type = element_type
        self.meas_type = meas_type
        self.meas_value_ideal = meas_value_ideal
        self.unc = unc                                          # uncertainty in percentage
        self.std_dev = 0.0                                      # standard deviation of measurement in per unit (or true-value)
        self.std_dev_act = 0.0                                  # standard deviation of measurement in actuals (or true-value)
        self.meas_value = 0.0                                   # measured values (affected by uncertainty)
        self.meas_value_act = 0.0                               # measurement values in actuals (affected by uncertainty)


class MeasurementSet:
    def __init__(self):
        self.measurements = []  # array with all measurements

    def create_measurement(self, element, element_type, meas_type, meas_value_ideal, unc):
        """
        to add elements to the measurements array
        """
        self.measurements.append(Measurement(element, element_type, meas_type, meas_value_ideal, unc))

    def update_measurement(self, element_uuid, meas_type, meas_data, value_in_pu=True):
        """
        to update meas_value of a specific measurement object in the measurements array
        """

        # only update measurements that are already included in the measurements set
        for meas in self.measurements:
            if meas.element.uuid == element_uuid:
                # special case for voltage magnitude: SOGNO interface only knows Vpmu_mag while measurement set distincts between Vpmu_mag and V_mag
                if meas_type == MeasType.Vpmu_mag and (meas.meas_type == MeasType.Vpmu_mag or meas.meas_type == MeasType.V_mag):
                    # volt pu conversion assuming that meas_data from device are in volts and single-phase value according to sogno interface
                    # while baseVoltage from CIM in [kV] and three-phase value
                    if not value_in_pu:
                        meas_value_pu = meas_data / (meas.element.baseVoltage / np.sqrt(3) )
                        meas_value_act = meas_data
                    else:
                        meas_value_pu = meas_data
                        meas_value_act = meas_data * (meas.element.baseVoltage / np.sqrt(3) )
                    print("Updating measurement value for {} of type {} from {} to {}".format(meas.element.uuid, str(meas.meas_type), meas.meas_value, meas_value_pu))                    
                    meas.meas_value = meas_value_pu 
                    meas.meas_value_act = meas_value_act                
                # special case for voltage magnitude: SOGNO interface only knows Ipmu_mag while measurement set distincts between Ipmu_mag and I_mag
                elif meas_type == MeasType.Ipmu_mag and (meas.meas_type == MeasType.Ipmu_mag or meas.meas_type == MeasType.I_mag or meas.meas_type == MeasType.Ipmu_inj_mag):
                    # current pu conversion assuming that meas_data from device are in A and single-phase value according to sogno interface
                    # while base_current in [kA]
                    if not value_in_pu:
                        meas_value_pu = meas_data / (meas.element.base_current )
                        meas_value_act = meas_data
                    else:
                        meas_value_pu = meas_data
                        meas_value_act = meas_data * (meas.element.base_current )
                    print("Updating measurement value for {} of type {} from {} to {}".format(meas.element.uuid, str(meas.meas_type), meas.meas_value, meas_value_pu))
                    meas.meas_value = meas_value_pu
                    meas.meas_value_act = meas_value_act
                # case for other measurements 
                elif (meas_type == meas.meas_type and (meas_type == MeasType.S1_real or meas_type == MeasType.S1_imag or meas_type == MeasType.Sinj_imag or meas_type == MeasType.Sinj_imag)): 
                    # power pu conversion assuming that meas_data from device are in watts and single-phase value according to sogno interface
                    # while baseApparent power in [MW] and three-phase value
                    if not value_in_pu:    
                        meas_value_pu = meas_data / (meas.element.base_apparent_power / 3 )
                        meas_value_act = meas_data
                    else:
                        meas_value_pu = meas_data
                        meas_value_act = meas_data * (meas.element.base_apparent_power / 3 )
                    print("Updating measurement value for {} of type {} from {} to {}".format(meas.element.uuid, str(meas.meas_type), meas.meas_value, meas_value_pu))
                    meas.meas_value = meas_value_pu
                    meas.meas_value_act = meas_value_act
                elif (meas_type == meas.meas_type and (meas_type == MeasType.Vpmu_phase or meas_type == MeasType.Ipmu_phase or meas_type == MeasType.Ipmu_inj_phase)):
                    print("Updating measurement value for {} of type {} from {} to {}".format(meas.element.uuid, str(meas.meas_type), meas.meas_value, meas_data))
                    meas.meas_value = meas_data
                    meas.meas_value_act = meas_data


    def read_measurements_from_file(self, powerflow_results, file_name):
        """
        read measurements from file.

        @param powerflow_results: object of class pyvolt.results.Results
        @param file_name
        """
        with open(file_name) as json_file:
            data = json.load(json_file)
        for key, value in data['Measurement'].items():
            if key == "Vmag":
                unc = float(value['unc'])
                for uuid in value['uuid']:
                    pf_node = powerflow_results.get_node(uuid=uuid)
                    element = pf_node.topology_node
                    meas_value_ideal = np.abs(pf_node.voltage_pu)
                    self.create_measurement(element, ElemType.Node, MeasType.V_mag, meas_value_ideal, unc)
            elif key == "Imag":
                unc = float(value['unc'])
                for uuid in value['uuid']:
                    pf_branch = powerflow_results.get_branch(uuid=uuid)
                    element = pf_branch.topology_branch
                    meas_value_ideal = np.abs(pf_branch.current_pu)
                    self.create_measurement(element, ElemType.Branch, MeasType.I_mag, meas_value_ideal, unc)
            elif key == "Pinj":
                unc = float(value['unc'])
                for uuid in value['uuid']:
                    pf_node = powerflow_results.get_node(uuid=uuid)
                    element = pf_node.topology_node
                    meas_value_ideal = pf_node.power_pu.real
                    self.create_measurement(element, ElemType.Node, MeasType.Sinj_real, meas_value_ideal, unc)
            elif key == "Qinj":
                unc = float(value['unc'])
                for uuid in value['uuid']:
                    pf_node = powerflow_results.get_node(uuid=uuid)
                    element = pf_node.topology_node
                    meas_value_ideal = pf_node.power_pu.imag
                    self.create_measurement(element, ElemType.Node, MeasType.Sinj_imag, meas_value_ideal, unc)
            elif key == "P1":
                unc = float(value['unc'])
                for uuid in value['uuid']:
                    pf_branch = powerflow_results.get_branch(uuid=uuid)
                    element = pf_branch.topology_branch
                    meas_value_ideal = pf_branch.power_pu.real
                    self.create_measurement(element, ElemType.Branch, MeasType.S1_real, meas_value_ideal, unc)
            elif key == "Q1":
                unc = float(value['unc'])
                for uuid in value['uuid']:
                    pf_branch = powerflow_results.get_branch(uuid=uuid)
                    element = pf_branch.topology_branch
                    meas_value_ideal = pf_branch.power_pu.imag
                    self.create_measurement(element, ElemType.Branch, MeasType.S1_imag, meas_value_ideal, unc)
            elif key == "P2":
                unc = float(value['unc'])
                for uuid in value['uuid']:
                    pf_branch = powerflow_results.get_branch(uuid=uuid)
                    element = pf_branch.topology_branch
                    meas_value_ideal = pf_branch.power2_pu.real
                    self.create_measurement(element, ElemType.Branch, MeasType.S2_real, meas_value_ideal, unc)
            elif key == "Q2":
                unc = float(value['unc'])
                for uuid in value['uuid']:
                    pf_branch = powerflow_results.get_branch(uuid=uuid)
                    element = pf_branch.topology_branch
                    meas_value_ideal = pf_branch.power2_pu.imag
                    self.create_measurement(element, ElemType.Branch, MeasType.S2_imag, meas_value_ideal, unc)
            elif key == "Vpmu":
                unc_mag = float(value['unc_mag'])
                unc_phase = float(value['unc_phase'])
                for uuid in value['uuid']:
                    pf_node = powerflow_results.get_node(uuid=uuid)
                    element = pf_node.topology_node
                    meas_value_ideal_mag = np.abs(pf_node.voltage_pu)
                    self.create_measurement(element, ElemType.Node, MeasType.Vpmu_mag, meas_value_ideal_mag, unc_mag)
                for uuid in value['uuid']:
                    pf_node = powerflow_results.get_node(uuid=uuid)
                    element = pf_node.topology_node
                    meas_value_ideal_phase = np.angle(pf_node.voltage_pu)
                    self.create_measurement(element, ElemType.Node, MeasType.Vpmu_phase, meas_value_ideal_phase, unc_phase)
            elif key == "Ipmu":
                unc_mag = float(value['unc_mag'])
                unc_phase = float(value['unc_phase'])
                for uuid in value['uuid']:
                    pf_branch = powerflow_results.get_branch(uuid=uuid)
                    element = pf_branch.topology_branch
                    meas_value_ideal_mag = np.abs(pf_branch.current_pu)
                    meas_value_ideal_phase = np.angle(pf_branch.current_pu)
                    self.create_measurement(element, ElemType.Branch, MeasType.Ipmu_mag, meas_value_ideal_mag, unc_mag)
                    self.create_measurement(element, ElemType.Branch, MeasType.Ipmu_phase, meas_value_ideal_phase, unc_phase)
            elif key == "Ipmu_inj":
                unc_mag = float(value['unc_mag'])
                unc_phase = float(value['unc_phase'])
                for uuid in value['uuid']:
                    pf_node = powerflow_results.get_node(uuid=uuid)
                    element = pf_node.topology_node
                    meas_value_ideal_mag = np.abs(pf_node.current_pu)
                    meas_value_ideal_phase = np.angle(pf_node.current_pu)
                    self.create_measurement(element, ElemType.Node, MeasType.Ipmu_inj_mag, meas_value_ideal_mag, unc_mag)
                    self.create_measurement(element, ElemType.Node, MeasType.Ipmu_inj_phase, meas_value_ideal_phase, unc_phase)

    def meas_creation(self, dist="normal", seed=None, type="simulation"):
        """
        It calculates the measured values (affected by uncertainty) at the measurement points
        which distribution should be used? if gaussian --> stddev must be divided by 3

        @param seed: Seed for RandomState (to make the random numbers predictable)
                     Must be convertible to 32 bit unsigned integers.
        @param seed: - normal: use normal distribution (-->std_dev are divided by 3)
                     - uniform: use normal distribution
        """
        if type == "simulation":
            np.random.seed(seed)
            if dist == "normal":
                err_pu = np.random.normal(0, 0, len(self.measurements))
                for index, measurement in enumerate(self.measurements):
                    if measurement.meas_type not in [MeasType.Ipmu_phase, MeasType.Vpmu_phase, MeasType.Ipmu_inj_phase]:
                        zdev_ideal = abs(measurement.meas_value_ideal * measurement.unc)/300
                        measurement.meas_value = measurement.meas_value_ideal + zdev_ideal * err_pu[index]
                        measurement.std_dev = abs(measurement.meas_value * measurement.unc)/300
                    elif measurement.meas_type in [MeasType.Ipmu_phase, MeasType.Vpmu_phase, MeasType.Ipmu_inj_phase]:
                        zdev_ideal = measurement.unc/3
                        measurement.meas_value = measurement.meas_value_ideal + zdev_ideal * err_pu[index]
                        measurement.std_dev = zdev_ideal # phase angle uncertainty is not relative
                    
            elif dist == "uniform":
                err_pu = np.random.uniform(-1, 1, len(self.measurements))
                for index, measurement in enumerate(self.measurements):
                    if measurement.meas_type not in [MeasType.Ipmu_phase, MeasType.Vpmu_phase, MeasType.Ipmu_inj_phase]:
                        zdev_ideal = abs(measurement.meas_value_ideal * measurement.unc)/300
                        measurement.meas_value = measurement.meas_value_ideal + np.multiply(3 * zdev_ideal, err_pu[index])
                        measurement.std_dev = abs(measurement.meas_value * measurement.unc)/300
                    elif measurement.meas_type in [MeasType.Ipmu_phase, MeasType.Vpmu_phase, MeasType.Ipmu_inj_phase]:
                        zdev_ideal = measurement.unc/3
                        measurement.meas_value = measurement.meas_value_ideal + np.multiply(3 * zdev_ideal, err_pu[index])
                        measurement.std_dev = zdev_ideal
                   
        elif type == "field":
            for measurement in self.measurements:
                measurement.meas_value = measurement.meas_value_ideal
                if measurement.meas_type not in [MeasType.Ipmu_phase, MeasType.Vpmu_phase, MeasType.Ipmu_inj_phase]:
                    measurement.std_dev = abs(measurement.meas_value * measurement.unc)/300
                elif measurement.meas_type in [MeasType.Ipmu_phase, MeasType.Vpmu_phase, MeasType.Ipmu_inj_phase]:
                    measurement.std_dev = measurement.unc/3

        # converting to actuals
        type_volt = [MeasType.Vpmu_mag, MeasType.V_mag]
        type_curr = [MeasType.Ipmu_mag, MeasType.I_mag, MeasType.Ipmu_inj_mag]
        type_power = [MeasType.S1_imag, MeasType.S1_real, MeasType.S2_imag, MeasType.S2_real, MeasType.Sinj_imag, MeasType.Sinj_real]
        type_phase = [MeasType.Vpmu_phase, MeasType.Ipmu_phase, MeasType.Ipmu_inj_phase]
        for index, meas in enumerate(self.measurements):
                if meas.meas_type in type_volt :
                    meas.meas_value_act = meas.meas_value * (meas.element.baseVoltage / np.sqrt(3))
                    meas.std_dev_act = meas.std_dev * (meas.element.baseVoltage / np.sqrt(3))
                elif meas.meas_type in type_curr:
                    meas.meas_value_act = meas.meas_value * (meas.element.base_current )
                    meas.std_dev_act = meas.std_dev * (meas.element.base_current )
                elif meas.meas_type in type_power :
                    meas.meas_value_act = meas.meas_value * (meas.element.base_apparent_power / 3 ) # TODO: Should be divided by 3 for single phase?
                    meas.std_dev_act = meas.std_dev * (meas.element.base_apparent_power / 3 )
                elif meas.meas_type in type_phase : 
                    meas.meas_value_act = meas.meas_value # unaffected by per-unit
                    meas.std_dev_act = meas.std_dev

    def meas_creation_test(self, err_pu):
        """
        For test purposes.
        It calculates the measured values (affected by uncertainty) at the measurement points.
        This function takes as paramenter a random distribution.
        """
        for index, measurement in enumerate(self.measurements):
            if measurement.meas_type not in [MeasType.Ipmu_phase, MeasType.Vpmu_phase]:
                measurement.std_dev = np.absolute(measurement.meas_value_ideal) * measurement.std_dev
            elif measurement.meas_type in [MeasType.Ipmu_phase, MeasType.Vpmu_phase]:
                measurement.std_dev = measurement.std_dev
            measurement.meas_value = measurement.meas_value_ideal + measurement.std_dev * err_pu[index]

    # measurement.meas_value = measurement.meas_value_ideal + measurement.std_dev*err_pu[index]

    def getMeasurementsOfType(self, type):
        """
        return an array with all measurements of type "type" in the array MeasurementSet.measurements.
        """
        measurements = []
        for measurement in self.measurements:
            if measurement.meas_type is type:
                measurements.append(measurement)

        return measurements

    def getNumberOfMeasurements(self, type):
        """
        return number of measurements of type "type" in the array MeasurementSet.measurements
        """
        number = 0
        for measurement in self.measurements:
            if measurement.meas_type is type:
                number = number + 1

        return number

    def getIndexOfMeasurements(self, type):
        """
        return index of all measurements of type "type" in the array MeasurementSet.measurements
        """
        idx = np.zeros(self.getNumberOfMeasurements(type), dtype=int)
        i = 0
        for index, measurement in enumerate(self.measurements):
            if measurement.meas_type is type:
                idx[i] = index
                i = i + 1

        return idx

    def getWeightsMatrix(self):
        """
        return an array the weights (obtained as standard_deviations^-2)
        """
        weights = np.zeros(len(self.measurements))
        for index, measurement in enumerate(self.measurements):
            # the weight is small and can bring instability during matrix inversion, so we "cut" everything below 10^-6
            if measurement.std_dev < 10 ** (-6):
                measurement.std_dev = 10 ** (-6)
            weights[index] = (measurement.std_dev) ** (-2)

        return weights

    def getWeightsMatrixActuals(self):
        """
        return an array the weights (obtained as standard_deviations^-2) in actuals
        """
        weights = np.zeros(len(self.measurements))
        for index, measurement in enumerate(self.measurements):
            # the weight is small and can bring instability during matrix inversion, so we "cut" everything below 10^-6
            if measurement.std_dev_act < 10 ** (-6):
                measurement.std_dev_act = 10 ** (-6)
            weights[index] = (measurement.std_dev_act) ** (-2)

        return weights

    def getCovarianceMatrix(self):
        """
        return an array the Measurement Covariance (obtained as standard_deviations^2)
        """
        cov = np.zeros(len(self.measurements))
        for index, measurement in enumerate(self.measurements):
            # the weight is small and can bring instability during matrix inversion, so we "cut" everything below 10^-6
            if measurement.std_dev < 10 ** (-6):
                measurement.std_dev = 10 ** (-6)
            cov[index] = (measurement.std_dev) ** (2)

        return cov

    def getCovarianceMatrixActuals(self):
        """
        return an array the Measurement Covariance (obtained as standard_deviations^-2) in actuals
        """
        cov = np.zeros(len(self.measurements))
        for index, measurement in enumerate(self.measurements):
            # the weight is small and can bring instability during matrix inversion, so we "cut" everything below 10^-6
            if measurement.std_dev_act < 10 ** (-6):
                measurement.std_dev_act = 10 ** (-6)
            cov[index] = (measurement.std_dev_act) ** (2)

        return cov

    def getMeasValues(self):
        """
        returns an array with all measured values (affected by uncertainty)
        """
        meas_real = np.zeros(len(self.measurements))
        for index, measurement in enumerate(self.measurements):
            meas_real[index] = measurement.meas_value

        """ Replace in meas_real amplitude and phase of Vpmu by real and imaginary part """
        # get all measurements of type MeasType.Vpmu_mag
        Vpmu_mag_idx = self.getIndexOfMeasurements(type=MeasType.Vpmu_mag)
        # get all measurements of type MeasType.Vpmu_phase
        Vpmu_phase_idx = self.getIndexOfMeasurements(type=MeasType.Vpmu_phase)
        for vpmu_mag_index, vpmu_phase_index in zip(Vpmu_mag_idx, Vpmu_phase_idx):
            vamp = self.measurements[vpmu_mag_index].meas_value
            vtheta = self.measurements[vpmu_phase_index].meas_value
            meas_real[vpmu_mag_index] = vamp * np.cos(vtheta)
            meas_real[vpmu_phase_index] = vamp * np.sin(vtheta)

        """ Replace in z amplitude and phase of Ipmu by real and imaginary part """
        # get all measurements of type MeasType.Ipmu_mag
        Ipmu_mag_idx = self.getIndexOfMeasurements(type=MeasType.Ipmu_mag)
        # get all measurements of type MeasType.Ipmu_phase
        Ipmu_phase_idx = self.getIndexOfMeasurements(type=MeasType.Ipmu_phase)
        for ipmu_mag_index, ipmu_phase_index in zip(Ipmu_mag_idx, Ipmu_phase_idx):
            iamp = self.measurements[ipmu_mag_index].meas_value
            itheta = self.measurements[ipmu_phase_index].meas_value
            meas_real[ipmu_mag_index] = iamp * np.cos(itheta)
            meas_real[ipmu_phase_index] = iamp * np.sin(itheta)

        """ Replace in z amplitude and phase of Ipmu_inj by real and imaginary part """
        # get all measurements of type MeasType.Ipmu_mag
        Ipmu_inj_mag_idx = self.getIndexOfMeasurements(type=MeasType.Ipmu_inj_mag)
        # get all measurements of type MeasType.Ipmu_phase
        Ipmu_inj_phase_idx = self.getIndexOfMeasurements(type=MeasType.Ipmu_inj_phase)
        for ipmu_inj_mag_index, ipmu_inj_phase_index in zip(Ipmu_inj_mag_idx, Ipmu_inj_phase_idx):
            iamp = self.measurements[ipmu_inj_mag_index].meas_value
            itheta = self.measurements[ipmu_inj_phase_index].meas_value
            meas_real[ipmu_inj_mag_index] = iamp * np.cos(itheta)
            meas_real[ipmu_inj_phase_index] = iamp * np.sin(itheta)

        return meas_real

    def getMeasValuesActuals(self):
        """
        returns an array with all measured values (affected by uncertainty)
        """
        meas_real = np.zeros(len(self.measurements))
        for index, measurement in enumerate(self.measurements):
            meas_real[index] = measurement.meas_value_act

        """ Replace in meas_real amplitude and phase of Vpmu by real and imaginary part """
        # get all measurements of type MeasType.Vpmu_mag
        Vpmu_mag_idx = self.getIndexOfMeasurements(type=MeasType.Vpmu_mag)
        # get all measurements of type MeasType.Vpmu_phase
        Vpmu_phase_idx = self.getIndexOfMeasurements(type=MeasType.Vpmu_phase)
        for vpmu_mag_index, vpmu_phase_index in zip(Vpmu_mag_idx, Vpmu_phase_idx):
            vamp = self.measurements[vpmu_mag_index].meas_value_act
            vtheta = self.measurements[vpmu_phase_index].meas_value_act
            meas_real[vpmu_mag_index] = vamp * np.cos(vtheta)
            meas_real[vpmu_phase_index] = vamp * np.sin(vtheta)

        """ Replace in z amplitude and phase of Ipmu by real and imaginary part """
        # get all measurements of type MeasType.Ipmu_mag
        Ipmu_mag_idx = self.getIndexOfMeasurements(type=MeasType.Ipmu_mag)
        # get all measurements of type MeasType.Ipmu_phase
        Ipmu_phase_idx = self.getIndexOfMeasurements(type=MeasType.Ipmu_phase)
        for ipmu_mag_index, ipmu_phase_index in zip(Ipmu_mag_idx, Ipmu_phase_idx):
            iamp = self.measurements[ipmu_mag_index].meas_value_act
            itheta = self.measurements[ipmu_phase_index].meas_value_act
            meas_real[ipmu_mag_index] = iamp * np.cos(itheta)
            meas_real[ipmu_phase_index] = iamp * np.sin(itheta)

        """ Replace in z amplitude and phase of Ipmu_inj by real and imaginary part """
        # get all measurements of type MeasType.Ipmu_mag
        Ipmu_inj_mag_idx = self.getIndexOfMeasurements(type=MeasType.Ipmu_inj_mag)
        # get all measurements of type MeasType.Ipmu_phase
        Ipmu_inj_phase_idx = self.getIndexOfMeasurements(type=MeasType.Ipmu_inj_phase)
        for ipmu_inj_mag_index, ipmu_inj_phase_index in zip(Ipmu_inj_mag_idx, Ipmu_inj_phase_idx):
            iamp = self.measurements[ipmu_inj_mag_index].meas_value_act
            itheta = self.measurements[ipmu_inj_phase_index].meas_value_act
            meas_real[ipmu_inj_mag_index] = iamp * np.cos(itheta)
            meas_real[ipmu_inj_phase_index] = iamp * np.sin(itheta)

        return meas_real
    
    def getSortedMeasurementSet(self):
        """
        Sorts measurements in the order required by the SE algorithm
        """
        
        sortedMeasurementSet = MeasurementSet()

        # Sort measurements  in the order required by the SE algorithm
        # Required order: Vmag, Pinj, Qinj, P1, Q1, P2, Q2, Imag, Vpmu_mag, Vpmu_phase, Ipmu_mag, Ipmu_phase, Ipmu_inj_mag, Ipmu_inj_phase
        for type_meas in [MeasType.V_mag, MeasType.Sinj_real, MeasType.Sinj_imag, MeasType.S1_real, MeasType.S1_imag, \
                         MeasType.S2_real, MeasType.S2_imag, MeasType.I_mag, MeasType.Vpmu_mag, MeasType.Vpmu_phase, MeasType.Ipmu_mag, MeasType.Ipmu_phase, MeasType.Ipmu_inj_mag, MeasType.Ipmu_inj_phase]:
            sortedMeasurementSet.measurements += self.getMeasurementsOfType(type_meas)
        return sortedMeasurementSet


    def getStd_Dev(self):
        """
        for test purposes
        returns an array with all standard deviations
        """
        std_dev = np.zeros(len(self.measurements))
        for index, measurement in enumerate(self.measurements):
            std_dev[index] = measurement.std_dev

        return std_dev

    def getIdealMeasValues(self, type=None):
        """
        for test purposes
        returns an array with all measured values
        """
        if type is None:
            meas_val = np.zeros(len(self.measurements))
            for index, measurement in enumerate(self.measurements):
                meas_val[index] = measurement.meas_value_ideal
        else:
            meas_val = np.zeros(self.getNumberOfMeasurements(type=type))
            idx = 0
            for index, measurement in enumerate(self.measurements):
                if measurement.meas_type is type:
                    meas_val[idx] = measurement.meas_value_ideal
                    idx += 1

        return meas_val

    def getMeasValuesTest(self, type=None):
        """
        returns an array with all measured values (affected by uncertainty)
        """
        if type is None:
            meas_real = np.zeros(len(self.measurements))
            for index, measurement in enumerate(self.measurements):
                meas_real[index] = measurement.meas_value
        else:
            meas_real = np.zeros(self.getNumberOfMeasurements(type=type))
            idx = 0
            for index, measurement in enumerate(self.measurements):
                if measurement.meas_type is type:
                    meas_real[idx] = measurement.meas_value
                    idx += 1

        return meas_real

    @staticmethod
    def mergeMeasurementSets(meas_set_1, meas_set_2):
        meas_set = MeasurementSet()
        meas_set.measurements = meas_set_1.measurements + meas_set_2.measurements
        return meas_set

