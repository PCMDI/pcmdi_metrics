from __future__ import print_function

import dask.bag
from dask.distributed import Client


def serial(func, parameters):
    """
    Run the function with the parameters serially.
    """
    results = []
    for p in parameters:
        results.append(func(p))
    return results

def multiprocess(func, parameters, num_workers=None, context=None):
    """
    Run the function with the parameters in parallel using multiprocessing.

    ``context`` is one of ``{"fork", "spawn", "forkserver"}``.  For
    dask<2.16.0,the default context is "fork" and for dask>=2.16.0, the default
    is "spawn".
    """
    bag = dask.bag.from_sequence(parameters)

    config = {'scheduler': 'processes'}
    if context is not None:
        config['multiprocessing.context'] = context
    elif hasattr(parameters[0], 'multiprocessing_context'):
        config['multiprocessing.context'] = \
            parameters[0].multiprocessing_context

    with dask.config.set(config):
        if num_workers:
            results = bag.map(func).compute(num_workers=num_workers)
        elif hasattr(parameters[0], 'num_workers'):
            results = bag.map(func).compute(num_workers=parameters[0].num_workers)
        else:
            # num of workers is defaulted to the number of logical processes
            results = bag.map(func).compute()

        return results

def distribute(func, parameters, scheduler_addr=None):
    """
    Run the function with the parameters in parallel distributedly.
    """
    try:
        if scheduler_addr:
            addr = scheduler_addr
        elif not hasattr(parameters[0], 'scheduler_addr'):
            raise RuntimeError('The parameters or distribute() need a scheduler_addr parameter.')
        else:
            addr = parameters[0].scheduler_addr

        client = Client(addr)
        results = client.map(func, parameters)
        client.gather(results)
    except Exception as e:
        print('Distributed run failed.')
        raise e
    finally:
        client.close()

    return results