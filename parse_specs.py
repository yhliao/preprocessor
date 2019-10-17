
def parse_block(infile):
   keys  = []
   specs = []

   endreached = False
   n = 0
   while not endreached:
      line = infile.readline().strip("\n").strip(' ')
      tokens = line.split("|")
      tokens = [tok.strip(' ') for tok in tokens]
      if line[0] == '#':
         pass ## For comments
      elif tokens[0] == ".END":
         endreached = True
      elif n == 0:
         keys    = tokens
      else:
         assert len(tokens)==len(keys)
         specs.append(tokens)
      n += 1
   return keys, specs

def parse_specfile(filename,blocks_key,blocks_specs,verbose=True):
   with open(filename,"r") as infile:
      EOF = False
      while not EOF: 
         line = infile.readline()
         if line == "":
            EOF=True
            if verbose:
               print("EOF reached... End parsing.")
         else:
            line = line.strip("\n")
            if line == "":
               pass

            else:
               tokens = line.split()
               if tokens[0][0] == '#':
                  pass ## For comments
               elif tokens[0] == ".START":
                  newblockname = tokens[1]
                  if verbose:
                     print ("Start reading new block ",newblockname)
                  newblockkey, newblockspecs = parse_block(infile)
                  blocks_key  [newblockname] = newblockkey
                  blocks_specs[newblockname] = newblockspecs

               else:
                  print ("parse_specfile: token {0} not recognizable".format(tokens[0]))
                  raise AssertionError
      infile.close()
   return blocks_key, blocks_specs

def lookup_spec(groups,key,value,specfile,verbose=False):
   blocks_key, blocks_specs = parse_specfile(specfile,{},{},verbose)
   for group in groups:

      keys = blocks_key[group]
      idx = keys.index(key)
      assert idx >= 0

      for spec_list in blocks_specs[group]:
         if spec_list[idx] == value:
            return (dict(zip(keys,spec_list)))

   raise AssertionError("lookup_spec: Not found")
