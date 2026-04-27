from flask import Flask, render_template, request, jsonify
from collections import defaultdict
import random

app = Flask(__name__)

# --------------------------------------------------
# Core Deadlock Algorithms  |  Group 15 - OS CA2
# R3E052B43, R3E052B44, R3E052B45
# --------------------------------------------------

def detect_cycles_dfs(n_proc, n_res, alloc, req):
    adj = defaultdict(list)
    for i in range(n_proc):
        for j in range(n_res):
            if req[i][j] > 0:
                adj[f"P{i}"].append(f"R{j}")
            if alloc[i][j] > 0:
                adj[f"R{j}"].append(f"P{i}")

    visited, on_stack, cycles, trace = {}, {}, [], []

    def dfs(v, path):
        visited[v] = True
        on_stack[v] = True
        path = path + [v]
        trace.append(f"Visiting {v}  |  path: {' > '.join(path)}")
        for w in adj[v]:
            if not visited.get(w):
                dfs(w, path)
            elif on_stack.get(w):
                idx = path.index(w)
                cycle = path[idx:]
                cycles.append(cycle)
                trace.append(f"*** CYCLE: {' > '.join(cycle)} > {w} ***")
        on_stack[v] = False

    all_nodes = [f"P{i}" for i in range(n_proc)] + [f"R{j}" for j in range(n_res)]
    trace.append("=== DFS Cycle Detection ===")
    for n in all_nodes:
        if not visited.get(n):
            trace.append(f"Starting from {n}")
            dfs(n, [])

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
    trace = ["=== Banker's Algorithm ===", f"Available: {work}", "Need = Max - Allocation"]
    changed = True
    while changed:
        changed = False
        for i in range(n_proc):
            if not finish[i] and all(need[i][j] <= work[j] for j in range(n_res)):
                trace.append(f"P{i}: need{need[i]} <= work{work} -> can run")
                for j in range(n_res):
                    work[j] += alloc[i][j]
                finish[i] = True
                seq.append(i)
                changed = True
                trace.append(f"  P{i} done. Work={work}")
    safe = all(finish)
    if safe:
        trace.append(f"SAFE STATE. Sequence: {' > '.join('P'+str(i) for i in seq)}")
    else:
        unsafe = [i for i in range(n_proc) if not finish[i]]
        trace.append(f"UNSAFE STATE. Cannot complete: {['P'+str(i) for i in unsafe]}")
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
    cycles, dfs_trace = detect_cycles_dfs(d["n_proc"], d["n_res"], d["alloc"], d["req"])
    deadlocked, mat_trace = resource_allocation_method(d["n_proc"], d["n_res"], d["alloc"], d["req"], d["avail"])
    return jsonify({"cycles":cycles,"deadlocked":deadlocked,"dfs_trace":dfs_trace,"mat_trace":mat_trace})


@app.route("/api/banker", methods=["POST"])
def banker():
    d = request.json
    safe, seq, trace, need = bankers_safety(d["n_proc"], d["n_res"], d["alloc"], d["max_need"], d["avail"])
    return jsonify({"safe":safe,"sequence":seq,"trace":trace,"need":need})


@app.route("/api/preset/<name>")
def preset(name):
    if name not in PRESETS:
        return jsonify({"error":"unknown preset"}), 404
    return jsonify(PRESETS[name])


@app.route("/api/randomize", methods=["POST"])
def randomize():
    d = request.json
    np_, nr = d.get("n_proc",4), d.get("n_res",3)
    alloc    = [[random.randint(0,2) for _ in range(nr)] for _ in range(np_)]
    req      = [[random.randint(0,2) for _ in range(nr)] for _ in range(np_)]
    max_need = [[alloc[i][j]+random.randint(0,2) for j in range(nr)] for i in range(np_)]
    avail    = [random.randint(0,2) for _ in range(nr)]
    return jsonify({"n_proc":np_,"n_res":nr,"alloc":alloc,"req":req,"avail":avail,"max_need":max_need})


@app.route("/api/recover", methods=["POST"])
def recover():
    d = request.json
    strategy, victim = d["strategy"], d["victim"]
    alloc, avail, nr = d["alloc"], d["avail"], d["n_res"]
    released = list(alloc[victim])
    if strategy in ("terminate","rollback"):
        for j in range(nr): avail[j] += alloc[victim][j]; alloc[victim][j] = 0
        label = "Terminated" if strategy == "terminate" else "Rolled back"
        msg = f"{label} P{victim}. Released: {released}. Available now: {avail}"
    else:
        parts = []
        for j in range(nr):
            if alloc[victim][j] > 0:
                avail[j] += alloc[victim][j]; parts.append(f"R{j}({alloc[victim][j]})"); alloc[victim][j] = 0
        msg = f"Preempted from P{victim}: {', '.join(parts) or 'nothing'}. Available: {avail}"
    return jsonify({"msg":msg,"alloc":alloc,"avail":avail})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
