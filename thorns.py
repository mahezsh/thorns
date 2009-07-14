# Thorns:  spike analysis software

import numpy as np

def signal_to_spikes_1D(fs, f):
    """
    Convert time function 1D array into spike events array.
    """
    import _cThorns
    # TODO: catch import error and use python implementation instead

    assert f.ndim == 1

    f = np.asarray(f).astype(int)
    fs = float(fs)

    spikes = _cThorns.c_signal_to_spikes(f) * 1000 / fs

    # non_empty = np.where(f > 0)[0]
    # spikes = []
    # for time_idx in non_empty:
    #     time_samp = f[time_idx]
    #     spikes.extend([1000 * time_idx/fs for each in range(time_samp)]) # ms
    # spikes = np.asarray(spikes)

    return spikes


def signal_to_spikes(fs, f):
    """
    Convert time functions to a list of spike trains.
    """
    fs = float(fs)

    spike_trains = []

    if f.ndim == 1:
        spike_trains.append(signal_to_spikes_1D(fs, f))
    elif f.ndim == 2:
        for f_1D in f.T:
            spike_trains.append(signal_to_spikes_1D(fs, f_1D))
    else:
        assert False

    return spike_trains



def test_signal_to_spikes():
    print "signal_to_spikes: ",
    fs = 1000
    a = np.array([[0,0,0,1,0,0],
                  [0,2,1,0,0,0]]).T
    expected = [np.array([3]),
                np.array([1,1,2])]

    out = signal_to_spikes(fs, a)
    for i in range(len(out)):
        assert np.all(expected[i] == out[i])
    print "OK"



def spikes_to_signal_1D(fs, spikes, tmax=None):
    """
    Convert spike train to its time function. 1D version.
    """
    # Test if all elements are floats (1D case)
    #assert np.all([isinstance(each, float) for each in spikes])

    # TODO: implement with np.histogram

    if tmax == None:
        tmax = max(spikes)

    f = np.zeros(np.floor(tmax * fs) + 1)

    # TODO: vecotorize
    # f[np.floor(spikes * fs).astype(int)] += 1
    for spike in spikes:
        f[int(np.floor(spike*fs))] += 1

    return f


def spikes_to_signal(fs, spikes):
    """
    Convert spike trains to theirs time functions.
    """
    # All elements are list (2D case)
    if np.all([isinstance(each, np.ndarray) for each in spikes]):

        f_list = []
        for train in spikes:
            f1d = spikes_to_signal_1D(fs, train)
            f_list.append(f1d)

        # Adjust length of each time function to the maximum
        max_len = max([len(f1d) for f1d in f_list])

        # Construct output
        f = np.zeros( (max_len, len(f_list)) )

        for i,f1d in enumerate(f_list):
            f[0:len(f1d), i] = f1d



    else:
        f = spikes_to_signal_1D(fs, spikes)

    return f


def plot_raster(spikes):
    import matplotlib.pyplot as plt

    # Assert list of arrays as input
    assert np.all([isinstance(each, np.ndarray) for each in spikes])

    n = []
    s = []
    for i,train in enumerate(spikes):
        s.extend(train)                 # flatten spikes
        n.extend([i for each in train]) # trial number

    plt.plot(s, n, 'o')
    plt.show()


def plot_psth(spikes, bin_size=1, axis=None, tmax=None, **kwargs):
    """
    Plots PSTH from spikes (list of arrays of spike timings)

    bin_size: bin size in ms
    axis: axis to draw on
    """
    import matplotlib.pyplot as plt


    # Assert list of arrays as input
    #assert np.all([isinstance(each, np.ndarray) for each in spikes])

    all_spikes = np.concatenate(tuple(spikes))


    # Remove entries greater than tmax
    if tmax != None:
        all_spikes = np.delete(all_spikes, np.where(np.asarray(all_spikes) > tmax)[0])

    if len(all_spikes) != 0:

        # bin size = 1ms
        nbins = np.floor((max(all_spikes) - min(all_spikes)) / float(bin_size))

        if axis == None:
            axis = plt.gca()
            axis.hist(all_spikes, nbins, **kwargs)
            plt.show()
        else:
            axis.hist(all_spikes, nbins, **kwargs)



def synchronization_index(Fstim, spikes):
    """
    Calculate Synchronization Index.

    Fstim: stimulus frequency in Hz
    spikes: list of arrays of spiking times

    return: synchronization index
    """
    Fstim = float(Fstim)
    Fstim = Fstim / 1000        # Hz -> kHz

    all_spikes = np.concatenate(tuple(spikes))

    # TODO: remove here spikes from the beginning and the end

    all_spikes = all_spikes - all_spikes.min()

    #bins = 360                  # number of bins per Fstim period
    # hist_range = (0, 1/Fstim)
    # ph = np.zeros(bins)
    # period_num = np.floor(all_spikes.max() * Fstim) + 1

    # for i in range(period_num):
    #     lo = i / Fstim
    #     hi = lo + 1/Fstim
    #     current_spikes = all_spikes[(all_spikes >= lo) & (all_spikes < hi)]
    #     ph += np.histogram(current_spikes-lo, bins=bins, range=hist_range)[0]

    folded = np.fmod(all_spikes, 1/Fstim)
    ph = np.histogram(folded, bins=180)[0]

    # indexing trick is necessary, because the sample at 2*pi belongs
    # to the next cycle
    x = np.cos(np.linspace(0, 2*np.pi, len(ph)+1))[0:-1]
    y = np.sin(np.linspace(0, 2*np.pi, len(ph)+1))[0:-1]

    xsum2 = (np.sum(x*ph))**2
    ysum2 = (np.sum(y*ph))**2

    r = np.sqrt(xsum2 + ysum2) / np.sum(ph)

    return r



def test_synchronization_index():
    fs = 36000.0
    Fstim = 100.0

    test0 = [np.arange(0, 0.1, 1/fs)*1000, np.arange(0, 0.1, 1/fs)*1000]
    si0 = synchronization_index(Fstim, test0)
    print "test0 SI: ", si0,
    assert si0 < 1e-4
    print "OK"

    test1 = [np.zeros(fs)]
    si1 = synchronization_index(Fstim, test1)
    print "test1 SI: ", si1,
    assert si1 == 1
    print "OK"



def test_c_signal_to_spikes():
    print "cThorns: ",
    import _cThorns

    a = np.array([0,0,1,2,0,1])
    expected = np.array([2,3,3,5])

    result = _cThorns.c_signal_to_spikes(a)
    assert np.all(result == expected)
    print "OK"




def _unnormalized_correlation_index(spike_trains, window_len=0.05):
    """
    Computes unnormalized correlation index. (Joris et al. 2006)


    >>> trains = [np.array([1, 2]), np.array([1.03, 2, 3])]
    >>> _unnormalized_correlation_index(trains)
    3
    """
    all_spikes = np.concatenate(tuple(spike_trains))

    Nc = 0                      # Total number of coincidences

    for spike in all_spikes:
        hits = all_spikes[(all_spikes >= spike) &
                          (all_spikes <= spike+window_len)]
        Nc += len(hits) - 1     # current spike included therefore -1

    return Nc


if __name__ == "__main__":
    import doctest

    # test_c_signal_to_spikes()
    # test_signal_to_spikes()
    # test_synchronization_index()

    doctest.testmod()
