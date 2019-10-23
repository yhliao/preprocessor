from pandas import DataFrame
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
   df = DataFrame(specs, columns=keys)
   return df

def parse_specfile(filename,blocks,verbose=True):
   ## blocks[newblockname] = DataFrame_from_new_block
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
                  blocks [newblockname] = parse_block(infile)

               else:
                  print ("parse_specfile: token {0} not recognizable".format(tokens[0]))
                  raise AssertionError
      infile.close()
   return blocks

def lookup_spec(groups,key,value,specfile,verbose=False):
   blocks = parse_specfile(specfile,{},verbose)
   for group in groups:

      for row in blocks[group].iterrows():
         if row[1][key] == value:
            return dict(row[1])

   raise AssertionError("lookup_spec: Not found")
