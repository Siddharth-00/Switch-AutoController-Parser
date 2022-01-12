from generator import generate_code
from block import Program, Block, IF, Increment, Decrement, Assign
controller_commands = set(['UP','DOWN','LEFT','RIGHT','X','Y','A','B','A_SPAM','B_SPAM','L','R','ZL','ZR','MINUS','PLUS','DPAD_UP','DPAD_DOWN','DPAD_LEFT','DPAD_RIGHT','TRIGGERS','HOME','NOTHING'])

def parse(source_path):
    #name = input("Name of project: ")

    if_stack = []
    while_stack = []
    repeat_stack = []

    program = Program()

    curr_start_command = 0
    curr_command = -1
    curr_block = Block(0, None, [], None)
    curr_counter = 0

    with open(source_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        command = ''
        args = ''
        splitLine = [s.strip() for s in line.split(' ', 1)]
        command = splitLine[0]
        if len(splitLine) > 1:
            args = splitLine[1]
        if command in controller_commands:
            assert args.isnumeric()
            program.commands.append((command, args))
            curr_command += 1
        elif command == 'CONFIG':
            var_name, val = [s.strip() for s in args.replace(' ', '').split('=')]
            assert val.isnumeric()
            program.config_variables.append((var_name, val))
        elif command == 'DECLARE':
            var_name, val = [s.strip() for s in args.replace(' ', '').split('=')]
            assert val.isnumeric()
            program.variables.append((var_name, val))
        elif command == 'ASSIGN':
            var_name, val = [s.strip() for s in args.replace(' ', '').split('=')]
            assert val.isnumeric()
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            old_block.next_block = curr_block
            old_block.assignments.append(Assign(var_name, val))
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif command == 'INC':
            var_name = args.strip()
            assert ' ' not in var_name
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            old_block.next_block = curr_block
            old_block.assignments.append(Increment(var_name))
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif command == 'DEC':
            var_name = args.strip()
            assert ' ' not in var_name
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            old_block.next_block = curr_block
            old_block.assignments.append(Decrement(var_name))
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif command == 'IF':
            predicate = args.strip()
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            if_stack.append([old_block.block_num])
            old_block.next_block = IF(predicate, curr_block, None)
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif command == 'ELSE':
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            if_stack[-1].append(old_block.block_num)
            program.blocks[if_stack[-1][0]].next_block.false_block = curr_block
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif command == 'ENDIF':
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            if_stack[-1].append(old_block.block_num)
            program.blocks.append(old_block)
            if not program.blocks[if_stack[-1][0]].next_block.false_block:
                program.blocks[if_stack[-1][0]].next_block.false_block = curr_block
            for b in if_stack.pop()[1:]:
                program.blocks[b].next_block = curr_block
            curr_start_command = curr_command + 1
        elif command == 'WHILE':
            predicate = args.strip()
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            while_stack.append((predicate, old_block.block_num))
            old_block.next_block = IF(predicate, curr_block, None)
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif command == 'ENDWHILE':
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            predicate, b = while_stack.pop()
            old_block.next_block = IF(predicate, program.blocks[b+1], curr_block)
            program.blocks[b].next_block.false_block = curr_block
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif command == 'REPEAT':
            n = args.strip()
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            program.variables.append(('c{}'.format(curr_counter), n))
            curr_block.assignments.append(Decrement('c{}'.format(curr_counter)))
            repeat_stack.append(('c{} > 1'.format(curr_counter), old_block.block_num))
            old_block.next_block = IF('c{} > 0'.format(curr_counter), curr_block, None)
            program.blocks.append(old_block)
            curr_counter += 1
            curr_start_command = curr_command + 1
        elif command == 'ENDREPEAT':
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            predicate, b = repeat_stack.pop()
            old_block.next_block = IF(predicate, old_block, curr_block)
            program.blocks[b].next_block.false_block = curr_block
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1

    old_block = curr_block
    old_block.command_range = (curr_start_command, curr_command)
    if curr_command < curr_start_command:
        old_block.command_range = (-1, 0)
    program.blocks.append(old_block)
    curr_start_command = curr_command + 1

    return program
