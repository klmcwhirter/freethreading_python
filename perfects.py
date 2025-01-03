#!/usr/bin/python3.13
'''
Calculate perfect numbers up to max_n using threads or processes.

Also has support for /usr/bin/python3.13t - NoGIL
'''

import argparse
import concurrent.futures
import logging
import multiprocessing as mp
import os
import sys
import sysconfig
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum, auto
from functools import reduce
from typing import Generator


class ExecutionMode(StrEnum):
    Single = auto()
    Processes = auto()
    Threads = auto()


MODE_2_WORKER_NAME = {
    ExecutionMode.Processes: 'Worker',
    ExecutionMode.Single: '',
    ExecutionMode.Threads: 'Thread'
}


@dataclass
class AppContext:
    mode: ExecutionMode = field(init=False)

    max_n: int = 1_000_000  # 34_000_000 -> 33_550_336

    # see https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor
    # see https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
    num_workers: int = min(12, os.process_cpu_count() or 1)

    verbose: bool = False

    def __post_init__(self):
        self.mode = ExecutionMode.Threads if self.gil_disabled else ExecutionMode.Processes

    @property
    def executor_cls(self) -> concurrent.futures.Executor:

        return concurrent.futures.ThreadPoolExecutor if self.mode == ExecutionMode.Threads \
            else concurrent.futures.ProcessPoolExecutor if self.mode == ExecutionMode.Processes \
            else concurrent.futures.Executor  # fallback to abstract class

    @property
    def gil_config(self) -> int | None:
        return sysconfig.get_config_vars().get('Py_GIL_DISABLED')

    @property
    def gil_disabled(self) -> int:
        return self.gil_config is not None and self.gil_config == 1

    def log_exec_ctx(self) -> None:
        logging.debug(f'{sys.version=}')

        self.log_gil_availability()

        logging.debug(self)

    def log_gil_availability(self) -> None:
        if self.gil_config is None:
            msg = 'GIL cannot be disabled'
        elif self.gil_config == 0:
            msg = 'GIL is active'
        elif self.gil_config == 1:
            msg = 'GIL is disabled'

        logging.debug(msg)

    def set_from_args(self, args: argparse.Namespace) -> None:
        # print(args)
        self.max_n = args.max_n
        self.num_workers = args.num_workers

        self.mode = ExecutionMode.Single if args.single_thread \
            else ExecutionMode.Processes if args.processes \
            else ExecutionMode.Threads if args.threads \
            else self.mode

        self.verbose = args.verbose

    def setup_logging(self) -> None:
        log_level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(level=log_level, format='{asctime} - {module} - {funcName} - {levelname} - {message}', style='{')

    def worker_name(self, idx=0) -> str:
        prefix = MODE_2_WORKER_NAME[self.mode]
        rc = f'{prefix}-{idx}' if self.mode != ExecutionMode.Single else prefix
        return rc


@contextmanager
def parse_args() -> Generator[AppContext, None, None]:
    '''parses cli args and returns app context'''

    ctx = AppContext()

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--max-n', type=int, default=ctx.max_n,
                        help=f'look for perfect numbers up to and including this value (default: {ctx.max_n:_})')
    parser.add_argument('-w', '--num-workers', type=int, default=ctx.num_workers,
                        help=f'number of worker processes to use (default: {ctx.num_workers})')
    parser.add_argument('-p', '--processes', default=False, action='store_true',
                        help=f'force use of processes instead of threads')
    parser.add_argument('-s', '--single-thread', default=False, action='store_true',
                        help=f'force use of no parallelization')
    parser.add_argument('-t', '--threads', default=False, action='store_true',
                        help=f'force use of threads instead of processes')
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='Enable verbose mode')

    args = parser.parse_args()
    ctx.set_from_args(args)

    ctx.setup_logging()
    ctx.log_exec_ctx()

    yield ctx


def find_perfect_numbers_range(rng: tuple[int], idx: int, ctx: AppContext) -> list[int]:
    '''worker function that finds perfect numbers within a range of values for n'''

    def _is_perfect_number(n: int) -> bool:
        '''Determines if n is a perfect number.'''

        def _factors(n: int) -> set[int]:
            '''Returns set of unique factors of n'''

            return set(reduce(
                list.__add__,
                ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0),
                []
            ))

        return n == sum(f for f in _factors(n) if n != f)

    logging.debug(f'{ctx.worker_name(idx=idx)} processing ({rng[0]:_}, {rng[-1]:_})')

    rc = [i for i in range(rng[0], rng[-1]+1) if _is_perfect_number(i)]

    return rc


def find_perfect_numbers(ctx: AppContext) -> list[int]:
    '''Orchestrates the process for finding perfect numbers'''

    if ctx.mode == ExecutionMode.Single:
        return find_perfect_numbers_range(rng=(1, ctx.max_n), idx=0, ctx=ctx)

    results = set[int]()

    with ctx.executor_cls(max_workers=ctx.num_workers, initializer=ctx.setup_logging) as executor:
        '''Use executor to parallelize the process of finding perfect numbers'''

        def _number_ranges(max_n: int, num_workers: int) -> list[tuple[int, int]]:
            '''Distribute work evenly across all workers; returns list of begin/end number ranges'''

            windows = [(0, 0)] * num_workers

            items_per_worker = int(max_n // num_workers) + 1

            last_idx = 1
            for t in range(num_workers):
                next_idx = min(max_n, last_idx + items_per_worker)

                windows[t] = (last_idx, next_idx)

                if next_idx >= max_n:
                    break

                last_idx = next_idx + 1

            return windows

        futures = {
            executor.submit(find_perfect_numbers_range, rng=rng, idx=idx, ctx=ctx): idx
            for idx, rng in enumerate(_number_ranges(ctx.max_n, ctx.num_workers))
        }

        for future in concurrent.futures.as_completed(futures):
            idx = futures[future]
            result = future.result()

            if result and len(result) > 0:
                logging.debug(f'Adding result from {ctx.worker_name(idx=idx)}')
                results.update(result)
            else:
                logging.debug(f'Skipping empty result from {ctx.worker_name(idx=idx)}')

    return sorted(list(results))


if __name__ == '__main__':
    mp.set_start_method('spawn')  # in case --processes is requested

    with parse_args() as ctx:
        logging.debug('starting ...')
        start_time = datetime.now()

        result = find_perfect_numbers(ctx)

        elapsed_time: timedelta = datetime.now() - start_time
        logging.info(f'{result} are perfect numbers in {elapsed_time}')

        logging.debug('done.')
