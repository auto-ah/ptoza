"""
.. moduleauthor:: Adam Gagorik <adam.gagorik@gmail.com>
"""
import argparse
import warnings
import logging
import yaml
import os

import pydarkstar.darkobject

class Options(pydarkstar.darkobject.DarkObject):
    """
    A Namespace object to use with argparse module.
    """
    def __init__(self, config='config.yaml', description=None):
        super(Options, self).__init__()
        self._ordered_keys = []
        self._exclude_keys = set()

        self._parent = argparse.ArgumentParser(add_help=False)
        self._parser = argparse.ArgumentParser(parents=[self._parent],
            description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

        self.config  = config

        # config file
        self._parent.add_argument('--config', type=str, default=self.config, metavar=self.config,
            help='configuration file name')

    def add_argument(self, *args, **kwargs):
        """
        Add command line info.
        """
        self._parser.add_argument(*args, **kwargs)

    def add_mutually_exclusive_group(self):
        """
        Add argument group.
        """
        return self._parser.add_mutually_exclusive_group()

    def parse_args(self, args=None):
        """
        Parse config file and then command line.
        """
        results, remaining_args = self._parent.parse_known_args(args, namespace=self)
        self.load()
        self._parser.parse_args(remaining_args, namespace=self)

    def __setattr__(self, key, value):
        super(Options, self).__setattr__(key, value)
        if not key.startswith('_'):
            if not key in self._ordered_keys:
                self._ordered_keys.append(key)

    def __setitem__(self, key, value):
        if not key in self._ordered_keys:
            raise KeyError('unknown key : %s' % key)
        setattr(self, key, value)

    def __getitem__(self, item):
        try:
            return super(Options, self).__getattribute__(item)
        except AttributeError:
            raise KeyError('unknown key : %s' % item)

    def include(self, key):
        """
        Include key for yaml.
        """
        self._exclude_keys.difference_update(key)
        self._exclude_keys.intersection_update(self._ordered_keys)

    def exclude(self, key):
        """
        Exclude key from yaml.
        """
        self._exclude_keys.add(key)
        self._exclude_keys.intersection_update(self._ordered_keys)

    @property
    def keys(self):
        """
        Return the ordered keys.
        """
        return self._ordered_keys

    def log_values(self, level=logging.DEBUG, fmt='%-10s = %s'):
        """
        Write values to logger.
        """
        for k in self.keys:
            self.log(level, fmt, k, getattr(self, k))

    def update(self, **kwargs):
        """
        Update values.
        """
        for k in kwargs:
            v = kwargs[k]

            if not hasattr(self, k):
                warnings.warn('key={} is unknown'.format(k))

            t = type(getattr(self, k))

            if not isinstance(v, t):
                warnings.warn('key={} is {}, expecting {}'.format(
                    k, type(v).__name__, t.__name__))

            self[k] = t(v)

    def load(self, stream=None, **kwargs):
        """
        Load data from yaml.
        """
        if stream is None:
            if not os.path.exists(self.config):
                return

            self.debug('load %s', self.config)
            with open(self.config, 'rb') as handle:
                data = yaml.load(handle)

        else:
            self.debug('load %s', stream)
            data = yaml.load(stream, **kwargs)

        if data is None:
            return

        try:
            self.update(**data)
        except TypeError:
            raise RuntimeError('yaml is invalid')

    def dump(self, stream=None):
        """
        Save data to yaml.
        """
        if stream is None:
            self.debug('save %s', self.config)
            with open(self.config, 'wb') as handle:
                yaml.dump(self.dict(), handle, default_flow_style=False)
        else:
            self.debug('save %s', stream)
            yaml.dump(self.dict(), stream, default_flow_style=False)

    def __iter__(self):
        """
        Iterate over keys.
        """
        for k in self._ordered_keys:
            yield k

    def dict(self):
        """
        Return namespace as python dict.
        """
        return {k : self[k] for k in self._ordered_keys if not k in self._exclude_keys}

if __name__ == '__main__':
    pass