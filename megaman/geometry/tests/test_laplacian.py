# <<<<<<< HEAD
from __future__ import division ## removes integer division

import os
import numpy as np
from scipy import io
from scipy import sparse
from nose.tools import assert_raises
from numpy.testing import assert_array_almost_equal, assert_array_equal
from scipy.spatial.distance import pdist, squareform
from megaman.geometry.distance import distance_matrix
import megaman.geometry.geometry as geom
from megaman.geometry.distance import distance_matrix
from megaman.geometry.geometry import laplacian_types
from megaman.geometry.affinity import compute_affinity_matrix
from megaman.geometry.laplacian import compute_laplacian_matrix

random_state = np.random.RandomState(36)
n_sample = 10
d = 2
X = random_state.randn(n_sample, d)
D = squareform(pdist(X))
D[D > 1/d] = 0
# =======
import os

import numpy as np
from numpy.testing import assert_allclose, assert_equal

from scipy.sparse import isspmatrix, csr_matrix
from scipy import io

from megaman.geometry.adjacency_new import compute_adjacency_matrix
from megaman.geometry.affinity_new import compute_affinity_matrix
from megaman.geometry.laplacian_new import Laplacian, compute_laplacian_matrix

# >>>>>>> distance_refactor

TEST_DATA = os.path.join(os.path.dirname(__file__),
                        'testmegaman_laplacian_rad0_2_lam1_5_n200.mat')

# <<<<<<< HEAD
def _load_test_data():
    """ Loads a .mat file from . that contains the following dense matrices
    test_dist_matrix
    Lsymnorm, Lunnorm, Lgeom, Lreno1_5, Lrw
    rad = scalar, radius used in affinity calculations, Laplacians
        Note: rad is returned as an array of dimension 1. Outside one must
        make it a scalar by rad = rad[0]
    """
    xdict = io.loadmat(TEST_DATA)

    rad = xdict[ 'rad' ]
    test_dist_matrix = xdict[ 'S' ] # S contains squared distances
    test_dist_matrix = np.sqrt( test_dist_matrix )
    Lsymnorm = xdict[ 'Lsymnorm' ]
    Lunnorm = xdict[ 'Lunnorm' ]
    Lgeom = xdict[ 'Lgeom' ]
    Lrw = xdict[ 'Lrw' ]
    Lreno1_5 = xdict[ 'Lreno1_5' ]
    A = xdict[ 'A' ]
    return rad, test_dist_matrix, A, Lsymnorm, Lunnorm, Lgeom, Lreno1_5, Lrw

def test_laplacian_unknown_method():
    """Test that laplacian fails with an unknown method type"""
    A = np.array([[ 5, 2, 1 ], [ 2, 3, 2 ],[1,2,5]])
    assert_raises(ValueError, compute_laplacian_matrix, A, method='<unknown>')

def test_equal_original(almost_equal_decimals = 5):
    """ Loads the results from a matlab run and checks that our results
    are the same. The results loaded are A the similarity matrix and
    all the Laplacians, sparse and dense.
    """

    rad, test_dist_matrix, Atest, Lsymnorm, Lunnorm, Lgeom, Lreno1_5, Lrw = _load_test_data()

    rad = rad[0]
    rad = rad[0]
    A_dense = compute_affinity_matrix(test_dist_matrix, method = 'auto',
                                      radius = rad)
    A_sparse = compute_affinity_matrix(sparse.csr_matrix(test_dist_matrix),
                                       method = 'auto', radius=rad)
    B = A_sparse.toarray()
    B[ B == 0. ] = 1.
    assert_array_almost_equal( A_dense, B, almost_equal_decimals )
    assert_array_almost_equal( Atest, A_dense, almost_equal_decimals )
    for (A, issparse) in [(Atest, False), (sparse.coo_matrix(Atest), True)]:
        for (Ltest, method ) in [(Lsymnorm, 'symmetricnormalized'),
                                 (Lunnorm, 'unnormalized'), (Lgeom, 'geometric'),
                                 (Lrw, 'randomwalk'), (Lreno1_5, 'renormalized')]:
            L, diag =  compute_laplacian_matrix(A, method=method,
                                        symmetrize=True, scaling_epps=rad,
                                        renormalization_exponent=1.5,
                                        return_diag=True)
            if issparse:
                assert_array_almost_equal( L.toarray(), Ltest, 5 )
                diag_mask = (L.row == L.col )
                assert_array_equal(diag, L.data[diag_mask].squeeze())
            else:
                assert_array_almost_equal( L, Ltest, 5 )
                di = np.diag_indices( L.shape[0] )
                assert_array_equal(diag, np.array( L[di] ))
# =======

def test_laplacian_vs_matlab():
    # Test that the laplacian calculation matches the matlab result
    matlab = io.loadmat(TEST_DATA)

    laplacians = {'unnormalized': matlab['Lunnorm'],
                  'symmetricnormalized': matlab['Lsymnorm'],
                  'geometric': matlab['Lgeom'],
                  'randomwalk': matlab['Lrw'],
                  'renormalized': matlab['Lreno1_5']}

    radius = matlab['rad'][0]

    def check_laplacian(input_type, laplacian_method):
        kwargs = {'scaling_epps': radius}
        if laplacian_method == 'renormalized':
            kwargs['renormalization_exponent'] = 1.5
        adjacency = input_type(np.sqrt(matlab['S']))
        affinity = compute_affinity_matrix(adjacency, radius=radius)
        laplacian = compute_laplacian_matrix(affinity,
                                             method=laplacian_method,
                                             **kwargs)
        if input_type is csr_matrix:
            laplacian = laplacian.toarray()
        assert_allclose(laplacian, laplacians[laplacian_method])

    for input_type in [np.array, csr_matrix]:
        for laplacian_method in laplacians:
            yield check_laplacian, input_type, laplacian_method


def test_laplacian_smoketest():
    rand = np.random.RandomState(42)
    X = rand.rand(20, 2)
    adj = compute_adjacency_matrix(X, radius=0.5)
    aff = compute_affinity_matrix(adj, radius=0.1)

    def check_laplacian(method):
        lap = compute_laplacian_matrix(aff, method=method)

        assert isspmatrix(lap)
        assert_equal(lap.shape, (X.shape[0], X.shape[0]))

    for method in Laplacian.asymmetric_methods():
        yield check_laplacian, method


def test_laplacian_full_output():
    # Test that full_output symmetrized laplacians have the right form
    rand = np.random.RandomState(42)
    X = rand.rand(20, 2)

    def check_symmetric(method, adjacency_radius, affinity_radius):
        adj = compute_adjacency_matrix(X, radius=adjacency_radius)
        aff = compute_affinity_matrix(adj, radius=affinity_radius)
        lap, lapsym, w = compute_laplacian_matrix(aff, method=method,
                                                  full_output=True)

        sym = w[:, np.newaxis] * (lap.toarray() + np.eye(*lap.shape))

        assert_allclose(lapsym.toarray(), sym)

    for method in Laplacian.asymmetric_methods():
        for adjacency_radius in [0.5, 1.0]:
            for affinity_radius in [0.1, 0.3]:
                yield check_symmetric, method, adjacency_radius, affinity_radius
# >>>>>>> distance_refactor
