"""Independent reference solutions for evaluator guard tests, never model input."""
import copy
import math
import threading


def integer(value, minimum):
    return type(value) is int and value >= minimum


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


class Ledger:
    def __init__(self, balances):
        if not isinstance(balances, dict) or any(
                not isinstance(k, str) or not k or not integer(v, 0)
                for k, v in balances.items()):
            raise ValueError("invalid balances")
        self.balances = dict(balances)
        self.history = {}

    def snapshot(self):
        return dict(self.balances)

    def apply(self, operations):
        if not isinstance(operations, list):
            raise ValueError("operations must be list")  # noqa: TRY004 - task contract requires ValueError
        balances, history, result = dict(self.balances), dict(self.history), []
        for item in operations:
            if not isinstance(item, dict) or set(item) != {"id", "source", "target", "amount"}:
                raise ValueError("invalid operation")
            id, source, target, amount = (item[k] for k in ("id", "source", "target", "amount"))
            if (not isinstance(id, str) or not id or not isinstance(source, str)
                    or not isinstance(target, str) or source not in balances
                    or target not in balances or source == target or not integer(amount, 1)):
                raise ValueError("invalid operation values")
            values = (source, target, amount)
            if id in history:
                if history[id] != values:
                    raise ValueError("conflicting id")
                result.append(False)
                continue
            if balances[source] < amount:
                raise ValueError("insufficient funds")
            balances[source] -= amount
            balances[target] += amount
            history[id] = values
            result.append(True)
        self.balances, self.history = balances, history
        return result


class Limiter:
    def __init__(self, limits, window, clock):
        if (not isinstance(limits, dict) or not limits or any(
                not isinstance(k, str) or not k or not integer(v, 1)
                for k, v in limits.items()) or not number(window)
                or window <= 0 or not callable(clock)):
            raise ValueError("invalid configuration")
        self.limits, self.window, self.clock = dict(limits), window, clock
        self.last, self.events, self.lock = None, {k: [] for k in limits}, threading.Lock()

    def acquire(self, request):
        with self.lock:
            if (not isinstance(request, dict) or not request or any(
                    k not in self.limits or not integer(v, 1) or v > self.limits[k]
                    for k, v in request.items())):
                raise ValueError("invalid request")
            now = self.clock()
            if not number(now) or (self.last is not None and now < self.last):
                raise ValueError("invalid clock")
            events = {k: [event for event in values if event[0] > now - self.window]
                      for k, values in self.events.items()}
            allowed = all(sum(v for _, v in events[k]) + weight <= self.limits[k]
                          for k, weight in request.items())
            if allowed:
                for key, weight in request.items():
                    events[key].append([now, weight])
            self.last, self.events = now, events
            return allowed

    def snapshot(self):
        with self.lock:
            return copy.deepcopy({"last": self.last, "events": self.events})

    def restore(self, state):
        with self.lock:
            try:
                if (not isinstance(state, dict) or set(state) != {"last", "events"}
                        or not isinstance(state["events"], dict)
                        or set(state["events"]) != set(self.limits)):
                    raise ValueError("invalid state")
                last, events = state["last"], copy.deepcopy(state["events"])
                if last is not None and not number(last):
                    raise ValueError("invalid last")
                for key, values in events.items():
                    if not isinstance(values, list):
                        raise ValueError("invalid event list")  # noqa: TRY004 - explicit task contract
                    previous, total = None, 0
                    for pair in values:
                        if not isinstance(pair, list) or len(pair) != 2:
                            raise ValueError("invalid event")
                        stamp, weight = pair
                        if (last is None or not number(stamp) or not integer(weight, 1)
                                or not last - self.window < stamp <= last
                                or (previous is not None and stamp < previous)):
                            raise ValueError("invalid event value")
                        previous, total = stamp, total + weight
                    if total > self.limits[key]:
                        raise ValueError("over capacity")
            except (TypeError, KeyError, OverflowError) as error:
                raise ValueError("invalid state") from error
            self.last, self.events = last, events
