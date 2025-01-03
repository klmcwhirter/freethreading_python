# Experiments on Performance of NoGIL Compile-time Option of python3.13t

The [`perfects.py`](./perfects.py) module finds [perfect numbers](https://mathworld.wolfram.com/PerfectNumber.html) from 1 up to and including some `max_n` value.

This problem is suitable for testing concurrent execution models because:

* while there is a formula for predicting where they appear - a brute force method is used by `perfects.py` to find perfect numbers. This presents as a normalizing effect on the characteristics of the execution model being tested
* the process for testing each value of `n` is independent from all other values of `n`; meaning parallelism can be maximized

[`perfects.py`](./perfects.py) supports the test goals via the following execution models selectable on the command line:

* `Single` - standard single threaded execution model
* `Processes` - multiple processes each evaluating an equally sized range of values for `n`
* `Threads` - multiple threads each evaluating an equally sized range of values for `n`

It does this by:
* simply executing the function that tests for perfect numbers for the range `1:max_n` in the `Single` case,
* using [concurrent.futures.ProcessPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor) in the `Processes` case,
* and using [concurrent.futures.ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor) in the `Threads` case.
* explicitly avoiding any shared state between the workers except for things that will not change (e.g. `ctx.worker_name(idx)`).

This makes the function that tests for perfect numbers completely reusable; eliminating any code differences due to execution model.

> NOTE: I did not bother with an *asyncio* implementation because I purposely avoided I/O as an additional testing variable. I do realize
that design decision makes the test less like *real world* scenarios. But the goal was to test concurrency in isolation from other features.
In other words, what is the significance of the NoGIL behavior and its direct effect on execution models?

### TL;DR

The effect of NoGIL on performance is not much if anything with lower values of `max_n`; and significantly worse performance with higher values.

## Command-line Options

Note that the default execution model depends on whether the GIL is disabled or not.

*If the GIL is disabled, the `Threads` execution model is the default, else the `Processes` model is the default.*

```
usage: perfects.py [-h] [-n MAX_N] [-w NUM_WORKERS] [-p] [-s] [-t] [-v]

options:
  -h, --help            show this help message and exit
  -n, --max-n MAX_N     look for perfect numbers up to and including this value (default: 1_000_000)
  -w, --num-workers NUM_WORKERS
                        number of worker processes to use (default: 12)
  -p, --processes       force use of processes instead of threads
  -s, --single-thread   force use of no parallelization
  -t, --threads         force use of threads instead of processes
  -v, --verbose         Enable verbose mode
```

## Goal of perfects_driver.sh

The goal of [`perfects_driver.sh`](./perfects_driver.sh) is to compare the validity of the results produced,
and time the actual execution component of the process of a matrix of the options.

The `-n 1_000_000` and `-w 10` options remain constant.

> Note the `-w` option is ignored when the -s option (`Single` execution model) is requested.
> That is indicated below by the use of ~~strikethrough~~.

The **lowest** and **highest** execution times in each group are indicated with **bold** typeface.

Here are the [results](./perfects_driver-py313-fed40.out) from one typical run with Python3.13 on Fedora WS 40 that is summarized below:

_I retested with Python 3.14.0a1 on Fedora 41. Here are those [results](./perfects_driver-py314a1-fed41.out)._

### Production Executable (python3.13)

| Command Line | Results | Elapsed Time |
| :-- | :--: | --: |
| **python3.13** perfects.py -n 1_000_000 -w 10 | [6, 28, 496, 8128] | **0:00:04.192254** |
| python3.13 perfects.py -n 1_000_000 -w 10 -v | [6, 28, 496, 8128] | 0:00:04.215628 |
| python3.13 perfects.py -n 1_000_000 -w 10 -p | [6, 28, 496, 8128] | 0:00:04.196177 |
| python3.13 perfects.py -n 1_000_000 -w 10 -p -v | [6, 28, 496, 8128] | 0:00:04.243090 |
| python3.13 perfects.py -n 1_000_000 ~~-w 10~~ -s | [6, 28, 496, 8128] | 0:00:19.412308 |
| python3.13 perfects.py -n 1_000_000 ~~-w 10~~ -s -v | [6, 28, 496, 8128] | 0:00:19.406344 |
| python3.13 perfects.py -n 1_000_000 -w 10 -t | [6, 28, 496, 8128] | 0:00:20.159437 |
| **python3.13** perfects.py -n 1_000_000 -w 10 -t -v | [6, 28, 496, 8128] | **0:00:20.342431** |

### Experimental Executable (python3.13t)

| Command Line | Results | Elapsed Time |
| :-- | :--: | --: |
| **python3.13t** perfects.py -n 1_000_000 -w 10 | [6, 28, 496, 8128] | **0:00:04.841594** |
| python3.13t perfects.py -n 1_000_000 -w 10 -v | [6, 28, 496, 8128] | 0:00:05.208515 |
| python3.13t perfects.py -n 1_000_000 -w 10 -p | [6, 28, 496, 8128] | 0:00:05.306935 |
| python3.13t perfects.py -n 1_000_000 -w 10 -p -v | [6, 28, 496, 8128] | 0:00:05.952637 |
| python3.13t perfects.py -n 1_000_000 ~~-w 10~~ -s | [6, 28, 496, 8128] | 0:00:25.363863 |
| **python3.13t** perfects.py -n 1_000_000 ~~-w 10~~ **-s** -v | [6, 28, 496, 8128] | **0:00:26.044659** |
| python3.13t perfects.py -n 1_000_000 -w 10 -t | [6, 28, 496, 8128] | 0:00:05.137568 |
| python3.13t perfects.py -n 1_000_000 -w 10 -t -v | [6, 28, 496, 8128] | 0:00:05.254062 |

## Results Summary

### Production Executable (python3.13)

It appears that the production executable (python3.13) with the GIL enabled is slightly more performant when using
the `Processes` execution model than the experimental executable (python3.13t) with the GIL disabled.

Also, when using the `Threads` execution model its performance is a little worse than the `Single` model.
This makes sense because the GIL is in effect and there is a little overhead associated with using a thread pool,
and multiple threads in general.

### Experimental Executable (python3.13t)

The `Threads` execution model with the experimental executable (python3.13t) is slightly less performant
than even when using the `Processes` model with python3.13 but the difference is within a reasonable margin of error.
So I am going to call those a wash.

The `Threads` execution model with python3.13t does enjoy similar performance as when using the `Processes`
execution model because it is able to use multiple cores with the NoGIL behavior. However both of these are very similar
to using the `Processes` model with python3.13.

And, as `max_n` increases (see **Appendix A** below) the performance benefits trail off significantly.

The performance of the `Single` model lags behind the production executable for some unknown reason.

In addition, the potential risks associated with execution integrity without the GIL explains why using the python3.13t
executable in production is not supported yet. And the results above do not show a compelling reason to do so.

**Recommendation:** Just stick with the `Processes` model for now while the experimentation continues.


## Appendix A - Results with `-n 33_551_000` and `-w 12`

These results were purposely (albeit selfishly, because of time commitment) trimmed down to perhaps the most interesting data points.

> As `max_n` grows in size, the experimental executable loses its performance similarity. *This is more than likely due to the overhead
associated with more aggressive context switching; resulting in additional resource contention.*

### Production Executable (python3.13)

| Command Line | Results | Elapsed Time |
| :-- | :--: | --: |
| python3.13 perfects.py -n 33_551_000 -w 12 | [6, 28, 496, 8128, 33550336] | 0:14:46.709272 |
| **python3.13** perfects.py -n 33_551_000 -w 12 -v | [6, 28, 496, 8128, 33550336] | **0:14:46.351818** |
| python3.13 perfects.py -n 33_551_000 -w 12 -p | [6, 28, 496, 8128, 33550336] | 0:14:47.447327 |
| **python3.13** perfects.py -n 33_551_000 -w 12 -p -v | [6, 28, 496, 8128, 33550336] | **0:14:49.279411** |

### Experimental Executable (python3.13t)

| Command Line | Results | Elapsed Time |
| :-- | :--: | --: |
| python3.13t perfects.py -n 33_551_000 -w 12 | [6, 28, 496, 8128, 33550336] | 0:18:21.164616 |
| python3.13t perfects.py -n 33_551_000 -w 12 -v | [6, 28, 496, 8128, 33550336] | 0:18:28.153575 |
| **python3.13t** perfects.py -n 33_551_000 -w 12 -p | [6, 28, 496, 8128, 33550336] | **0:18:02.101572** |
| python3.13t perfects.py -n 33_551_000 -w 12 -p -v | [6, 28, 496, 8128, 33550336] | 0:18:10.316738 |
| **python3.13t** perfects.py -n 33_551_000 -w 12 -t | [6, 28, 496, 8128, 33550336] | **0:18:35.191395** |
| python3.13t perfects.py -n 33_551_000 -w 12 -t -v | [6, 28, 496, 8128, 33550336] | 0:18:27.886885 |
