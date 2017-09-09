import time

ts = []

t = 0.06
iters = 1000
for i in range(iters):
    ts.append(time.time())
    time.sleep(t)

l = []
for i, _ in enumerate(ts):
    if i == 0:
        continue
    l.append(ts[i] - ts[i - 1])

d = {
    'less': 0,
    5: 0,
    3: 0,
    1: 0,
    'half': 0
}
for x in l:
    if x < t:
        d['less'] = d['less'] + 1
    if x > (1.05 * t):
        d[5] = d[5] + 1
    if x > (1.03 * t):
        d[3] = d[3] + 1
    if x > (1.01 * t):
        d[1] = d[1] + 1
    if x > (1.005 * t):
        d['half'] = d['half'] + 1

print('Out of {}'.format(iters), d)
