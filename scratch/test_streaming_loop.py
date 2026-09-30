import numpy as np
from numba import njit, prange
import time

@njit(parallel=True)
def test_parallel_streaming(n_spans, n_crs, n_trs, n_te, n_oh, n_ple, n_pte, n_cfg):
    total = n_spans * n_crs * n_trs * n_te * n_oh * n_ple * n_pte * n_cfg
    acc = 0.0
    for i in prange(n_spans):
        local_acc = 0.0
        for j in range(n_crs):
            for k in range(n_trs):
                for l in range(n_te):
                    for m in range(n_oh):
                        for p in range(n_ple):
                            for q in range(n_pte):
                                for r in range(n_cfg):
                                    local_acc += (i + j + k + l + m + p + q + r) * 0.001
        acc += local_acc
    return acc, total

t0 = time.time()
# Warmup
test_parallel_streaming(2, 2, 2, 2, 2, 2, 2, 2)
t1 = time.time()
print(f"Compilation time: {t1 - t0:.3f} s")

t0 = time.time()
acc, total = test_parallel_streaming(33, 16, 7, 8, 5, 11, 7, 6)
t1 = time.time()
print(f"Evaluated {total:,} loops in {t1 - t0:.3f} s! Throughput: {total / (t1 - t0):,.0f} it/s")
