"""Standard reliability and covariation measures."""

from __future__ import division

import numpy as np
import scipy.stats

from pyanno.util import is_valid, MISSING_VALUE


def pearsons_rho(annotations1, annotations2, nclasses=None):
    """Compute Pearson's product-moment correlation coefficient."""

    valid = is_valid(annotations1) & is_valid(annotations2)
    if all(~valid): return np.nan
    rho, pval = scipy.stats.pearsonr(annotations1[valid], annotations2[valid])
    return rho


def spearmans_rho(annotations1, annotations2, nclasses=None):
    """Compute Spearman's rank correlation coefficient."""

    valid = is_valid(annotations1) & is_valid(annotations2)
    if all(~valid): return np.nan
    rho, pval = scipy.stats.spearmanr(annotations1[valid], annotations2[valid])
    return rho


def cronbachs_alpha(annotations, nclasses=None):
    """Compute Cronbach's alpha."""

    nitems = annotations.shape[0]
    valid_anno = np.ma.masked_equal(annotations, MISSING_VALUE)

    item_var = valid_anno.var(1, ddof=1)
    total_var = valid_anno.sum(0).var(ddof=1)

    return nitems/(nitems - 1.) * (1. - item_var.sum() / total_var)
