"""Pinned official interpreter and Python loader, with local orchestration.

The upstream source bytes are unchanged. Only two upstream helper functions
are AST-extracted to avoid importing the unrelated environment dependencies.
This is not Kaggle's sandbox or its time-limit enforcement.
"""
import ast
import builtins
import hashlib
import json
import os
import random
import sys
import types
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/kaggriculture'
_engine = None
_loader = None
_policy_active = False


def _offline_audit(event, args):
    if _policy_active and (event.startswith(('socket.', 'http.client.', 'urllib.', 'ctypes.'))
                           or event in ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn')):
        raise RuntimeError('Offline policy: network and external processes are forbidden')


sys.addaudithook(_offline_audit)


@contextmanager
def offline_policy():
    """Python audit guard for trusted standalone policies, not a security sandbox."""
    global _policy_active
    before = _policy_active
    _policy_active = True
    try:
        yield
    finally:
        _policy_active = before


class Attr(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value


def verify_vendor():
    manifest = json.loads((VENDOR / 'provenance.json').read_text())
    for name, entry in manifest['files'].items():
        actual = hashlib.sha256((VENDOR / name).read_bytes()).hexdigest()
        if actual != entry['sha256']:
            raise ValueError(f'Vendored source hash mismatch: {name}')
    return manifest


def _function(filename, name):
    tree = ast.parse((VENDOR / filename).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    scope = dict(Any=Any, Callable=Callable, random=random, sys=sys, os=os,
                 StringIO=StringIO, InvalidArgument=ValueError)
    exec(compile(ast.Module(body=[node], type_ignores=[]), filename, 'exec'), scope)
    return scope[name]


def load_engine():
    global _engine
    if _engine is None:
        verify_vendor()
        utility = types.ModuleType('kaggle_environments.utils')
        utility.resolve_episode_seed = _function('utils.py', 'resolve_episode_seed')
        real_import = builtins.__import__

        def scoped_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'kaggle_environments.utils' and level == 0:
                return utility
            return real_import(name, globals, locals, fromlist, level)

        module = types.ModuleType('kpro_official_engine')
        module.__file__ = str(VENDOR / 'kaggriculture.py')
        module.__dict__['__builtins__'] = dict(vars(builtins), __import__=scoped_import)
        exec(compile((VENDOR / 'kaggriculture.py').read_bytes(), module.__file__, 'exec'), module.__dict__)
        _engine = module
    return _engine


def load_policy(path):
    global _loader
    if _loader is None:
        verify_vendor()
        _loader = _function('agent.py', 'get_last_callable')
    path = Path(path).resolve()
    # The upstream loader changes stdout/sys.path; restore even after failure.
    before_path, before_stdout = sys.path[:], sys.stdout
    before_modules = dict(sys.modules)
    try:
        with offline_policy():
            return _loader(path.read_text(), path=str(path))
    finally:
        sys.path[:] = before_path
        sys.stdout = before_stdout
        for name in set(sys.modules) - set(before_modules):
            del sys.modules[name]
        sys.modules.update(before_modules)


def new_game(seed):
    if type(seed) is not int:
        raise ValueError('Integer seed required')
    schema = json.loads((VENDOR / 'kaggriculture.json').read_text())['configuration']
    configuration = Attr({k: v.get('default') if isinstance(v, dict) else v for k, v in schema.items()})
    configuration.seed = seed
    env = Attr(configuration=configuration, info={}, done=False)
    state = [Attr(observation=Attr(step=0, remainingOverageTime=60),
                  status='ACTIVE', reward=0, action={}) for _ in range(2)]
    load_engine().interpreter(state, env)
    return state, env
