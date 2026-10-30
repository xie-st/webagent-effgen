"""Small DAG scheduler: isolated node inputs, scoped locks, verified merges."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from copy import deepcopy
from dataclasses import dataclass
import threading
import time


class ScopeLock:
    """Readers may overlap; any write excludes reads/writes of that account."""
    def __init__(self):
        self.condition = threading.Condition()
        self.readers, self.writer, self.waiting = 0, False, 0

    def acquire(self, write, context):
        with self.condition:
            self.waiting += int(write)
            try:
                while self.writer or (self.readers if write else self.waiting):
                    context.check()
                    self.condition.wait(0.05)
                context.check()
                if write:
                    self.writer = True
                else:
                    self.readers += 1
            finally:
                self.waiting -= int(write)

    def release(self, write):
        with self.condition:
            if write:
                self.writer = False
            else:
                self.readers -= 1
            self.condition.notify_all()


@dataclass(frozen=True)
class NodeResult:
    value: object
    verified: bool


@dataclass(frozen=True)
class Node:
    name: str
    run: object
    deps: tuple[str, ...] = ()
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    readonly: bool = True
    scope: str = "default-account"


@dataclass
class NodeContext:
    inputs: dict
    cancelled: threading.Event
    deadline: float
    version: int

    def check(self):
        if self.cancelled.is_set():
            raise RuntimeError("Node cancelled")
        if time.time() >= self.deadline:
            raise TimeoutError("Node deadline reached")


class Scheduler:
    def __init__(self, nodes, *, workers=3, pause_requested=None):
        items = list(nodes)
        self.nodes = {n.name: n for n in items}
        if len(items) != len(self.nodes) or workers < 1:
            raise ValueError("Unique node names and positive workers required")
        self.workers, self.lock = workers, threading.Lock()
        self.pause_requested = pause_requested or (lambda: False)
        self.events, self.results = [], {}
        self.status = {name: "pending" for name in self.nodes}
        self.cancelled = {name: threading.Event() for name in self.nodes}
        self.versions = {name: 0 for name in self.nodes}
        self.resources = {}
        self.scopes = {n.scope: ScopeLock() for n in items}
        self._validate()

    def _validate(self):
        seen, active = set(), set()
        def visit(name):
            if name not in self.nodes or name in active:
                raise ValueError("Unknown dependency or dependency cycle")
            if name in seen:
                return
            active.add(name)
            for dep in self.nodes[name].deps:
                visit(dep)
            active.remove(name)
            seen.add(name)
        for name, node in self.nodes.items():
            visit(name)
            if node.readonly and node.writes:
                raise ValueError("A read-only node cannot declare writes")
            for key in self._keys(node):
                self.resources.setdefault(key, ScopeLock())

    def _keys(self, node):
        keys = set(node.reads) | set(node.writes)
        return sorted(keys)

    def cancel(self, name):
        with self.lock:
            self.cancelled[name].set()
            self.versions[name] += 1
            if self.status[name] in {"pending", "running"}:
                self.status[name] = "cancelled"

    def _execute(self, node, context):
        acquired = []
        scope = self.scopes[node.scope]
        scope.acquire(not node.readonly, context)
        try:
            for key in self._keys(node):
                write = key in node.writes
                self.resources[key].acquire(write, context)
                acquired.append((self.resources[key], write))
            while self.pause_requested():
                context.check()
                time.sleep(0.05)
            context.check()
            result = node.run(context)
            context.check()
            if not isinstance(result, NodeResult):
                raise TypeError("Node must return an explicitly verified NodeResult")
            return result
        finally:
            for resource, write in reversed(acquired):
                resource.release(write)
            scope.release(not node.readonly)

    def run(self, *, deadline):
        futures = {}
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            while True:
                with self.lock:
                    if time.time() >= deadline:
                        for name in self.nodes:
                            self.cancelled[name].set()
                            self.versions[name] += 1
                            if self.status[name] in {"pending", "running"}:
                                self.status[name] = "cancelled"
                    for name, node in self.nodes.items():
                        if self.status[name] != "pending":
                            continue
                        dependencies = [self.status[d] for d in node.deps]
                        if any(s in {"failed", "cancelled", "blocked"} for s in dependencies):
                            self.status[name] = "blocked"
                        elif all(s == "verified" for s in dependencies) and not self.pause_requested():
                            context = NodeContext(deepcopy({d: self.results[d] for d in node.deps}),
                                                  self.cancelled[name], deadline, self.versions[name])
                            self.status[name] = "running"
                            futures[pool.submit(self._execute, node, context)] = (name, context.version)
                    pending = any(s == "pending" for s in self.status.values())
                if not futures and not pending:
                    break
                if not futures:
                    time.sleep(0.05)
                    continue
                done, _ = wait(futures, timeout=0.05, return_when=FIRST_COMPLETED)
                for future in done:
                    name, version = futures.pop(future)
                    try:
                        result, error = future.result(), None
                    except Exception as exc:
                        result, error = None, type(exc).__name__
                    with self.lock:
                        if version != self.versions[name] or self.cancelled[name].is_set():
                            self.events.append({"node": name, "event": "late_result_discarded"})
                            continue
                        if result is not None and result.verified:
                            self.results[name] = deepcopy(result.value)
                            self.status[name] = "verified"
                        else:
                            self.status[name] = "failed"
                        self.events.append({"node": name, "status": self.status[name], "error": error})
        return {"status": dict(self.status), "results": deepcopy(self.results), "events": list(self.events)}
