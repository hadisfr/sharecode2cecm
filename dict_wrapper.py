#!/usr/bin/env python3


class DictWrapper():
    """object-like dict wrapper"""

    def __init__(self, dictionary=dict()):
        self.dictionary = dictionary
        for (key, value) in self.dictionary.items():
            if isinstance(value, dict):
                self.dictionary[key] = DictWrapper(value)

    def __getattr__(self, key):
        try:
            return self.dictionary[key]
        except KeyError:
            return dict.__getattribute__(self.dictionary, key)

    def __setattr__(self, key, value):
        if key == "dictionary":
            return super().__setattr__(key, value)
        else:
            try:
                self.dictionary[key] = value
            except KeyError:
                return dict.__setattr__(self.dictionary, key, value)

    def __repr__(self):
        return "DictWrapper(%r)" % self.dictionary

    def __str__(self):
        return str(self.dictionary)

    def __iter__(self):
        return dict.__iter__(self.dictionary)

    def __len__(self):
        return len(self.dictionary)
