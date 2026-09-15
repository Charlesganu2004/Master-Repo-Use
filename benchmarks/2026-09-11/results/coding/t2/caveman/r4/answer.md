All 7 pass.

**Why deque:** deque per key give O(1) append/popleft, so expiring old timestamps from front cost nothing extra per call. Single lock around whole read-check-write section make check-then-act atomic across threads, avoid race where two threads both see room and both insert. `defaultdict` keep memory small since each key's own deque prune itself on every call, no need for background sweep thread.

**Edge cases not handled:**
- Memory: keys never accessed again keep empty-ish deque entry in dict forever (no eviction of dead keys).
- Clock going backward (non-monotonic custom clock) could make cutoff math wrong, let stale entries linger or wrongly evict.
- Lock is global across all keys, so under many distinct keys, contention serialize unrelated callers (no per-key locking or sharding).
- No async support, only for use with `threading`, blocking `allow` call hold lock while pruning deque, could stall other keys briefly under very deep deques.