from __future__ import division

import unittest
import numpy as np
import pyanno

import pyanno.measures as pm


class Bunch(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class TestMeasures(unittest.TestCase):

    def setUp(self):
        """Define fixtures."""

        # ---- annotations for fully agreeing annotators
        nitems = 100
        nannotators = 5
        nclasses = 4

        # perfect agreement, 2 missing annotations per row
        annotations = np.empty((nitems, nannotators), dtype=int)

        for i in xrange(nitems):
            annotations[i,:] = np.random.randint(nclasses)
            perm = np.random.permutation(nclasses)
            annotations[i,perm[0:2]] = -1

        self.full_agreement = Bunch(nitems=nitems,
                                    nannotators=nannotators,
                                    nclasses=nclasses,
                                    annotations=annotations)

        # ---- test example from
        # http://en.wikipedia.org/wiki/Krippendorff%27s_Alpha#A_computational_example
        annotations = np.array(
            [
                [-1,  1, -1],
                [-1, -1, -1],
                [-1,  2,  2],
                [-1,  1,  1],
                [-1,  3,  3],
                [ 3,  3,  4],
                [ 4,  4,  4],
                [ 1,  3, -1],
                [ 2, -1,  2],
                [ 1, -1,  1],
                [ 1, -1,  1],
                [ 3, -1,  3],
                [ 3, -1,  3],
                [-1, -1, -1],
                [ 3, -1,  4]
            ]
        )
        annotations[annotations>=0] -= 1
        coincidence = np.array(
            [
                [6, 0, 1, 0],
                [0, 4, 0, 0],
                [1, 0, 7, 2],
                [0, 0, 2, 3]
            ]
        )
        nc = np.array([7, 4, 10, 5])
        self.krippendorff_example = Bunch(annotations = annotations,
                                          coincidence = coincidence,
                                          nc = nc,
                                          nclasses = 4,
                                          alpha_diagonal = 0.811,
                                          alpha_binary = 0.691)

    def test_confusion_matrix(self):
        anno1 = np.array([0, 0, 1, 1, 2, 3])
        anno2 = np.array([0, 1, 1, 1, 2, 2])
        expected = np.array(
            [
                [1, 1, 0, 0],
                [0, 2, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 0]
            ])
        cm = pm.confusion_matrix(anno1, anno2, 4)
        np.testing.assert_array_equal(cm, expected)


    def test_confusion_matrix_missing(self):
        """Test confusion matrix with missing data."""
        anno1 = np.array([0, 0, 1, 1, -1, 3])
        anno2 = np.array([0, -1, 1, 1, 2, 2])
        expected = np.array(
            [
                [1, 0, 0, 0],
                [0, 2, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 1, 0]
            ])
        cm = pm.confusion_matrix(anno1, anno2, 4)
        np.testing.assert_array_equal(cm, expected)


    def test_chance_agreement_same_frequency(self):
        distr = np.array([0.1, 0.5, 0.4])
        anno1 = pyanno.util.random_categorical(distr, nsamples=10000)
        anno2 = pyanno.util.random_categorical(distr, nsamples=10000)

        expected = distr ** 2.
        freqs = pm.chance_agreement_same_frequency(anno1, anno2, len(distr))

        np.testing.assert_allclose(freqs, expected, atol=1e-2, rtol=0.)


    def test_chance_agreement_different_frequency(self):
        distr1 = np.array([0.1, 0.5, 0.4])
        distr2 = np.array([0.6, 0.2, 0.2])
        anno1 = pyanno.util.random_categorical(distr1, nsamples=10000)
        anno2 = pyanno.util.random_categorical(distr2, nsamples=10000)

        expected = distr1 * distr2
        freqs = pm.chance_agreement_different_frequency(anno1, anno2,
                                                        len(distr1))

        np.testing.assert_allclose(freqs, expected, atol=1e-2, rtol=0.)


    def test_observed_agreement(self):
        anno1 = np.array([0, 0, 1, 1, -1, 3])
        anno2 = np.array([0, -1, 1, 1, -1, 2])
        nvalid = np.sum((anno1!=-1) & (anno2!=-1))

        expected = np.array([1., 2., 0., 0.]) / nvalid
        freqs = pm.observed_agreement_frequency(anno1, anno2, 4)

        np.testing.assert_array_equal(freqs, expected)


    def test_cohens_kappa(self):
        # test basic functionality with full agreement, missing annotations
        fa = self.full_agreement

        self.assertEqual(pm.cohens_kappa(fa.annotations[:,0],
                                         fa.annotations[:,1]),
                         1.0)


    def test_cohens_weighted_kappa(self):
        # test basic functionality with full agreement, missing annotations
        fa = self.full_agreement

        self.assertEqual(pm.cohens_weighted_kappa(fa.annotations[:,0],
                                                  fa.annotations[:,1]),
                         1.0)


    def test_cohens_weighted_kappa2(self):
        # cohen's weighted kappa is the same as cohen's kappa when
        # the weights are 0. on the diagonal and 1. elsewhere
        anno1 = np.array([0, 0, 1, 2, 1, -1, 3])
        anno2 = np.array([0, -1, 1, 0, 1, -1, 2])
        weighted_kappa = pm.cohens_weighted_kappa(anno1, anno2,
                                                  pm.binary_distance)
        cohens_kappa = pm.cohens_kappa(anno1, anno2)
        self.assertAlmostEqual(weighted_kappa, cohens_kappa, 6)


    def test_scotts_pi(self):
        # test basic functionality with full agreement, missing annotations
        fa = self.full_agreement

        self.assertEqual(pm.scotts_pi(fa.annotations[:,0],
                                      fa.annotations[:,1]),
                         1.0)


    def test_fleiss_kappa_nannotations(self):
        # same example as
        # http://en.wikipedia.org/wiki/Fleiss%27_kappa#Worked_example
        nannotations = np.array(
            [
                [0, 0, 0, 0, 14],
                [0, 2, 6, 4, 2],
                [0, 0, 3, 5, 6],
                [0, 3, 9, 2, 0],
                [2, 2, 8, 1, 1],
                [7, 7, 0, 0, 0],
                [3, 2, 6, 3, 0],
                [2, 5, 3, 2, 2],
                [6, 5, 2, 1, 0],
                [0, 2, 2, 3, 7]
            ]
        )
        expected = 0.21
        kappa = pm._fleiss_kappa_nannotations(nannotations)
        self.assertAlmostEqual(kappa, expected, 2)


    def test_fleiss_kappa(self):
        # test basic functionality with full agreement, missing annotations
        fa = self.full_agreement

        self.assertEqual(pm.fleiss_kappa(fa.annotations, fa.nclasses), 1.0)

        # unequal number of annotators per row
        fa.annotations[0,:] = -1
        self.assertRaises(ValueError, pm.fleiss_kappa, fa.annotations)


    def test_krippendorffs_alpha(self):
        # test basic functionality with full agreement, missing annotations
        fa = self.full_agreement

        self.assertEqual(pm.krippendorffs_alpha(fa.annotations),
                         1.0)


    def test_coincidence_matrix(self):
        # test example from
        # http://en.wikipedia.org/wiki/Krippendorff%27s_Alpha#A_computational_example
        kr = self.krippendorff_example
        coincidence = pm._coincidence_matrix(kr.annotations, kr.nclasses)
        np.testing.assert_allclose(coincidence, kr.coincidence)

    def test_krippendorffs_alpha2(self):
        # test example from
        # http://en.wikipedia.org/wiki/Krippendorff%27s_Alpha#A_computational_example
        kr = self.krippendorff_example

        alpha = pm.krippendorffs_alpha(kr.annotations,
                                       metric_func=pm.binary_distance)
        self.assertAlmostEqual(alpha, kr.alpha_binary, 3)

        alpha = pm.krippendorffs_alpha(kr.annotations,
                                       metric_func=pm.diagonal_distance)
        self.assertAlmostEqual(alpha, kr.alpha_diagonal, 3)