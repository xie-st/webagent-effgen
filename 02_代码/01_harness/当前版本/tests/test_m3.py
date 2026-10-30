import threading
import time
import unittest
from web_agent.scheduler import Node, NodeResult, Scheduler
from web_agent.adapters.browser import SiteLimiter, Interrupted


class SchedulerTests(unittest.TestCase):
    def test_cycle_rejected_before_work(self):
        with self.assertRaises(ValueError):
            Scheduler([Node("a", None, ("b",)), Node("b", None, ("a",))])

    def test_parallel_reads_and_verified_dependencies(self):
        barrier = threading.Barrier(2)
        def read(ctx):
            barrier.wait(timeout=2)
            return NodeResult("read", True)
        def merge(ctx):
            self.assertEqual(ctx.inputs, {"a": "read", "b": "read"})
            ctx.inputs["a"] = "local-only"
            return NodeResult("merged", True)
        scheduler = Scheduler([Node("a", read), Node("b", read), Node("c", merge, ("a", "b"))])
        result = scheduler.run(deadline=time.time() + 5)
        self.assertEqual(set(result["status"].values()), {"verified"})
        self.assertEqual(result["results"]["a"], "read")

    def test_reads_of_same_resource_can_overlap(self):
        barrier = threading.Barrier(2)
        def read(ctx):
            barrier.wait(timeout=2)
            return NodeResult('read',True)
        result=Scheduler([Node('a',read,reads=('catalog',)),Node('b',read,reads=('catalog',))],workers=2).run(deadline=time.time()+3)
        self.assertEqual(set(result['status'].values()),{'verified'})

    def test_initial_pause_prevents_dispatch_until_resumed(self):
        paused=threading.Event(); paused.set()
        entered=threading.Event()
        def run(ctx):
            entered.set()
            return NodeResult('ok',True)
        def resume():
            time.sleep(.12)
            self.assertFalse(entered.is_set())
            paused.clear()
        controller=threading.Thread(target=resume); controller.start()
        result=Scheduler([Node('a',run)],pause_requested=paused.is_set).run(deadline=time.time()+3)
        controller.join()
        self.assertEqual(result['status']['a'],'verified')

    def test_failure_blocks_only_related_successors(self):
        bad = lambda c: NodeResult(None, False)
        good = lambda c: NodeResult("ok", True)
        result = Scheduler([Node("a", bad), Node("b", good, ("a",)),
                            Node("c", good)]).run(deadline=time.time() + 5)
        self.assertEqual(result["status"], {"a": "failed", "b": "blocked", "c": "verified"})

    def test_shared_write_lock_covers_confirmation(self):
        active, maximum, lock = [0], [0], threading.Lock()
        def write(ctx):
            with lock:
                active[0] += 1
                maximum[0] = max(maximum[0], active[0])
            time.sleep(0.05)  # includes simulated read-modify-confirm interval
            with lock:
                active[0] -= 1
            return NodeResult("confirmed", True)
        result = Scheduler([Node("a", write, writes=("cart",), readonly=False),
                            Node("b", write, writes=("cart",), readonly=False)]).run(deadline=time.time() + 5)
        self.assertEqual(maximum[0], 1)
        self.assertEqual(set(result["status"].values()), {"verified"})

    def test_cancelled_late_result_is_not_merged(self):
        started = threading.Event()
        def slow(ctx):
            started.set()
            time.sleep(0.1)
            return NodeResult("late", True)
        scheduler = Scheduler([Node("a", slow), Node("b", slow, ("a",))])
        thread = threading.Thread(target=lambda: (started.wait(), scheduler.cancel("a")))
        thread.start()
        result = scheduler.run(deadline=time.time() + 5)
        thread.join()
        self.assertEqual(result["status"], {"a": "cancelled", "b": "blocked"})
        self.assertEqual(result["results"], {})
        self.assertTrue(any(e.get("event") == "late_result_discarded" for e in result["events"]))

    def test_limiter_wait_is_deadline_and_takeover_aware(self):
        limiter = SiteLimiter()
        limiter.defer("site", "0.1")
        with self.assertRaises(Interrupted):
            limiter.wait("site", time.time() + 1, lambda: True)
        with self.assertRaises(TimeoutError):
            limiter.wait("site", time.time() - 1, lambda: False)


if __name__ == "__main__":
    unittest.main()
