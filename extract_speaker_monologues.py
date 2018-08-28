def extract_speaker_monologues(file='./samples/wfc.txt'):
  '''extracts the monologues from an earnings call transcript. attributes speaker to each monologue.
  returns list of executive names, list of analyst names, and dictionary of the monologues'''

  # read text file
  with open(file,'r') as f:
    allLines = f.readlines()
  allLines = [line for line in allLines if line!='\n'] # strip empty lines

  # get executives list
  def extract_name(line, monologues):
    name = line.lower().split('-')[0].split()
    name = [name[0], name[-1]]
    name = ' '.join(name)
    monologues[name] = ''
    return name

  # prepare for the loop
  flag = ''
  executives = []
  analysts = []
  monologues = {'operator': ''}

  # loop over all lines
  for line in allLines:

    # set flag if key line is detected
    if 'executives\n'==line.lower(): flag = 'executives'; continue
    if 'analysts\n'==line.lower(): flag = 'analysts'; continue
    if line.lower().strip('\n') in executives or line.lower().strip('\n') in analysts or line.lower().strip('\n') in monologues.keys():
      flag = line.lower().strip('\n')
      if flag not in monologues.keys(): monologues[flag] = '' # create key in monologues dictionary
      continue

    # process lines according to the current flag
    if flag=='executives': executives.append(extract_name(line, monologues))
    if flag=='analysts': analysts.append(extract_name(line, monologues))
    if flag in monologues.keys():
      monologues[flag] = monologues[flag]+' '+line

  return executives, analysts, monologues
