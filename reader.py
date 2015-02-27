# coding: utf-8
# Created January 8th 2015
# tomlreader.py

import datetime

def tokenize(iterable):
    """Tokenize the shit out of those lines.
    Yields tuples of (line_start, [(token, offset), ..]) """
    # global
    current = []
    line_tokens = []
    string_scope = False
    string_container = None
    triple_quoted = False
    escaped = False
    escaped_line = False
    triple_content = False
    array_nesting = 0
    line_start = 0 # At which line the returned tokens start
    _escaped_chars = {
        "b": "\b", 
        "t": "\t",
        "n": "\n", 
        "f": "\f", 
        "r": "\r", 
        "/": "/", 
        "\\": "\\"
    }
    
    def yield_current():
        """Yields the last token if any"""
        if current:
            token = "".join(current)
            #print("Yield: {}".format(token))
            line_tokens.append((token, start))
            current.clear()
    
    for line_num, line in enumerate(iterable):
        #print(line)
        assignment = False
        started = None
        start = 0
        identifier = False
        offset = 0
        line_length = len(line)
        
        #print("Start line, array nesting: {}: {}".format(array_nesting, line))
        # Continued single-line string
        if escaped:
            # Make sure not to escape the next non-whitespace char
            escaped_line = True
        
        # A string == being made
        elif triple_quoted:
            # If this == not after an empty first line
            if triple_content:
                # Add the newline
                current.append("\n")
            else:
                # Ensure that no more newlines are trimmed
                triple_content = True
        
        # Or there is simply a line ready
        elif line_tokens and (not array_nesting):
            yield (line_start, line_tokens)
            line_tokens = []
            line_start = line_num
            
        # If it's not in any scope, set the current line to this one
        elif not (string_scope or escaped or escaped_line or array_nesting):
            line_start = line_num
            
        while offset < line_length:
            #print("current: {}".format(current))
            char = line[offset]
            # Not inside a string
            if not string_scope:
                if char.isspace():
                    # Active token: save
                    yield_current()
                    start = offset + 1
                
                # Array scope
                elif array_nesting:
                    # Comment
                    if char == "#":
                        # Close the token
                        yield_current()
                        # Yield everything from this on
                        current.append(line[start:])
                        yield_current()

                        # Go to the next line
                        offset = line_length
                        continue
                    # String
                    if (char == '"') or (char == "'"):
                        string_scope = True
                        string_container = char
                
                        # Return previous tokens, if any
                        yield_current()
                    
                        # triple-quoted
                        if line[offset: offset + 3] == string_container * 3:
                            triple_quoted = True
                            triple_content = False
                            current.append(string_container) # *3
                            offset += 3
                            continue
                        
                        # Make sure to add the string identifying char
                        else:
                            offset += 1
                            current.append(char)
                            continue
                            
                    # Change the array scope
                    if char == "[" or char == "]":
                        yield_current()
                        start = offset
                        current.append(char)
                        yield_current()
                        if char == "[":
                            array_nesting += 1
                        else:
                            array_nesting -= 1
                    
                    # Add an element
                    elif char == ",":
                        yield_current()
                        # TODO continue or yield commas as well?
                    
                    # Just append the char
                    else:
                        current.append(char)
                else:   
                    # If the line content hasn't started yet
                    if not started: 
                        # A dict identifier == found
                        if char == "[":
                            # Check for two (list)
                            if line[offset + 1: offset + 2] == "[":
                                current.append("[[")
                                offset += 1
                                identifier = 2
                            else:
                                current.append("[")
                                identifier = 1
                            yield_current()
                    
                            # Set the start of the following token
                            start = offset + 1
                        
                        # Comments are 'special'
                        elif char == "#":
                            # Yield everything from this on
                            current.append(line[start:])
                            yield_current()
                        
                            # Go to the next line
                            offset = line_length
                            continue
                        
                        # If not, just start
                        else:
                            current.append(char)
                        started = True
                    
                    # The line has started
                    else:
                        # Comments are 'special'
                        if char == "#":
                            # Return the previous token
                            yield_current()
                            
                            # Yield everything from this on
                            start = offset
                            current.append(line[start:])
                            yield_current()
                            
                            # Go to the next line
                            offset = line_length
                            continue
                    
                        # Assignment operator found
                        elif char == "=":
                            # Yield preceding and set assignment flag
                            yield_current()
                            assignment = True
                            
                            # Yield this char
                            current.append(char)
                            start = offset
                            yield_current()
                            
                            # Move the start to after this char
                            start = offset + 1
                        
                        # Array, yay
                        elif assignment and (char == "["):
                            yield_current()
                            start = offset
                            current.append(char)
                            yield_current()
                            
                            # Start the scope
                            array_nesting += 1
                    
                        # Terminating identifier bracket
                        elif char == "]":
                            # There's an identifier to close
                            if identifier:                                
                                # Return the previous token
                                yield_current()
                            
                                # Check for a better token
                                if (identifier == 2) and (line[offset + 1: offset + 2] == "]"):
                                    current.append("]]")
                                    offset += 1
                                else:
                                    current.append("]")
                                
                                start = offset
                                yield_current()
                            
                                # Set the start of the following characters
                                start = offset + identifier
                                
                                identifier = 0
                            
                            else:
                                current.append(char)
                        # String start
                        elif assignment and (char == '"' or char == "'"):
                            string_scope = True
                            string_container = char
                    
                            # Return previous tokens, if any
                            yield_current()
                        
                            # triple-quoted
                            if line[offset: offset + 3] == string_container * 3:
                                triple_quoted = True
                                triple_content = False
                                current.append(string_container) # *3
                                offset += 3
                                continue
                            
                            # Make sure to add the string identifying char
                            else:
                                current.append(char)
                    
                        # Default: add char
                        else:
                            current.append(char)
        
            # Inside a string scope
            else:                
                if escaped:
                    # Ignore whitespace after the escape char
                    if char.isspace():
                        offset += 1
                        continue
                        
                    # It's a line escape
                    elif escaped_line:
                        # Ignore the escape thing, and set the escapes to false
                        escaped_line = False
                        
                        # Check if the string is ending
                        if char == string_container:
                            # It is indeed the end of a triple-quoted part
                            if triple_quoted:
                                if line[offset: offset + 3] == string_container * 3:
                                    escaped = False
                                    current.append(string_container) # * 3
                                    yield_current()
                                    offset += 3
                                    triple_quoted = False
                                    string_scope = False
                                    string_container = None
                                    continue
                                # Pass on the else to the below != \ check
                            
                            # It is the end of a single-quoted part
                            else:
                                escaped = False
                                current.append(char)
                                yield_current()
                                offset += 1
                                continue
                        
                        # It's not another escape char
                        if char != "\\":
                            escaped = False
                            current.append(char)
                            
                        offset += 1
                        continue
                        
                    # Escaped unicode sequence
                    if char == "u":
                        raise Exception("Escaped unicode == NOT supported!")
                    escape_char = _escaped_chars.get(char, None)
                    
                    # Another valid escapable char
                    if escape_char:
                        current.append(escape_char)
                    # Just something... ignore the escape
                    else:
                        current.append(char)
                    escaped = False
                
                # Handle those nasty multiline strings
                elif triple_quoted:
                    triple_content = True
                    if char == string_container:
                        # Check if this really terminates
                        if line[offset : offset + 3] == string_container * 3:
                            current.append(string_container) # * 3
                            yield_current()
                            offset += 3
                            triple_quoted = False
                            string_scope = False
                            string_container = None
                            continue
                        
                    # Escape character in a non-literal string
                    if (char == "\\") and (string_container != "'"):
                        escaped = True
                    
                    # False alarm, just add the char
                    else:
                        current.append(char)
                        
                else:
                    # Escape character in a non-literal string
                    if char == "\\" and (string_container != "'"):
                        escaped = True
                
                    # When the string ends
                    elif char == string_container:
                        current.append(char)
                        yield_current()
                        string_scope = False
                
                    # Normal case
                    else:
                        current.append(char)
            offset += 1
    
        # Get the remainder
        if (not (triple_quoted or escaped)) and current:
            yield_current()
    
    # Finally (after the for loop checking lines)
    if line_tokens:
        yield (line_start, line_tokens)



def loads(string):
    """Loads a dictionary from the given string"""
    data = {}
    lines = string.split("\n")
    scope = []
    
    var = {}
    var["last_scope"] = scope
    var["last_target"] = data
    replacements = {
        "b": "\b", 
        "t": "\t",
        "n": "\n", 
        "f": "\f", 
        "r": "\r", 
        "/": "/", 
        "\\": "\\"
    }
    illegal_key_chars = {
        "=", ".", "#", "[", "]"
    }
    
    def error_token(msg): # , line_num, offset
        """Raises an exception with some debug info :)"""
        arrmsg = " in array starting" if array_depth else ""
        message = msg + arrmsg + " on line {}:\n{}\n{}".format(
            line_num, lines[line_num], "~" * offset + "^")
        raise Exception(message)
    
    def validate(key):
        """Ensures that the given key token is valid"""
        invalid = set()
        for char in key:
            if char.isspace():
                invalid.add(char)
            elif char in illegal_key_chars:
                invalid.add(char)
        
        if invalid:
            error_token("Invalid characters ({}) found in key".format(
                ", ".join(["'{}'".format(c) for c in invalid])
            ))
    
    def interpret(token):
        """Interprets the given token as an internal value"""
        # String (the tokenizer handles escapes)
        if token.startswith(("'", '"')):
            return token[1:-1]
        
        # Number or datetime            
        elif token[0].isnumeric() or token.startswith(("-", "+")):
            if len(token) > 4:
                # Datetime format
                if token[4] == "-": # 1994-02-20 etc.
                    fmt = "%Y-%m-%dT%H:%M:%S"
                    value = token
                                
                    # Partial seconds
                    if "." in value:
                       fmt += ".%f"

                    # No timezone difference
                    if value.endswith("Z"):
                       fmt += "Z"
                    # Timezone difference
                    else:
                       # Remove the ':' in the RFC format
                       value = value[:-3] + value[-2:]
                       fmt += "%z"

                    # YYYY-MM-DDTHH:MM:SS-Offset
                    # 1996-12-19T16:39:57-08:00
                    # 1990-12-31T15:59:60-08:00
                    try:
                       return datetime.datetime.strptime(value, fmt)
                    except Exception as e:
                       error_token("Invalid datetime '{}'".format(token))
            
            # Float
            if "." in token:
                try:
                    return float(token)
                except ValueError as e:
                    error_token("Invalid float value '{}'".format(token))
            
            # Int
            else:
                try:
                    return int(token)
                except ValueError as e:
                    error_token("Invalid integer value '{}'".format(token))
        
        # Something else?
        else:
            error_token("Unknown value in assignment")
    
    def assign(final_key, value):
        """Assigns the given value to the key at the given key path in the data"""
        # Validate the key?
        validate(final_key)
        # Resolve the target
        # Cached
        if scope is var["last_scope"]:
            #print("Found cache for scope {}: {}".format(scope, var['last_target']))
            target = var["last_target"]
            
        # Nope
        else:
            target = data
            for key in scope:
                if type(target) == list:
                    # Get the last element then
                    target = target[-1]
                    
                found = target.get(key, None)
                # Create intermediate dictionaries
                if found is None:
                    # Ensure that the keys are valid
                    validate(key)
                    
                    # Create the stuff
                    #print("Creating intermediate '{}' for scope {}".format(
                    #    key, scope
                    #))
                    new = {}
                    target[key] = new
                    target = new
                else:
                    # It's just a dictionary
                    target = found
                    
            # Cache it for next time
            var["last_scope"] = scope
            var["last_target"] = target
        
        # If the target is a list of dicts
        if type(target) == list:
            # Then it should be the most reason of these :)
            target = target[-1]
        
        # Assign
        found = target.get(final_key, None)
        
        # A key is there
        if found:
            #print("Found value at scope {} and key {}: {}".format(scope, final_key, found))
            # Well, it's an array of dictionaries anyway
            if type(found) == list:
                # Check if the value is also a dictionary
                if type(value) != dict:
                    # TODO improve this error
                    message = "Non-dictionary value added to list of dictionaries"
                    raise Exception(message)
                
                # Assign it :)
                found.append(value)
            
            else:
                message = "Duplicate key found: '{}'\n{}".format(
                    final_key, lines[line_num]
                )
                raise Exception(message)
        
        # No key found
        else:
            # Just assign it :)
            target[final_key] = value
    
    for (line_num, line) in tokenize(lines):
        # Set the environment
        array_depth = 0 # How many open brackets are left? [ => 1
        id_brackets = 0 # 1 or 2 depending on type
        assignment = False # Are we assigning?
        started = False
        key = None
        value = None
        done = False
        arr = []
        
        # Parse the tokens
        for (token, offset) in line:
            # Priority of checks
            # Comment
            if token.startswith("#"):
                # TODO do that ID assignment stuff here
                pass
                
            # Done
            elif done:
                error_token("Found token after completed statement")
            
            # [ Dictionary.identifier ] or [[ Array.identifier ]]
            elif id_brackets:
                if not key:
                    key = token
                else:
                    if token == "]" * id_brackets:
                        if not key:
                            error_token("Expected key before closing bracket ")
                        
                        # Dict
                        if id_brackets == 1:
                            #print("Found dictionary")
                            new_scope = key.split(".")
                            scope = new_scope[:-1]
                            assign(new_scope[-1], {})
                            scope = new_scope
                        
                        # Array of dicts
                        else:
                            #print("Found array of dictionaries")
                            # Check whether it is started
                            new_dict_array = False
                            target = data
                            for part in key.split("."):
                                if type(target) == list:
                                    target = target[-1]
                                target = target.get(part, None)
                                if target == None:
                                    new_dict_array = True
                                    break
                            
                            # It hasn't started     
                            if new_dict_array:
                                #print("- Creating new array {}".format(key))
                                new_scope = key.split(".")
                                scope = new_scope[:-1]
                                # Create the array with the first dict
                                arr = [{}]
                                assign(new_scope[-1], arr)
                                #print("Arr: {}".format(arr))
                                #print("Data:")
                                #pprint.pprint(data)
                                #var["last_target"] = arr
                                scope = new_scope
                                #print("- Scope: {}".format(scope))
                            
                            # If it has started
                            else:
                                #print("- Appending to array")
                                new_scope = key.split(".")
                                scope = new_scope[:-1]
                                assign(new_scope[-1], {})
                                scope = new_scope
                            
                        done = True
                    else:
                        error_token("Expected closing bracket")
            
            # Assigning = true # <= that last part
            elif assignment:
                # Inside an array
                if array_depth:
                    # Start sub-array
                    if token == "[":
                        # Resolve the target
                        arr_target = value
                        for i in range(array_depth - 1):
                            arr_target = arr_target[-1]
                        
                        # Add to it :)
                        arr_target.append([])
                        array_depth += 1
                    
                    # End array
                    elif token == "]":
                        array_depth -= 1
                        # Check if it is the definitive end
                        if array_depth == 0:
                            done = True
                            assign(key, value)
                    
                    # New value
                    else:
                        #print("{:03}, array value: {}, depth: {}".format(
                        #    line_num, value, array_depth))
                        #print(lines[line_num])
                        
                        # Resolve the target
                        arr_target = value
                        for i in range(array_depth - 1):
                            arr_target = arr_target[-1]
                        
                        # Add the value of the token
                        arr_target.append(interpret(token))
                
                # Not inside an array
                else:
                    # Create the array and start it
                    if token == "[":
                        array_depth += 1
                        value = []
                    
                    # The assignment is done!
                    else:
                        assign(key, interpret(token))
                        done = True
            
            # The line isn't really started
            else:
                # There is a key
                if key:
                    if token != "=":
                        message = error_token("Missing assignment operator")
                        raise Exception(message)
                    else:
                        assignment = True
                
                # A dictionary starts
                elif token == "[":
                    id_brackets = 1
                
                # A list of dictionaries has an entry
                elif token == "[[":
                    id_brackets = 2
                
                # Or it's probably a key
                else:
                    key = token
                
                # The line is started!
                started = True
                
        if started and (not done):
            if id_brackets:
                error_token("Incomplete identifier")
            else:
                error_token("Incomplete assignment")
    
    # Return the constructed dictionary
    return data

def load(file):
    """Loads TOML from the given file path or file-like-object"""
    if type(file) == str:
        with open(file) as f:
            return loads(f.read())
    else:
        return loads(file.read())

def test_load():
    import pprint
    doc = """
    [test]
    [[test.friends]]
    #age = 10 #20
    #bob
    #andy + 2
    age = 30#300
    phone=11223344
    cost = 654563.5623432
    date = 1979-05-27T00:32:00.999999-07:00
    date2 = 1996-12-19T16:39:57-08:00
    r2d2 = 1997-12-19T16:39:57Z
    [[test.friends]]
    Hello = "World\\n Cool?\\t maybe"
    is = "This thing"       #working
    long = ''' This is some very long string
    As you can see,
    Maybe it's too long?''' # I don't know
    arr = [1,2, 3, 4, 5]
    more = ["hello","silly", "goose"]
    [test.friends.canoe]
    what = "About some string that is \\
    quoted unto the next line?"
    and = "What about \\
    Doing that \\
    Twice?" # It should be okay
    # TOML github examples:
    key1 = "The quick brown fox jumps over the lazy dog."

    key2 = \"""
The quick brown \\


      fox jumps over \\
        the lazy dog.\"""

    key3 = \"""\\
           The quick brown \\
           fox jumps over \\
           the lazy dog.\\
           \"""
    
    key4 = '''
    
    Will only the first newline become removed?
    I wonder :)
This is a literal, by the way \\
'''

continued = "some \\
string"
without = "any trailing whitespace"
    
    [new.scope]
    2d = [[1,2,3,4,], [5, 6,7, 8,9 ], 
[1,2,3,4,5], 
[5,6,7,8,9],
]
    and = "Something after the array ]]]][\\"\\"\\"[[[[]]]]]"
    
    literal = '\\hello world\\not doing anything... are you? \\t '
    
    #composite key = "Okay?" # Maybe?
    #broken =
    #and without assigner?
    
    #[ this is ]
    #[ this is. not okay]
    #another long key       = 3231.25234234
    """
    
    data = loads(doc)
    pprint.pprint(data)
    
    print("")
    print("===== Document 2 =====")
    print("")
    
    doc2 = """
    #Bill friend
    Bob = 200
    I = "Hello World"
    [friend]
    nice = "lady"
    float = 3.2312
    int = +3203232
    [ path.thing ]
    derp = "durr"
    [[ some.list ]]
    value = 1
    comment = "nothing" # Yeah, no comment
    [some.list.arguments]
    a = 2
    b = 5
    result = 7.3234
    [[ some.list]]
    value = 2
    lalala = 'huhuhu'
    [[some.list.friends]]
    name = "Alice"
    age = 21.323
    [[some.list.friends]]
    name = "Snorri"
    age = 18
    [some.other]
    value = "other"
    
    """
    
    data = loads(doc2)
    pprint.pprint(data)
    
    print("")
    print("===== Token printing ====")
    print("")
    
    
    print("Tokens:")
    for (line_num, line) in tokenize(doc.split("\n")):
        #print("{:03}: {}".format(num, line))
        #print("~" * start + "^")
        tokens = []
        #for (token, offset) in line:
        #    tokens.append(token)
        #print(" | ".join(tokens))
        print("{:03}: ".format(line_num) + " | ".join([token for (token, offset) in line]))
    
    #reader = TomlReader()
    #dic = reader.loads(doc)
    #pprint.pprint(dic)

def main():
    import json, pprint, sys#, toml
    #print(sys.argv)
    line = True
    #s = sys.stdin.read()
    #while line:
    #print("String: {}".format(string))
    with open("data/Animations.toml") as f:
        #s = f.read()
        print("Loading...")
        #data = loads(s)
        for _ in tokenize(f.readlines()):
            pass
        print("Loaded!")
    
    print("Dumping...")
    #print(toml.dumps(data))
    #pprint.pprint(data)
    #print(json.dumps(data))
    #import tomlwriter
    #tomlwriter.dump(data)
    
    
if __name__ == '__main__':
    #main()
    s = '''
[package]

name            = "token"
version         = "1.0.0-rc1"
authors         = ["Jakob Lautrup Nysom <jaln@itu.dk>"]
documentation   = "https://machtan.github.io/token-rs/token"
repository      = "https://github.com/Machtan/token-rs"
readme          = "README.md"
keywords        = ["string", "tokenizer", "sentence", "splitter"]
license         = "MIT?"
description     = """
A simple string-tokenizer (and sentence splitter)

Note: If you find that you would like to use the name for something more
appropriate, please just send me a mail at jaln at itu dot dk
"""
    '''.strip()
    
    print("="*40)
    print("="*15 + " Tokens " + "="*15)
    print("="*40)
    for (line_start, tokens) in tokenize(s.split("\n")):
        #print(tokens)
        for (token, offset) in tokens:
            print(token)
    
    print("="*40)
    bob = loads(s)
    print(bob)