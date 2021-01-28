import numpy as np


def detect_anomaly(references, point, threshold=3.0):
    '''
    The values of anomaly points are always smaller than correct values
    '''
    mean = np.mean(references)
    std = np.std(references)
    if point < mean - threshold * std:
        return True

    return False


def detect_anomaly_t(references, point):
    '''
    Anomaly temperature points always have no more than one decimal point
    '''
    if (point * 10) % 1 > 1E-3:
        return False

    return detect_anomaly(references, point)


def detect_anomaly_p(references, point):
    '''
    Anomaly pressure points always have values much smaller than correct values
    '''
    if point > np.mean(references) / 2:
        return False

    return detect_anomaly(references, point)


def detect_convergence(array):
    '''
    Detect whether and when the time series converges
    '''
    pass
