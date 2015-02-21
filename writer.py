# coding: utf-8
# Created @ January 7th 2015
# tomlwriter.py
"""
Writes toml files in a fancy way
"""

# TODO validate keys!
import datetime
import sys

class IllegalKeyChar(Exception):
    """An exception for when illegal characters are found in dictionary keys"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class WrongKeyType(Exception):
    """An exception for when the type of a key is not a string"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class MultiTypeArray(Exception):
    """An exception for when objects of differing types are found in an array"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class TomlWriter:
    stringtrans = {
        ord("\""): "\\\"",
        ord("\b"): "\\b", 
        ord("\t"): "\\t",
        ord("\n"): "\\n", 
        ord("\f"): "\\f", 
        ord("\r"): "\\r", 
        ord("/"): "\\/", 
        ord("\\"): "\\\\"
    }
    simpletypes = {
        int,
        float,
        datetime.datetime
    }
    
    invalid_key_chars = {
        "=", ".", "#", "[", "]"
    }
    
    def __init__(self):
        """docstring for init"""
        self.context = [] # ("name", "dict"|"list")
        self.current = "ERROR"
        self.cache = {}
    
    def simple_dump(self, data):
        """For *simple* data types"""
        if type(data) in self.simpletypes:
            return str(data)
            
        elif type(data) is bool:
            return str(int(data))
        
        elif type(data) is list:
            #print("- Dumping list")
            arrtype = type(data[0])
            parts = ["[ "]
            for num, item in enumerate(data):
                if type(item) is not arrtype:
                    self.error_array_type(item, arrtype, num, data, self.current)
                parts.append(self.simple_dump(item))
                parts.append(", ")
            parts.append("]")
            return "".join(parts)
        
        elif type(data) is str:
            return '"{}"'.format(data.translate(self.stringtrans))
        
        else:
            raise Exception("Unsupported type found: '{}': {}!".format(type(data), data))
    
    def sortkey(self, val):
        """A key for sorting stuff :)"""
        _ , value = val
        t = type(value)
        if (t is dict) or (value is None):  # dicts last
            return 2
        elif t is list:  # then lists in the middle
            return 1
        else:  # and everything else in sorted order before that
            return 0
    
    def get_context(self):
        """Returns the context as a tuple of its long toml name, and 
        its type (list or dict)"""
        if not self.context:
            # Default scope is a dict
            return ("", "dict")
            
        contype = self.context[len(self.context)-1][1]
        if contype is "list":
            conparts = ["[[ "]
        else:
            conparts = ["[ "]
        middle = []
        for (part, _) in self.context:
            middle.append(part)
        conparts.append(".".join(middle))
        if contype is "list":
            conparts.append(" ]]")
        else:
            conparts.append(" ]")
        return ("".join(conparts), contype)
    
    def error_array_type(self, item, arrtype, number, array, name):
        """Raises an error for an array element with a wrong type"""
        # Quote strings for easier reading :)
        if type(item) == str:
            item = '"' + item + '"'
            
        message = "Found {} in array of type {}. [{}]: {}, {}: {}".format(
            type(item), arrtype.__name__, number, item, 
            name if name else "Array", array)
            
        raise MultiTypeArray(message)
    
    def error_key_type(self, key, dic):
        """Raises an error for a dictionary key with a wrong type (not a string)"""
        message = "The provided key is a {} and not a string: {}. {}: {}".format(
            type(key), key, self.current if self.current else "Dictionary", dic)
        
        raise WrongKeyType(message)
    
    def _get_invalid(self, key):
        """Returns a set of the invalid characters in the given TOML key"""
        invalid = set()
        for char in key:
            if (char in self.invalid_key_chars) or char.isspace():
                invalid.add(char)
        return invalid
    
    def validate_context(self, key):
        """Validates the given context part"""
        invalid = self._get_invalid(key)
        if invalid:
            context, _ = self.get_context()
            message = "Found invalid chars ({}) in key '{}' of context '{}'".format(
                ", ".join(["'{}'".format(c) for c in invalid]), key, context
            )
            raise IllegalKeyChar(message)
    
    def validate_key(self):
        """Validates the current key"""
        invalid = self._get_invalid(self.current)
        if invalid:
            message = "Found invalid chars ({}) in key '{}'".format(
                ", ".join(["'{}'".format(c) for c in invalid]), self.current)
            raise IllegalKeyChar(message)
    
    def iter_lines(self, data):
        """Returns the string lines created from iterating over the given data"""
        # Make sure to eliminate nonetypes!
        if data is None:
            data = {}
        
        if type(data) == dict:
            # Name the context if present
            if self.context:
                name, contype = self.get_context()
                # TODO check for illegal dictionary keys
                
                
                # Check if it is already cached
                if id(data) in self.cache:
                    # Get the cached id
                    cid = self.cache_or_find(data)
                    #print("Found cache of {}: {}".format(id(data), cid))
                    
                    # Just make a reference in the output
                    yield name + " #@ref=" + cid
                    raise StopIteration
                
                else:
                    # Cache a new thing
                    cid = self.cache_or_find(data)
                    yield name + " #@id=" + cid
            
            for key, value in sorted(data.items(), key=self.sortkey):
                self.current = key
                if type(key) is not str:
                    self.error_key_type(key, data)
                
                # Validate the new context key
                self.validate_context(key)
                
                # Set the context
                if type(value) == list:
                    self.context.append((key, "list"))
                else:
                    self.context.append((key, "dict"))
                    
                # Iterate over the data
                yield from self.iter_lines(value)
                
                # Move out of context again
                self.context.pop() 
                
        elif type(data) is list:
            # Make sure to avoid errors early, here
            if not self.context:
                raise Exception("Not in context yet at {}!".format(data))
            
            # empty array
            if len(data) is 0:  
                yield self.current + " = []"
                
            else:
                # Check if it is cached
                if id(data) in self.cache:
                    cid = self.cache_or_find(data)
                    
                    self.validate_key()
                    
                    # Make a reference to the cached data
                    yield self.current + " = [] #@ref=" + str(cid)
                    # Then stop this iteration
                    raise StopIteration

                # Cache the list
                cid = self.cache_or_find(data)
                
                # Get the array type
                arrtype = type(data[0])
                
                # Save the name
                arrname = self.current
                
                # It's a list of dictionaries
                if arrtype == dict:  
                    
                    # Add a comment in the code before the array
                    # The special name is because it isn't on the same line as the data
                    yield "#@list-id=" + cid
                    
                    for num, item in enumerate(data):
                        if type(item) != dict:  # ensure homogenity
                            self.error_array_type(item, arrtype, num, data, arrname)
                        yield from self.iter_lines(item)
                
                # Normal list
                else:
                    self.validate_key()
                    yield self.current + " = " + self.simple_dump(data) + " #@id=" + cid
                    
        else:
            # Same as above, no context-related errors, pls
            if not self.context:
                raise Exception("Not in context yet at {}!".format(data))
            
            # Ensure that the current key is valid
            self.validate_key()
            yield self.current + " = " + self.simple_dump(data)            
    
    def cache_or_find(self, data):
        """Caches the data (sorta)"""
        data_id = id(data)
        if data_id in self.cache:
            return self.cache[data_id]
        else:
            nid = str(self.next_id)  # strings
            self.cache[data_id] = nid
            self.next_id += 1
            return nid
    
    def dump(self, data, flo=sys.stdout):
        """Dumps the given data into an open flo 
        (or stdout by default)"""
        self.cache = {} # python id: cache id
        self.next_id = 1
        self.context = []
        for line in self.iter_lines(data):
            print(line, file=flo)
    
    def dumps(self, data):
        """Dumps the given data into a string"""
        self.cache = {}
        self.next_id = 1
        self.context = []
        lines = list(self.iter_lines(data))
        return "\n".join(lines)

def dump(data, flo=sys.stdout):
    """Dumps an object to a file"""
    writer = TomlWriter()
    writer.dump(data, flo)

def dumps(data):
    """Dumps an object as a string"""
    writer = TomlWriter()
    return writer.dumps(data)

def main():
    """entry point"""
    import yaml
    import toml
    testdict = {
        "Name": "Bob",
        "Age": 36,
        "Occupation": "Builder",
        "Cats": [
            "Benny", "Biffy", "Rex"
        ],
        "Belongings": {
            "car": {
                "name": "shittycar",
                "age": 10,
                "noise": "LOOOOUD"
            },
            "keys": [
                "brown", "red", "blue"
            ]
        },
        "friends": [
            {
                "name": "billy",
                "age": 34,
                "cat": {
                    "name": "miss terrible",
                    "age": 14,
                    "smell": "dubious"
                }
            },
            {
                "name": "alice",
                "age": 38,
                "computers": [
                    {
                        "name": "Dell",
                        "age": 2,
                        "condition": "good"
                    },
                    {
                        "name": "Mac",
                        "age": 3,
                        "condition": "broken"
                    }
                ],
                "fears": [],
                "dog": None
            }
        ]
    }
    
    simple = {
        "hello": "world",
        "dump": [1,2,3,4],
        "and": datetime.datetime.now(),
        "also": 1,
        "and_finally": 3.91982,
        "a_dict": {
            "with.nested": {
                "value": "hello"
            }
        }
    }
    
    dump(simple)
    
    print("")
    print("==== Multidimensional arrays ====")
    print("")
    
    arraytest = {
        "2D": [
            [1,2,3,4,5,6],
            [6,5,4,3,2,1],
            [4,5,6,1,2,3],
            [3,2,1,6,5,4]
        ],
        "3D": [
            [
                [1,1,1,1],
                [2,2,2,2],
                [3,3,3,3]
            ],
            [
                [4,4,4,4],
                [5,5,5,5],
                [6,6,6,6],
            ]
            
        ]
    }
    print(toml.dumps(arraytest))
    dump(arraytest)
    
    print("")
    print("==== Recursive example =====")
    print("")
    
    alice = {
        "age": 20,
        "favorite food": "ice cream"
    }
    alice["likes"] = alice # narcissist!
    recursive = {
        "alice": alice,
        "params": [1,2,3,4,5]
    }
    recursive["extra"] = {
        "some": "field",
        "more params": recursive["params"]
    }
    
    dump(recursive)
    
    print("")
    print("=== Error messages === ")
    print("")
    print("Wrong array:")
    wrongarr = {
        "arr": [1, 2, 3, "WRONG", 4, 5]
    }
    try:
        dump(wrongarr)
        assert False, "It passed, FAIL!"
    except Exception as e:
        print("Got dump exception: {}".format(e))
    
    wrongdictarr = {
        "some scope": "hello world",
        "whatever": 321321321,
        "test": {
            "subscope": "value"
        },
        "long_unique_array_name": [
            {
                "name": "Alice",
                "tale": "YEAH!"
            },
            42
        ]
    }
    try:
        dump(wrongdictarr)
        assert False, "It passed, FAIL!"
    except Exception as e:
        print("Got dump exception: {}".format(e))
    
    print("Wrong keys:")
    badkeys = {
        "bob": "nice",
        "alice": "good",
        2: "HOW COULD YOU!",
        2.345: "WHY ARE YOU DOING THIS TO ME?!"
    }
    try:
        dump(badkeys)
        assert False, "It passed: FAIL!"
    except Exception as e:
        print("Got dump exception: {}".format(e))
    
    # == Illegal key char test
    try:
        dump({
            "Hello World": "Yay"
        })
    except Exception as e:
        print("Got dump exception: {}".format(e))
    
    """
    print("")
    print("==== Second example =====")
    print("")
    
    dump(testdict)
    
    print("")
    print("==== TOML ======")
    print("")
    
    toml.dump(testdict, sys.stdout)
    """

if __name__ == '__main__':
    #main()
    badstring = "hello\nhow\twell\fis this\\ escaped \" //\\?"
    print(badstring.translate(TomlWriter.stringtrans))
    #dump(data)
    #data = yaml.load("Map003.yaml")
    #toml.dump(data, sys.stdout)