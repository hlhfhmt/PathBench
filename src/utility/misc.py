import numpy as np
from collections.abc import Iterable
from typing import Tuple
import os
import importlib.util

def fmt_row(width, row):
    out = " | ".join(fmt_item(x, width) for x in row)
    return out


def fmt_item(x, l):
    if isinstance(x, np.ndarray):
        assert x.ndim == 0
        x = x.item()
    if isinstance(x, float):
        rep = "%g" % x
    else:
        rep = str(x)
    return " " * (l - len(rep)) + rep


def get_stats(loss, predictions, labels):
    cp = np.argmax(predictions.cpu().data.numpy(), 1)
    error = np.mean(cp != labels.cpu().data.numpy())
    return loss.item(), error


def print_stats(epoch, avg_loss, avg_error, num_batches, time_duration):
    print(
        fmt_row(10, [
            epoch + 1, avg_loss / num_batches, avg_error / num_batches,
            time_duration
        ]))


def print_header():
    print(fmt_row(10, ["Epoch", "Train Loss", "Train Error", "Epoch Time"]))


def exclude_from_dict(d, keys):
    return {key: d[key] for key in d if key not in keys}

def flatten(l, ignored_values = []):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            for el2 in flatten(el):
                if el2 not in ignored_values:
                    yield el2
        elif el not in ignored_values:
            yield el

def array_shape(a) -> Tuple[int, ...]:
    if isinstance(a[0], Iterable):
        return (len(a), *array_shape(a[0]))
    else:
        return (len(a),)

def try_load_algorithm(path):
    if not os.path.exists(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location("custom_loaded", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from algorithms.algorithm import Algorithm
        # For now, just looking to see if it subclasses "Algorithm"
        for item_n in dir(module):
            if item_n.startswith("_"): continue
            item = getattr(module, item_n)
            if issubclass(item, Algorithm):
                return item
        return None
    except:
        return None
