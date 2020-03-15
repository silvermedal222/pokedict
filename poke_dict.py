import sys, csv
from enum import IntEnum
from string import digits

class TypeEnum(IntEnum):
	UNKNOWN = -1
	NONE = 0
	BUG = 1
	DARK = 2
	DRAGON = 3
	ELECTRIC = 4
	FAIRY = 5
	FIGHTING = 6
	FIRE = 7
	FLYING = 8
	GHOST = 9
	GRASS = 10
	GROUND = 11
	ICE = 12
	NORMAL = 13
	POISON = 14
	PSYCHIC = 15
	ROCK = 16
	STEEL = 17
	WATER = 18

class Pokemon:
	def __init__(self, num, name, **kwargs):
		self._num = num
		# self._name = name[0].upper() + name[1:].lower()
		self._name = name
		self._type1 = kwargs.get('type1', TypeEnum.UNKNOWN)
		self._type2 = kwargs.get('type2', TypeEnum.NONE)
		self._evo_from = None
		self._evo_to = []

	def get_num(self):
		return self._num

	def set_num(self, num):
		self._num = num

	def get_name(self):
		return self._name

	def set_name(self, name):
		self._name = name

	def get_type1(self):
		return self._type1

	def set_type1(self, type1):
		self._type1 = type1

	def get_type2(self):
		return self._type2

	def set_type2(self, type2):
		self._type2 = type2

	def get_evo_from(self):
		return self._evo_from

	def set_evo_from(self, pokemon, inner=False):
		self._evo_from = pokemon
		# not inner to prevent infinite loop
		if isinstance(pokemon, Pokemon) and not inner:
			pokemon.set_evo_to(self, inner=True)

	def del_evo_from(self, inner=False):
		# not inner to prevent infinite loop
		if isinstance(self._evo_from, Pokemon) and not inner:
			self._evo_from.del_evo_to(self, inner=True)
		self._evo_from = None

	def get_evo_to(self):
		return self._evo_to

	def set_evo_to(self, pokemon, inner=False):
		if isinstance(pokemon, Pokemon):
			duplicate = False
			for mon in self._evo_to:
				if mon.get_num() == pokemon.get_num():
					# mon already in evo_to list
					duplicate = True
					break

			if not duplicate:
				# keep all evos in order
				i = 0
				for mon in self._evo_to:
					if mon.get_num() > pokemon.get_num():
						break
					i += 1
				self._evo_to.insert(i, pokemon)

			# prevent infinite loop
			if not inner:
				pokemon.set_evo_from(self, inner=True)

	def del_evo_to(self, pokemon, inner=False):
		if isinstance(pokemon, Pokemon):
			i = 0
			# find pokemon to delete
			for mon in self._evo_to:
				if mon.get_num() == pokemon.get_num():
					break
				i += 1
			# if pokemon found
			if i < len(self._evo_to):
				del self._evo_to[i]

			# prevent infinite loop
			if not inner:
				pokemon.del_evo_from(inner=True)


	def __repr__(self):
		return 'No: {}\nName: {}\nType 1: {}\nType 2: {}\nEvolves From: {}\nEvolves To: {}'.format(self._num, self._name, self._type1.name, self._type2.name, str(self._evo_from), [str(pokemon) for pokemon in self._evo_to])

	def __str__(self):
		return '{} {}'.format(self._num, self._name)


## PokeDex Exceptions
class PokeDexError(Exception):
	pass

class PokeDexHasEntryName(PokeDexError):
	pass

class PokeDexHasEntryNum(PokeDexError):
	pass

class PokeDexFull(PokeDexError):
	pass

class PokeDexEmpty(PokeDexError):
	pass

class PokeDexOutOfRange(PokeDexError):
	pass

class PokeDexBadMax(PokeDexError):
	pass

class PokeDex:
	def __init__(self, filename, max_num, new):
		self._by_num = {}
		self._by_name = {}
		self._max_num = max_num
		self._size = 0
		if not new:
			self.populate_from_file(filename)

	def __len__(self):
		return self._size

	def get_max_num(self):
		return self._max_num

	def set_max_num(self, new_max):
		if new_max < self._size or new_max <= 0:
			raise PokeDexBadMax

		self._max_num = new_max

	def populate_from_file(self, filename):
		filename += '.csv'
		print('Opening {}'.format(filename))
		progress = 1

		first = True
		with open(filename, 'r') as csvfile:
			pokedex_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
			from_to_list = []
			for row in pokedex_reader:
				# first row contains the max_num
				if first:
					self._max_num = int(row[0])
					first = False
					continue
				# add all mons to the dex
				mon, from_to = self._csv_row_to_pokemon(row)
				from_to_list.append(from_to)
				self.add(mon)
				print('Loading -- {}/{}'.format(progress, self._max_num), end='\r')
				progress += 1
			# link all evolutions
			self._link_evolutions(from_to_list)
		print('\n{} loaded.'.format(filename))

	def _csv_row_to_pokemon(self, row):
		# print(row)
		num = int(row[0])
		name = row[1]
		type1 = TypeEnum[row[2][9:]]
		type2 = TypeEnum[row[3][9:]]
		evo_from = None if len(row[4]) == 0 else int(row[4])
		evo_to = []
		for evo in row[5:]:
			evo_to.append(int(evo))

		opts = {}
		opts['type1'] = type1
		opts['type2'] = type2

		return Pokemon(num, name, **opts), (num, evo_from, evo_to)

	def _link_evolutions(self, from_to_list):
		for from_to in from_to_list:
			num, evo_from, evo_to = from_to
			pokemon = self.find(num)
			from_mon = self.find(evo_from) if evo_from != None else None
			to_mons = [self.find(evo) for evo in evo_to]
			pokemon.set_evo_from(from_mon)
			for mon in to_mons:
				pokemon.set_evo_to(mon)

	def find(self, query):
		return self._find_by_num(query) if isinstance(query, int) else self._find_by_name(query)

	def _find_by_num(self, query):
		return self._by_num.get(query, None)

	def _find_by_name(self, query):
		# name = query[0].upper() + query[1:].lower()
		name = query.lower()
		return self._by_name.get(name, None)

	def add(self, pokemon):
		if self._size >= self._max_num:
			raise PokeDexFull
		elif pokemon.get_num() in self._by_num:
			raise PokeDexHasEntryNum
		elif pokemon.get_name() in self._by_name:
			raise PokeDexHasEntryName
		elif pokemon.get_num() <= 0 or pokemon.get_num() > self._max_num:
			raise PokeDexOutOfRange

		self._by_num[pokemon.get_num()] = pokemon
		self._by_name[pokemon.get_name().lower()] = pokemon
		self._size += 1

	def delete(self, pokemon):
		if self._size == 0:
			raise PokeDexEmpty

		if pokemon == None:
			print('The specified pokemon does not exist in the pokedex.')
			return

		if pokemon.get_num() not in self._by_num and pokemon.get_name().lower() not in self._by_name:
			print('{} is only in one of the searchable dicts (num/name) for some reason. Try reloading.'.format(pokemon))
			return

		# delete self as the evo_from for all subsequent evolutions
		while len(pokemon.get_evo_to()) > 0:
			pokemon.get_evo_to()[0].del_evo_from()

		# delete self as an evo_to entry for the prior evolution
		pokemon.del_evo_from()

		del self._by_num[pokemon.get_num()]
		del self._by_name[pokemon.get_name().lower()]
		self._size -= 1

	def update_num(self, pokemon, num):
		del self._by_num[pokemon.get_num()]
		self._by_num[num] = pokemon

	def update_name(self, pokemon, name):
		del self._by_name[pokemon.get_name().lower()]
		self._by_name[name] = pokemon

	def list_pokemon(self, fltr):
		if fltr == 'all':
			for i in range(1, self._max_num+1):
				pokemon = self._by_num.get(i, '{} UNKNOWN/UNSEEN'.format(i))
				print(pokemon)
		elif fltr == 'known':
			for i in range(1, self._max_num+1):
				if i in self._by_num:
					print(self._by_num[i])

	# When writing to a csv, all evolution references should be the pokedex number
	# The list of numbers in the to_evo list should be delimited by spaces, and each number should be less than the current mon's number
	# [num, name, type1, type2, from, flatten(to)]

	def write(self, outname):
		outname += '.csv'
		progress = 1
		with open(outname, 'w', newline='') as f:
			pokedex_writer = csv.writer(f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			# first row is the max_num
			pokedex_writer.writerow([self._max_num])
			# write all pokemon
			for entry in range(1, self._max_num+1):
				pokemon = self.find(entry)
				if pokemon == None:
					continue
				# print('Writing Entry--')
				# print(repr(pokemon))
				row = []
				row.append(pokemon.get_num())
				row.append(pokemon.get_name())
				row.append(pokemon.get_type1())
				row.append(pokemon.get_type2())
				evo_from = pokemon.get_evo_from()
				row.append(evo_from.get_num() if isinstance(evo_from, Pokemon) else None)
				for mon in pokemon.get_evo_to():
					row.append(mon.get_num())
				pokedex_writer.writerow(row)
				print('Progress -- {}/{}'.format(progress, self._max_num), end='\r')
				progress += 1
		print('\nWrote to {}'.format(outname))

class MainLoop:
	def __init__(self, filename='national', max_num=890, new=False):
		self.pokedex = PokeDex(filename, max_num, new)
		self.filename = filename
		self.help_msgs = self._init_help_msgs()
		self.edit_help_msgs = self._init_edit_help_msgs()
		self.change_made = False
		self.edit_change_made = False
		self.main_exit = False
		self.edit_exit = False

	def _init_help_msgs(self):
		help_msgs = {}
		help_msgs['add'] = 'Add a pokemon to the pokedex. The command format is \'add <num> <name>\'.'
		help_msgs['delete'] = 'Delete a pokemon from the pokedex. The command format is \'delete <num>|<name>\'.'
		help_msgs['edit'] = 'Edit the number, name, type1, and type2 fields for a pokemon. Editing mode can be identified by the console input reader looking like \'*>>\'. The command format is \'edit <num>|<name>\'. Type \'help\' while in editing more for more details.'
		help_msgs['evos'] = 'See the full evolution chain for a pokemon. The command format is \'evos <num>|<name>\'.'
		help_msgs['exit'] = 'Exit the pokedex. The command format is \'exit\'.'
		help_msgs['find'] = 'Find a pokemon in the pokedex. The command format is \'find <num>|<name>\'.'
		help_msgs['getmax'] = 'Get the max PokeDex size. The command format is \'getmax\'.'
		help_msgs['getsize'] = 'Get the current PokeDex size. The command format is \'getsize\'.'
		help_msgs['help'] = 'See detailed instructions for how to use this pokedex. The command format is \'help [<cmd>]\'.'
		help_msgs['link'] = 'Link two pokemon in an evolutionary chain. The command format is \'link <num>|<name> <num>|<name>\' where the first pokemon evolves into the second.'
		help_msgs['list'] = 'List the pokemon in the pokedex. The command format is \'list <filter>\' where <filter> can be \'all\'|\'known\'.'
		help_msgs['relink'] = 'Relink all evolutions in the pokedex. Use to fix all potentially broken/lopsided evolution chains after unlinking. Suggest to use after all unlinks. The command format is \'relink\'.'
		help_msgs['setmax'] = 'Set the max PokeDex size. The max size must be greater than the current PokeDex size. The command format is \'setmax <max_num>\'.'
		help_msgs['unlink'] = 'Unlink two pokemon in an evolutionary chain. The command format is \'unlink <num>|<name> <num>|<name>\' where the pokedex stores the first pokemon as evolving into the second.'
		help_msgs['write'] = 'Write the current pokedex to disk. The command format is \'write [outname]\' where \'outname\' is the name of the file to write to. Beware that if a file of the same name already exists in the current directory, this will overwrite that file.'

		return help_msgs

	def _init_edit_help_msgs(self):
		edit_help_msgs = {}

		edit_help_msgs['exit'] = 'Exit editing mode. The command format is \'exit\'.'
		edit_help_msgs['help'] = 'See detailed instructions for how to use the editing mode. The command format is \'help [<cmd>]\'.'
		edit_help_msgs['save'] = 'Save the current values for the pokemon. The command format is \'save\'.'
		edit_help_msgs['set'] = 'Set a value for a field. The command format is \'set <field> <value>\' where <field> can be \'number\'|\'name\'|\'type1\'|\'type2\'.'
		edit_help_msgs['status'] = 'Check the current editing status. The edits will only be retained in the pokedex if saved. The command format is \'status\'.'

		return edit_help_msgs


	def _create_pokemon(self, args):
		num = int(args[0])
		name = args[1]
		
		opts = {}
		## Get user input
		t1 = input('Enter Type 1 (Optional)\n>> ').upper().rstrip()
		get_t2 = len(t1) > 0
		if get_t2:
			t2 = input('Enter Type 2 (Optional)\n>> ').upper().rstrip()

		## Set user input
		# type 1
		if len(t1) == 0:
			print('Setting Type 1 to UNKNOWN')
		else:
			print('Setting Type 1 to {}'.format(t1))
			opts['type1'] = TypeEnum[t1]
		# type 2
		if get_t2:
			if len(t2) == 0:
				print('Setting Type 2 to NONE')
			else:
				print('Setting Type 2 to {}'.format(t2))
				opts['type2'] = TypeEnum[t2]

		return Pokemon(num, name, **opts)

	def _get_query_type(self, query):
		# check if user inputted num or name, and return correctly typed query
		by_num = True
		for ch in query:
			if ch not in digits:
				by_num = False
				break
		return int(query) if by_num else query

	def add(self, args):
		# check if input is in correct format
		if len(args) != 2:
			print('Wrong number of arguments supplied. Retry command as \'add <num> <name>\'.')
			return

		pokemon = self._create_pokemon(args)
		self.pokedex.add(pokemon)
		self.change_made = True

	def edit(self, args):
		# check if input is in correct format
		if len(args) != 1:
			print('Wrong number of arguments supplied. Retry command as \'edit <num>|<name>\'.')
			return

		query = self._get_query_type(args[0])
		pokemon = self.pokedex.find(query)

		print('Entering Editing Mode')
		self.edit_loop(pokemon)

	def edit_exit_func(self, pokemon, vals, args):
		if self.edit_change_made:
			print('There are unsaved changes for this pokemon. Exit without saving changes?')
			yn = input('Y/N? ')
			if yn.lower() == 'y':
				print('Exiting.')
				self.edit_exit = True
			else:
				print('Cancelling exit.')
		else:
			print('Exiting.')
			self.edit_exit = True

	def edit_help(self, pokemon, vals, args):
		# check if input is in correct format
		if len(args) > 2:
			print('Wrong number of arguments supplied. Retry command as \'help [<cmd>]\'.')
			return

		if len(args) == 0:
			print('The following commands are available. Type \'help <cmd>\' to see more detailed instructions.')
			print('exit')
			print('help')
			print('save')
			print('set')
			print('status')

		if len(args) == 1:
			print(self.edit_help_msgs.get(args[0], '{} is not a valid <cmd>.'.format(args[0])))

	def edit_save(self, pokemon, vals, args):
		# check if input is in correct format
		if len(args) != 0:
			print('Wrong number of arguments supplied. Retry command as \'save\'.')
			return

		print('Saving Status')
		print('{} -----> {}'.format(pokemon.get_num(), vals[0]))
		print('{} -----> {}'.format(pokemon.get_name(), vals[1]))
		print('{} -----> {}'.format(pokemon.get_type1().name, vals[2].name))
		print('{} -----> {}'.format(pokemon.get_type2().name, vals[3].name))

		self.change_made = True
		self.edit_change_made = False

		self.pokedex.update_num(pokemon, vals[0])
		self.pokedex.update_name(pokemon, vals[1])

		pokemon.set_num(vals[0])
		pokemon.set_name(vals[1])
		pokemon.set_type1(vals[2])
		pokemon.set_type2(vals[3])

	def edit_set(self, pokemon, vals, args):
		# check if input is in correct format
		if len(args) != 2:
			print('Wrong number of arguments supplied. Retry command as \'set <field> <value>\'.')
			return

		field = args[0]
		if field == 'number':
			print('Setting \'number\' to {}'.format(args[1]))
			self.edit_change_made = True
			vals[0] = int(args[1])
		elif field == 'name':
			print('Setting \'name\' to {}'.format(args[1][0].upper() + args[1][1:].lower()))
			self.edit_change_made = True
			vals[1] = args[1][0].upper() + args[1][1:].lower()
		elif field == 'type1':
			print('Setting \'type1\' to {}'.format(args[1].upper()))
			self.edit_change_made = True
			vals[2] = TypeEnum[args[1].upper()]
		elif field == 'type2':
			print('Setting \'type2\' to {}'.format(args[1].upper()))
			self.edit_change_made = True
			vals[3] = TypeEnum[args[1].upper()]
		else:
			print('Bad <field> supplied. <field> can be \'number\'|\'name\'|\'type1\'|\'type2\'.')

	def edit_status(self, pokemon, vals, args):
		# check if input is in correct format
		if len(args) != 0:
			print('Wrong number of arguments supplied. Retry command as \'status\'.')
			return

		print('Current Editing Status')
		print('Number: {} --?--> {}'.format(pokemon.get_num(), vals[0]))
		print('Name: {} --?--> {}'.format(pokemon.get_name(), vals[1]))
		print('Type 1: {} --?--> {}'.format(pokemon.get_type1().name, vals[2].name))
		print('Type 2: {} --?--> {}'.format(pokemon.get_type2().name, vals[3].name))

	def get_edit_cmds(self):
		edit_cmds = {}

		edit_cmds['exit'] = self.edit_exit_func
		edit_cmds['help'] = self.edit_help
		edit_cmds['save'] = self.edit_save
		edit_cmds['set'] = self.edit_set
		edit_cmds['status'] = self.edit_status

		return edit_cmds

	def edit_loop(self, pokemon):
		edit_cmds = self.get_edit_cmds()

		vals = []
		vals.append(pokemon.get_num())
		vals.append(pokemon.get_name())
		vals.append(pokemon.get_type1())
		vals.append(pokemon.get_type2())

		while(True):
			try:
				if self.edit_exit:
					break
				line = input('*>> ').rstrip()
				if len(line) == 0:
					continue
				args = line.split()
				func = edit_cmds.get(args[0], None)
				if func == None:
					print('The input \'{}\' is not a valid command. Please try again, or type \'help\' to see the available commands. Commands are case-sensitive.'.format(args[0]))
				else:
					func(pokemon, vals, args[1:])
			except PokeDexHasEntryName:
				print('An entry already exists with that name. Delete the conflicting entry before trying again.')
			except PokeDexHasEntryNum:
				print('An entry already exists with that number. Delete the conflicting entry before trying again.')
			except Exception as e:
				# print('Edit exception')
				# print(e)
				print('Oops! Something went wrong. Please try again.')
		print('Exiting Editing Mode')
		# reset edit_exit flag
		self.edit_exit = False

	def delete(self, args):
		# check if input is in correct format
		if len(args) != 1:
			print('Wrong number of arguments supplied. Retry command as \'delete <num>|<name>\'.')
			return

		query = self._get_query_type(args[0])
		pokemon = self.pokedex.find(query)

		self.pokedex.delete(pokemon)
		self.change_made = True

	def evo_chain(self, args):
		# check if input is in correct format
		if len(args) != 1:
			print('Wrong number of arguments supplied. Retry command as \'evos <num>|<name>\'.')
			return

		query = self._get_query_type(args[0])
		pokemon = self.pokedex.find(query)
		
		self._chain_printer(pokemon)

	def _chain_printer(self, pokemon):
		# essentially pretty printing of a Depth First Traversal
		root = pokemon
		while root.get_evo_from() != None:
			root = root.get_evo_from()

		self._print_helper(root, 0)

	def _print_helper(self, pokemon, depth, indent=4):
		space = ' ' * indent * depth
		print(space + str(pokemon))
		for mon in pokemon.get_evo_to():
			self._print_helper(mon, depth+1)

	def find(self, args):
		# check if input is in correct format
		if len(args) < 1:
			print('Wrong number of arguments supplied. Retry command as \'find <num>|<name>\'.')
			return

		query = self._get_query_type(args[0])
		pokemon = self.pokedex.find(query)
		print(repr(pokemon))
		return pokemon

	def get_max(self, args):
		print('The PokeDex max size is {}.'.format(self.pokedex.get_max_num()))

	def get_size(self, args):
		print('The current PokeDex size is {}.'.format(len(self.pokedex)))

	def link(self, args):
		# check if input is in correct format
		if len(args) != 2:
			print('Wrong number of arguments supplied. Retry command as \'link <num>|<name> <num>|<name>\'.')
			return

		p1 = self._get_query_type(args[0])
		p2 = self._get_query_type(args[1])
		poke1 = self.pokedex.find(p1)
		poke2 = self.pokedex.find(p2)
		if poke1 == None:
			print('{} was not found in the PokeDex.'.format(args[0]))
			return
		if poke2 == None:
			print('{} was not found in the PokeDex.'.format(args[1]))
			return
		poke1.set_evo_to(poke2)
		print('Linked {} -----> {}'.format(str(poke1), str(poke2)))
		self.change_made = True

	def list_pokemon(self, args):
		# check if input is in correct format
		if len(args) != 1:
			print('Wrong number of arguments supplied. Retry command as \'list <filter>\'.')
			return

		if args[0] == 'all':
			self.pokedex.list_pokemon(args[0])
		elif args[0] == 'known':
			self.pokedex.list_pokemon(args[0])
		else:
			print('Bad <filter> supplied. <filter> can be \'all\'|\'known\'')

	def run_help(self, args):
		# check if input is in correct format
		if len(args) > 2:
			print('Wrong number of arguments supplied. Retry command as \'help [<cmd>]\'.')
			return

		if len(args) == 0:
			print('The following commands are available. Type \'help <cmd>\' to see more detailed instructions.')
			print('add')
			print('delete')
			print('edit')
			print('evos')
			print('exit')
			print('find')
			print('getmax')
			print('getsize')
			print('help')
			print('link')
			print('list')
			print('relink')
			print('setmax')
			print('unlink')
			print('write')

		if len(args) == 1:
			print(self.help_msgs.get(args[0], '{} is not a valid <cmd>.'.format(args[0])))

	def relink(self, args):
		print('Relinking all evolution chains.')
		for i in range(1, self.pokedex.get_max_num()+1):
			pokemon = self.pokedex.find(i)
			if isinstance(pokemon, Pokemon):
				for evo in pokemon.get_evo_to():
					evo.set_evo_from(pokemon, inner=True)

	def set_max(self, args):
		# check if input is in correct format
		if len(args) != 1:
			print('Wrong number of arguments supplied. Retry command as \'setmax <max_num>\'.')
			return

		new_max = int(args[0])
		self.pokedex.set_max_num(new_max)
		print('New max size of the PokeDex is set to {}.'.format(new_max))
		self.change_made = True

	def unlink(self, args):
		# check if input is in correct format
		if len(args) != 2:
			print('Wrong number of arguments supplied. Retry command as \'unlink <num>|<name> <num>|<name>\'.')
			return

		p1 = self._get_query_type(args[0])
		p2 = self._get_query_type(args[1])
		poke1 = self.pokedex.find(p1)
		poke2 = self.pokedex.find(p2)
		if poke1 == None:
			print('{} was not found in the PokeDex.'.format(args[0]))
			return
		if poke2 == None:
			print('{} was not found in the PokeDex.'.format(args[1]))
			return
		poke1.del_evo_to(poke2)
		print('Unlinked {} --X--> {}'.format(str(poke1), str(poke2)))
		self.change_made = True

	def write(self, args):
		# check if input is in correct format
		if len(args) > 1:
			print('Wrong number of arguments supplied. Retry command as \'write [outname]\'.')
			return

		fname = self.filename if len(args) == 0 else args[0]
		print('Write current pokedex to {}.csv?'.format(fname))
		yn = input('Y/N? ')
		if yn.lower() == 'y':
			print('Writing to {}.csv'.format(fname))
			self.pokedex.write(outname=fname)
			self.change_made = False
		else:
			print('Cancelled writing current pokedex to {}.csv'.format(fname))

	def exit(self, args):
		if self.change_made:
			print('There are unwritten changes in the pokedex. Exit without writing changes?')
			yn = input('Y/N? ')
			if yn.lower() == 'y':
				print('Exiting.')
				self.main_exit = True
			else:
				print('Cancelling exit.')
		else:
			print('Exiting.')
			self.main_exit = True

	def get_cmds(self):
		cmds = {}
		cmds['add'] = self.add
		cmds['delete'] = self.delete
		cmds['evos'] = self.evo_chain
		cmds['edit'] = self.edit
		cmds['exit'] = self.exit
		cmds['find'] = self.find
		cmds['getmax'] = self.get_max
		cmds['getsize'] = self.get_size
		cmds['help'] = self.run_help
		cmds['link'] = self.link
		cmds['list'] = self.list_pokemon
		cmds['relink'] = self.relink
		cmds['setmax'] = self.set_max
		cmds['unlink'] = self.unlink
		cmds['write'] = self.write

		return cmds

	def run(self):
		cmds = self.get_cmds()
		while(True):
			try:
				if self.main_exit:
					break
				line = input('>> ').rstrip()
				if len(line) == 0:
					continue
				args = line.split()
				func = cmds.get(args[0], None)
				if func == None:
					print('The input \'{}\' is not a valid command. Please try again, or type \'help\' to see the available commands. Commands are case-sensitive.'.format(args[0]))
				else:
					func(args[1:])
			except PokeDexFull:
				print('The PokeDex is full!. Cannot add new pokemon.')
			except PokeDexEmpty:
				print('The PokeDex is empty!')
			except PokeDexOutOfRange:
				print('The pokemon number is not in the range 1 - {}'.format(self.pokedex.get_max_num()))
			except PokeDexHasEntryName:
				print('An entry already exists with that name. Delete the conflicting entry before trying again.')
			except PokeDexHasEntryNum:
				print('An entry already exists with that number. Delete the conflicting entry before trying again.')
			except PokeDexBadMax:
				print('The new max number is either not positive or less than the current PokeDex size of {}.'.format(len(self.pokedex)))
			except Exception as e:
			# 	print('Main Exception')
			# 	print(e)
				print('Oops! Something went wrong. Please try again.')
		print('Shutting Down the Pokedex')

def main(args):
	if len(args) == 0:
		print('No parameters supplied. Defaulting to the national dex.')
		loop = MainLoop()
	elif len(args) == 1:
		print('Opening the {} dex'.format(args[0]))
		loop = MainLoop(filename=args[0])
	elif len(args) == 2:
		print('Creating a new dex with the name {} and size {}'.format(args[0], args[1]))
		loop = MainLoop(filename=args[0], max_num=int(args[1]), new=True)
	loop.run()

if __name__ == '__main__':
	main(sys.argv[1:])