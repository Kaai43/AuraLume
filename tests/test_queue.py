import random

from auralume.queue import PlayQueue


def test_empty_and_end_stop_without_wrapping():
    queue = PlayQueue()
    assert queue.next() is None
    queue.set(['a', 'b'], 'a')
    assert queue.current == 'a'
    assert queue.next() == 'b'
    assert queue.next() is None
    assert queue.previous() == 'a'


def test_repeat_one_only_on_automatic_advance_and_repeat_all_wraps():
    queue = PlayQueue()
    queue.set(['a', 'b'], 'a')
    queue.repeat = 'one'
    assert queue.next(automatic=True) == 'a'
    assert queue.next() == 'b'
    queue.repeat = 'all'
    assert queue.next() == 'a'


def test_shuffle_visits_every_track_before_repeat_and_previous_retraces():
    queue = PlayQueue(rng=random.Random(4))
    queue.set(['a', 'b', 'c', 'd'], 'a')
    queue.shuffle = True
    seen = [queue.current, queue.next(), queue.next(), queue.next()]
    assert set(seen) == {'a', 'b', 'c', 'd'}
    assert queue.next() is None
    assert queue.previous() == seen[-2]


def test_enqueue_into_empty_queue_is_playable():
    queue = PlayQueue()
    queue.enqueue('a')
    assert queue.current == 'a'
    queue.enqueue('b')
    assert queue.next() == 'b'
