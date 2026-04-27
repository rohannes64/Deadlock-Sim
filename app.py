from flask import Flask, render_template, request, jsonify
from collections import defaultdict
import random

app = Flask(__name__)

# --------------------------------------------------
# Core Deadlock Algorithms  |  Group 15 - OS CA2
# R3E052B43, R3E052B44, R3E052B45
# --------------------------------------------------

def detect_cycles_dfs(n_proc, n_res, alloc, req):
    """
    Build a proper Wait-For Graph (WFG) with only P->P edges, then run DFS
    cycle detection on it.

    Pi -> Pj  iff  Pi requests at least one resource type that Pj currently holds.

    Using a WFG (instead of the raw RAG) avoids false-positive cycles in
    multi-instance resource systems: a cycle in the RAG is necessary but NOT
    sufficient for deadlock; a cycle in the WFG is the correct visual indicator
    of a circular-wait condition among processes.
    """
    # Build Wait-For edges: Pi waits for Pj if Pj holds something Pi needs
    wfg = defaultdict(list)
    for i in range(n_proc):
        for j in range(n_proc):
            if i == j:
                continue
            # Pi -> Pj if any resource type k: req[i][k]>0 and alloc[j][k]>0
            if any(req[i][k] > 0 and alloc[j][k] > 0 for k in range(n_res)):
                wfg[f"P{i}"].append(f"P{j}")

    visited, on_stack, cycles, trace = {}, {}, [], []

    def dfs(v, path):
        visited[v] = True
        on_stack[v] = True
        path = path + [v]
        trace.append(f"Visiting {v}  |  path: {' > '.join(path)}")
        for w in wfg[v]:
            if not visited.get(w):
                dfs(w, path)
            elif on_stack.get(w):
                idx = path.index(w)
                cycle = path[idx:]
                cycles.append(cycle)
                trace.append(f"*** CYCLE: {' > '.join(cycle)} > {w} ***")
        on_stack[v] = False

    trace.append("=== DFS Cycle Detection (Wait-For Graph) ===")
    for i in range(n_proc):
        node = f"P{i}"
        if not visited.get(node):
            trace.append(f"Starting from {node}")
            dfs(node, [])

    seen, unique = set(), []
    for c in cycles:
        k = tuple(sorted(c))
        if k not in seen:
            seen.add(k)
            unique.append(c)
    return unique, trace


def resource_allocation_method(n_proc, n_res, alloc, req, avail):
    work = list(avail)
    finish = [False] * n_proc
    trace = ["=== Resource Allocation Matrix Method ===", f"Initial Available: {work}"]
    changed = True
    while changed:
        changed = False
        for i in range(n_proc):
            if not finish[i]:
                if all(req[i][j] <= work[j] for j in range(n_res)):
                    trace.append(f"P{i} can complete -> releasing {alloc[i]}")
                    for j in range(n_res):
                        work[j] += alloc[i][j]
                    finish[i] = True
                    changed = True
                    trace.append(f"  Available now: {work}")
    deadlocked = [i for i in range(n_proc) if not finish[i]]
    if deadlocked:
        trace.append(f"DEADLOCKED: {['P'+str(i) for i in deadlocked]}")
    else:
        trace.append("No deadlock. All processes can complete.")
    return deadlocked, trace


def bankers_safety(n_proc, n_res, alloc, max_need, avail):
    need = [[max(0, max_need[i][j] - alloc[i][j]) for j in range(n_res)] for i in range(n_proc)]
    work, finish, seq = list(avail), [False]*n_proc, []
    trace = [
        "=== Banker's Algorithm ===",
        f"Available: {work}",
        "Need matrix (Max - Allocation):",
    ]
    for i in range(n_proc):
        trace.append(f"  P{i}: need={need[i]}, alloc={alloc[i]}, max={max_need[i]}")
    trace.append("--- Safety check ---")

    changed = True
    while changed:
        changed = False
        for i in range(n_proc):
            if not finish[i] and all(need[i][j] <= work[j] for j in range(n_res)):
                trace.append(
                    f"P{i}: need{need[i]} <= work{work} -> GRANT resources, run to completion"
                )
                for j in range(n_res):
                    work[j] += alloc[i][j]
                finish[i] = True
                seq.append(i)
                changed = True
                trace.append(
                    f"  P{i} completes & releases alloc{alloc[i]} -> work now {work}"
                )
    safe = all(finish)
    if safe:
        seq_str = ' -> '.join('P'+str(i) for i in seq)
        trace.append(f"SAFE STATE. Safe execution sequence: {seq_str}")
        trace.append(
            "Each process in this sequence can acquire all needed resources, "
            "run to completion, and release them for the next."
        )
    else:
        unsafe = [i for i in range(n_proc) if not finish[i]]
        trace.append(f"UNSAFE STATE. Cannot complete: {['P'+str(i) for i in unsafe]}")
        trace.append(
            "No safe sequence exists — granting further requests risks deadlock."
        )
    return safe, seq, trace, need


PRESETS = {
    "circular3": {"n_proc":3,"n_res":3,
        "alloc":[[1,0,0],[0,1,0],[0,0,1]],"req":[[0,1,0],[0,0,1],[1,0,0]],
        "avail":[0,0,0],"max_need":[[2,1,1],[1,2,1],[1,1,2]]},
    "circular2": {"n_proc":2,"n_res":2,
        "alloc":[[1,0],[0,1]],"req":[[0,1],[1,0]],
        "avail":[0,0],"max_need":[[1,1],[1,1]]},
    "partial": {"n_proc":4,"n_res":3,
        "alloc":[[1,0,0],[0,1,0],[0,0,1],[0,0,0]],"req":[[0,1,0],[0,0,1],[1,0,0],[0,0,1]],
        "avail":[1,0,0],"max_need":[[2,1,0],[1,2,1],[1,0,2],[1,1,2]]},
    "safe": {"n_proc":4,"n_res":3,
        "alloc":[[0,1,0],[2,0,0],[3,0,2],[2,1,1]],"req":[[0,0,0],[2,0,2],[0,0,0],[1,0,0]],
        "avail":[3,3,2],"max_need":[[7,5,3],[3,2,2],[9,0,2],[2,2,2]]}
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/detect", methods=["POST"])
def detect():
    d = request.json
    # DFS builds the Wait-For graph for visual representation only.
    # It is NOT authoritative for deadlock in multi-instance systems.
    wait_for_cycles, dfs_trace = detect_cycles_dfs(d["n_proc"], d["n_res"], d["alloc"], d["req"])

    # Matrix Method is the sole authority: a process is deadlocked iff it
    # cannot finish even after all other completable processes release resources.
    deadlocked, mat_trace = resource_allocation_method(d["n_proc"], d["n_res"], d["alloc"], d["req"], d["avail"])

    return jsonify({
        # Primary deadlock authority — use this for all highlighting & status.
        "deadlocked": deadlocked,
        "deadlock_confirmed": len(deadlocked) > 0,
        # Secondary visual aid — shows Wait-For graph cycles, NOT deadlock truth.
        "wait_for_cycles": wait_for_cycles,
        # Keep legacy "cycles" key so existing callers don't break, but it now
        # mirrors wait_for_cycles and must never drive the deadlock decision.
        "cycles": wait_for_cycles,
        "dfs_trace": dfs_trace,
        "mat_trace": mat_trace,
    })


@app.route("/api/banker", methods=["POST"])
def banker():
    d = request.json
    safe, seq, trace, need = bankers_safety(d["n_proc"], d["n_res"], d["alloc"], d["max_need"], d["avail"])
    # Expose unsafe processes so the frontend can sync state.deadlocked if desired.
    unsafe_procs = [i for i in range(d["n_proc"]) if i not in seq] if not safe else []
    return jsonify({
        "safe": safe,
        "sequence": seq,
        "trace": trace,
        "need": need,
        # Mirrors detect endpoint contract so the frontend can unify state.
        "deadlock_confirmed": not safe,
        "unsafe_procs": unsafe_procs,
    })


@app.route("/api/preset/<name>")
def preset(n):
    if n not in PRESETS:
        return jsonify({"error":"unknown preset"}), 404
    return jsonify(PRESETS[n])


@app.route("/api/randomize", methods=["POST"])
def randomize():
    d = request.json
    np_, nr = d.get("n_proc", 4), d.get("n_res", 3)

    # Allocation: each process holds 0-2 units of each resource
    alloc = [[random.randint(0, 2) for _ in range(nr)] for _ in range(np_)]

    # Available: 0-3 units of each resource type free
    avail = [random.randint(0, 3) for _ in range(nr)]

    # Max need must be >= alloc and at least 1 unit more for at least one resource
    # so that need = max - alloc > 0 (otherwise the process is trivially done)
    max_need = []
    for i in range(np_):
        row = list(alloc[i])
        # Ensure at least one resource has additional need
        bump_idx = random.randint(0, nr - 1)
        for j in range(nr):
            extra = random.randint(0, 2)
            if j == bump_idx and extra == 0:
                extra = 1          # guarantee at least one non-zero need
            row[j] = alloc[i][j] + extra
        max_need.append(row)

    # Request: what each process is currently asking for.
    # Constrain req[i][j] <= max_need[i][j] - alloc[i][j]  (can't request beyond declared max)
    # and req[i][j] is at most what's plausibly available so scenarios aren't always hopeless.
    req = []
    for i in range(np_):
        row = []
        for j in range(nr):
            need_ij = max_need[i][j] - alloc[i][j]   # guaranteed >= 0
            row.append(random.randint(0, need_ij))
        req.append(row)

    return jsonify({
        "n_proc": np_, "n_res": nr,
        "alloc": alloc, "req": req,
        "avail": avail, "max_need": max_need
    })


@app.route("/api/recover", methods=["POST"])
def recover():
    d = request.json
    strategy, victim = d["strategy"], d["victim"]
    alloc, avail, nr = d["alloc"], d["avail"], d["n_res"]
    req = d["req"]  # must be included in payload and zeroed on recovery
    released = list(alloc[victim])
    if strategy in ("terminate", "rollback"):
        for j in range(nr):
            avail[j] += alloc[victim][j]
            alloc[victim][j] = 0
            req[victim][j] = 0          # process is gone / rolled back — clear its requests
        label = "Terminated" if strategy == "terminate" else "Rolled back"
        msg = f"{label} P{victim}. Released: {released}. Available now: {avail}"
    else:
        # Preempt: seize all held resources, but process stays alive — clear alloc only
        parts = []
        for j in range(nr):
            if alloc[victim][j] > 0:
                avail[j] += alloc[victim][j]
                parts.append(f"R{j}({alloc[victim][j]})")
                alloc[victim][j] = 0
                req[victim][j] = 0      # process must re-request after preemption
        msg = f"Preempted from P{victim}: {', '.join(parts) or 'nothing'}. Available: {avail}"
    return jsonify({"msg": msg, "alloc": alloc, "req": req, "avail": avail})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
