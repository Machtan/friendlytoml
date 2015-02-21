# Friendly Toml

This is a python module with a friendlier implementation for writing/reading the TOML config file types.

## Why it is friendly

### Reading

When you try to read a malformed file, it will tell you exactly* where it went wrong. 

### Writing

If you try to write something that doesn't work, it actually tells you why, and errors quickly (sorta).

It also writes your dictionaries in a sorted order, meaning that two runs with identical dictionary structures, will also have an identical output file. Neat!

Additionally, it writes lines in the target until it fails. This means that it might generate incomplete TOML files if you do not handle exceptions, but at the same time shows you exactly in which point it failed, and gives you an amount of debug information to work with, in case your structures were faulty to begin with.

\* _With multiline strings, the output shows the right line number and offset, but the wrong 'content'... sorry_

## Note

Since I tried to make this able to store more data types than what is reasonable for the specification (data structures with recursive references, like in YAML), the writer presently caches all data structures that it has written... this is probably quite inefficient for memory usage, so **Be Warned**.

### Compatibility

I've tried my best to make it conform to the standard (even for weird strings), but I haven't tested it extensively. It should however be more 'complete' than the other TOML versions I used (`PyToml` and `toml`, I think), but it writes more slowly (due to inefficient implementation, and an attempt to save more metadata). 

Anyhow, this is just something I made for my own sake, so it may or may not work. 

Use at your own risk :d (It shouldn't be able to mutate anything, though).


# Usage

Download the repo and either point your `$PYTHONPATH` environment variable to it, or just put it inside the folder in which you want to use it.


# Examples

```python
import friendlytoml as toml

if __name__ == __main__:
    bob = {"hello": "world", "nice": "day"}
    s = toml.dumps(bob)
    print(s)
    
    alice = toml.loads(s)
    print("Equal alice/bob : {0}".format(alice == bob))
    
    #testfile = "_test.toml"
    #with open(testfile, "w") as w:
    #    toml.dump(bob, w)
    #
    #carl = toml.load(testfile)
    #print("Equal carl/bob : {0}".format(carl == bob))
    # Please remove the test file again ;)
```


# Testing

I haven't really tested this very exhaustively.... D:

As such: It might work, it might not, it's written pretty badly so I'm not sure I'll fix it before it gets overhauled. My apologies.


# License

MIT (Do what you want)
