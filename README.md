# Desbordante benchmark runner

Run a benchmark on the headless machine and copy its JSON report to the machine
that has matplotlib.  Each invocation benchmarks exactly one algorithm.

```bash
# Timing benchmark (the first two, smallest Iowa data sets)
desbordante-benchmark-runner timed \
  --test-suite iowas-low-arities --algorithm fd-pac --test-count 2 \
  --output timed-report.json

# Memory benchmark
desbordante-benchmark-runner memory \
  --test-suite iowas-low-arities --algorithm fd-pac --test-count 2 \
  --output memory-report.json

# On the plotting machine (opens the figure)
desbordante-benchmark-runner plot --input timed-report.json

# Or save it instead
desbordante-benchmark-runner plot --input timed-report.json --output timed.pdf
desbordante-benchmark-runner plot --input memory-report.json --output memory.pdf
```

Reports are JSON dumps of `list[Stats]`.  They retain the measurements used for
the plots as well as the calculated normality-test p-values, mean, standard
deviation, 95% confidence-interval half-width, and an IQR outlier decision.
