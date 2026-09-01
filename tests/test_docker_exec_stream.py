"""Closing docker exec streams.

An unclosed stream's urllib3 response is finalized by the garbage collector, which
reports `ValueError: I/O operation on closed file` from inside __del__ and leaves the
socket open until then.
"""

from swebench.harness.docker_utils import _close_exec_stream


class _Closeable:
    def __init__(self, raises=False):
        self.closed = False
        self._raises = raises

    def close(self):
        if self._raises:
            raise ValueError("I/O operation on closed file")
        self.closed = True


class _Stream(_Closeable):
    def __init__(self, response=None, raises=False):
        super().__init__(raises=raises)
        self._response = response


def test_closes_stream_and_response():
    response = _Closeable()
    stream = _Stream(response)
    _close_exec_stream(stream)
    assert stream.closed and response.closed


def test_none_is_a_noop():
    _close_exec_stream(None)  # a timeout before exec_start leaves it unset


def test_a_raising_stream_still_closes_the_response():
    # CancellableStream.close() reaches into _fp.fp and throws when already closed;
    # the response underneath is the one whose finalizer produces the noise.
    response = _Closeable()
    _close_exec_stream(_Stream(response, raises=True))
    assert response.closed


def test_a_raising_response_is_swallowed():
    stream = _Stream(_Closeable(raises=True))
    _close_exec_stream(stream)
    assert stream.closed


def test_stream_without_a_response_attribute():
    stream = _Closeable()
    _close_exec_stream(stream)
    assert stream.closed


def test_double_close_is_safe():
    response = _Closeable()
    stream = _Stream(response)
    _close_exec_stream(stream)
    _close_exec_stream(stream)  # reader thread and timeout path can both call it
    assert stream.closed and response.closed
