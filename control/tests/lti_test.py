"""lti_test.py"""

import numpy as np
import pytest

from control import c2d, tf, tf2ss, NonlinearIOSystem
from control.lti import (LTI, common_timebase, damp, dcgain, isctime, isdtime,
                         issiso, pole, timebaseEqual, zero)
from control.tests.conftest import slycotonly


class TestLTI:

    def test_pole(self):
        sys = tf(126, [-1, 42])
        np.testing.assert_equal(sys.pole(), 42)
        np.testing.assert_equal(pole(sys), 42)

    def test_zero(self):
        sys = tf([-1, 42], [1, 10])
        np.testing.assert_equal(sys.zero(), 42)
        np.testing.assert_equal(zero(sys), 42)

    def test_issiso(self):
        assert issiso(1)
        with pytest.raises(ValueError):
            issiso(1, strict=True)

        # SISO transfer function
        sys = tf([-1, 42], [1, 10])
        assert issiso(sys)
        assert issiso(sys, strict=True)

        # SISO state space system
        sys = tf2ss(sys)
        assert issiso(sys)
        assert issiso(sys, strict=True)

    @slycotonly
    def test_issiso_mimo(self):
        # MIMO transfer function
        sys = tf([[[-1, 41], [1]], [[1, 2], [3, 4]]],
                 [[[1, 10], [1, 20]], [[1, 30], [1, 40]]]);
        assert not issiso(sys)
        assert not issiso(sys, strict=True)

        # MIMO state space system
        sys = tf2ss(sys)
        assert not issiso(sys)
        assert not issiso(sys, strict=True)

    def test_damp(self):
        # Test the continuous time case.
        zeta = 0.1
        wn = 42
        p = -wn * zeta + 1j * wn * np.sqrt(1 - zeta**2)
        sys = tf(1, [1, 2 * zeta * wn, wn**2])
        expected = ([wn, wn], [zeta, zeta], [p, p.conjugate()])
        np.testing.assert_equal(sys.damp(), expected)
        np.testing.assert_equal(damp(sys), expected)

        # Also test the discrete time case.
        dt = 0.001
        sys_dt = c2d(sys, dt, method='matched')
        p_zplane = np.exp(p*dt)
        expected_dt = ([wn, wn], [zeta, zeta],
                       [p_zplane, p_zplane.conjugate()])
        np.testing.assert_almost_equal(sys_dt.damp(), expected_dt)
        np.testing.assert_almost_equal(damp(sys_dt), expected_dt)

    def test_dcgain(self):
        sys = tf(84, [1, 2])
        np.testing.assert_equal(sys.dcgain(), 42)
        np.testing.assert_equal(dcgain(sys), 42)

    @pytest.mark.parametrize("dt1, dt2, expected",
                             [(None, None, True),
                              (None, 0, True),
                              (None, 1, True),
                              pytest.param(None, True, True,
                                           marks=pytest.mark.xfail(
                                               reason="returns false")),
                              (0, 0, True),
                              (0, 1, False),
                              (0, True, False),
                              (1, 1, True),
                              (1, 2, False),
                              (1, True, False),
                              (True, True, True)])
    def test_timebaseEqual_deprecated(self, dt1, dt2, expected):
        """Test that timbaseEqual throws a warning and returns as documented"""
        sys1 = tf([1], [1, 2, 3], dt1)
        sys2 = tf([1], [1, 4, 5], dt2)

        print(sys1.dt)
        print(sys2.dt)

        with pytest.deprecated_call():
            assert timebaseEqual(sys1, sys2) is expected
        # Make sure behaviour is symmetric
        with pytest.deprecated_call():
            assert timebaseEqual(sys2, sys1) is expected

    @pytest.mark.parametrize("dt1, dt2, expected",
                             [(None, None, None),
                              (None, 0, 0),
                              (None, 1, 1),
                              (None, True, True),
                              (True, True, True),
                              (True, 1, 1),
                              (1, 1, 1),
                              (0, 0, 0),
                              ])
    @pytest.mark.parametrize("sys1", [True, False])
    @pytest.mark.parametrize("sys2", [True, False])
    def test_common_timebase(self, dt1, dt2, expected, sys1, sys2):
        """Test that common_timbase adheres to :ref:`conventions-ref`"""
        i1 = tf([1], [1, 2, 3], dt1) if sys1 else dt1
        i2 = tf([1], [1, 4, 5], dt2) if sys2 else dt2
        assert common_timebase(i1, i2) == expected
        # Make sure behaviour is symmetric
        assert common_timebase(i2, i1) == expected

    @pytest.mark.parametrize("i1, i2",
                             [(True, 0),
                              (0, 1),
                              (1, 2)])
    def test_common_timebase_errors(self, i1, i2):
        """Test that common_timbase throws errors on invalid combinations"""
        with pytest.raises(ValueError):
            common_timebase(i1, i2)
        # Make sure behaviour is symmetric
        with pytest.raises(ValueError):
            common_timebase(i2, i1)

    @pytest.mark.parametrize("dt, ref, strictref",
                             [(None, True, False),
                              (0, False, False),
                              (1, True, True),
                              (True, True, True)])
    @pytest.mark.parametrize("objfun, arg",
                             [(LTI, ()),
                              (NonlinearIOSystem, (lambda x: x, ))])
    def test_isdtime(self, objfun, arg, dt, ref, strictref):
        """Test isdtime and isctime functions to follow convention"""
        obj = objfun(*arg, dt=dt)

        assert isdtime(obj) == ref
        assert isdtime(obj, strict=True) == strictref

        if dt is not None:
            ref = not ref
            strictref = not strictref
        assert isctime(obj) == ref
        assert isctime(obj, strict=True) == strictref
