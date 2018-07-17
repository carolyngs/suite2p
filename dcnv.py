import numpy as np
from joblib import Parallel, delayed
import multiprocessing
from scipy.ndimage import filters

def oasis1t(F, ops):
    ca = F    
    NT = F.shape[0]
    
    v = np.zeros((NT,))
    w = np.zeros((NT,))
    t = np.zeros((NT,), dtype=int)
    l = np.zeros((NT,))
    s = np.zeros((NT,))

    g = -1./(ops['tau'] * ops['fs'])

    for i in range(0,10):
        it = 0
        ip = 0

        while it<NT:    
            v[ip], w[ip],t[ip],l[ip] = ca[it],1,it,1    

            while ip>0:
                if v[ip-1] * np.exp(g * l[ip-1]) > v[ip]:
                    # violation of the constraint means merging pools
                    f1 = np.exp(g * l[ip-1])
                    f2 = np.exp(2 * g * l[ip-1])
                    wnew = w[ip-1] + w[ip] * f2
                    v[ip-1] = (v[ip-1] * w[ip-1] + v[ip] * w[ip]* f1) / wnew
                    w[ip-1] = wnew
                    l[ip-1] += l[ip]

                    ip += -1
                else:
                    break    
            it += 1
            ip += 1

        s[t[1:ip]] = v[1:ip] - v[:ip-1] * np.exp(g * l[:ip-1])
        
        return s

def oasis(F, ops):
    num_cores = multiprocessing.cpu_count()

    F = preprocess(F,ops)
    
    inputs = range(F.shape[0])

    results = Parallel(n_jobs=num_cores)(delayed(oasis1t)(F[i, :], ops) for i in inputs)
    
    # collect results as numpy array
    sp = np.zeros_like(F)
    for i in inputs:
        sp[i,:] = results[i]
        
    return sp


def preprocess(F,ops):
    sig = 3.
    #Flow = filters.percentile_filter(Flow,    5, int(ops['win']*ops['fs']))
    Flow = filters.gaussian_filter(F,    sig)
    Flow = filters.minimum_filter1d(Flow,    int(ops['win']*ops['fs']))
    Flow = filters.maximum_filter1d(Flow,    int(ops['win']*ops['fs']))
    F = F - Flow
    return F