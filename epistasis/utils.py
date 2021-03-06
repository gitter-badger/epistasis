__doc__ = """Submodule with handy utilities for constructing epistasis models."""
# -------------------------------------------------------
# Miscellaneous Python functions for random task
# -------------------------------------------------------

import itertools as it
import numpy as np
from scipy.misc import comb
from sklearn.metrics import mean_squared_error
from collections import OrderedDict

# -------------------------------------------------------
#
# -------------------------------------------------------

class SubclassException(Exception):
    """ For methods that must be implemented in a subclass. """

# -------------------------------------------------------
# Model Parameter methods
# -------------------------------------------------------

class Bunch:
    """Classic bunch object for constructing empty objects."""
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def update(self, **kwargs):
        """Turn a dictionary into an object with"""
        types = dict([(key, type(val)) for key, val in self.__dict__.items()])
        for key, value in kwargs.items():
            typed = types[key]
            if typed == np.ufunc:
                typed_val = value
            elif self.__dict__[key] == None:
                typed_val = value
            else:
                typed_val = types[key](value)
            setattr(self, key, typed_val)


def label_to_key(label, state=""):
    """ Convert interaction label to key. `state` is added to end of key."""
    if type(state) != str:
        raise Exception("`state` must be a string.")
    return ",".join([str(l) for l in label]) + state

def label_to_lmfit(label, state=""):
    if type(state) != str:
        raise Exception("`state` must be a string.")
    return "K" + "_".join([str(l) for l in label]) + state

def key_to_label(key):
    """ Convert an interaction key to label."""
    return [int(k) for k in key.split(",")]

def epistatic_order_indices(length, order):
    """ Return  the indices of interactions with the given order.

    Parameters
    ----------
    length : int
        length of the sequences
    order : int
        order of interactions to return
    """
    start = int(sum([comb(length, i) for i in range(order)]))
    stop = int(start + comb(length, order))
    return start, stop


def genotype_params(genotype, order=None):
    """List the possible parameters (as label form) for a binary genotype
    up to a given order.
    """
    if order is None:
        order = len(genotype)

    length = len(genotype)

    mutations = [i + 1 for i in range(length) if genotype[i] == "1"]
    params = [[0]]
    for o in range(1, order+1):
        params += [list(z) for z in it.combinations(mutations, o)]

    return params

def build_interaction_labels(length, order):
    """Return interactions labels for building X matrix. """
    labels = [[0]]
    for o in range(1,order+1):
        for label in it.combinations(range(1,length+1), o):
            labels.append(list(label))
    return labels

def params_index_map(mutations):
    """Write a dictionary that maps mutations dictionary to indices in dummy
    variable matrix.

    Parameters
    ----------
    mutations : dict
        mapping each site to their accessible mutations alphabet.
        mutations = {site_number : alphabet} If site does not mutate,
        value should be None.

    Returns
    -------
    mutations : dict
        `mutations = { site_number : indices }`. If the site alphabet is
        note included, the model will assume binary between wildtype and derived.

    Example
    -------
    .. code-block:: python

        mutations = {
            0: [indices],
            1: [indices],
            ...
        }
    """
    param_map = dict()
    n_sites = 1
    for m in mutations:
        if mutations[m] is None:
            param_map[m] = None
        else:
            param_map[m] = list(range(n_sites, n_sites + len(mutations[m]) - 1))
            n_sites += len(mutations[m])-1
    return param_map

def build_model_params(length, order, mutations, start_order=0):
    """ Build interaction labels up to nth order given a mutation alphabet.

    Parameters
    ----------
    n : int
        order of interactions
    mutations  : dict
        `mutations = { site_number : indices }`. If the site
        alphabet is note included, the model will assume binary
        between wildtype and derived.

    Example
    -------
    .. code-block:: python

        mutations = {
            0: [indices],
            1: [indices],
            ...
        }

    Returns
    -------
    interactions : list
        list of all interaction labels for system with
        sequences of a given length and epistasis with given order.
    """
    # Include the intercept interaction?
    if start_order == 0:
        interactions = [[0]]
        orders = range(1,order+1)
    else:
        interactions = list()
        orders = range(start_order,order+1)


    # Recursive algorithm that's difficult to follow.

    # Iterate through each order
    for o in orders:

        # Iterate through all combinations of orders with given length
        for term in it.combinations(range(length), o):
            # If any sites in `term` == None, skip this term.
            bad_term = False
            lists = []
            for i in range(len(term)):
                if mutations[term[i]] == None:
                    bad_term = True
                    break
                else:
                    lists.append(mutations[term[i]])

            # Else, add interactions combinations to list
            if bad_term is False:
                for r in it.product(*lists):
                    interactions.append(list(r))


    return interactions
