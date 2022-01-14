from generator import generate_code
from block import Program, Block, IF, Increment, Decrement, Assign
import re
controller_commands = set(['NOTHING','A','B','X','Y','L','R','ZL','ZR','PLUS','MINUS','HOME','CAPTURE','LCLICK','UP','DOWN','LEFT','RIGHT','RCLICK','RUP','RDOWN','RLEFT','RRIGHT','DPAD_UP','DPAD_DOWN','DPAD_LEFT','DPAD_RIGHT','A_SPAM','B_SPAM'])

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
        res = None
        if (line.strip().startswith('--')):
            continue
        if (res := re.findall(r'CONFIG\s+(\S+)\s*=\s*(\d+)', line)):
            var_name, val = res[0]
            assert val.isnumeric()
            program.config_variables.append((var_name, val))
        elif (res := re.findall(r'DECLARE\s+(\S+)\s*=\s*(\d+)', line)):
            var_name, val = res[0]
            assert val.isnumeric()
            program.variables.append((var_name, val))
        elif (res := re.findall(r'ASSIGN\s+(\S+)\s*=\s*(\d+)', line)):
            var_name, val = res[0]
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
        elif (res := re.findall(r'INC\s+(\S+)', line)):
            var_name = res[0]
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            old_block.next_block = curr_block
            old_block.assignments.append(Increment(var_name))
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif (res := re.findall(r'DEC\s+(\S+)', line)):
            var_name = res[0]
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
        elif (res := re.findall(r'IF\s+(.+)', line)):
            predicate = res[0]
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            if_stack.append([old_block.block_num])
            old_block.next_block = IF(predicate, curr_block, None)
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif (res := re.findall(r'ELSE', line)):
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            if_stack[-1].append(old_block.block_num)
            program.blocks[if_stack[-1][0]].next_block.false_block = curr_block
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif (res := re.findall(r'ENDIF', line)):
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
        elif (res := re.findall(r'WHILE\s+(.+)', line)):
            predicate = res[0]
            old_block = curr_block
            curr_block = Block(old_block.block_num + 1, None, [], None)
            old_block.command_range = (curr_start_command, curr_command)
            if curr_command < curr_start_command:
                old_block.command_range = (-1, 0)
            while_stack.append((predicate, old_block.block_num))
            old_block.next_block = IF(predicate, curr_block, None)
            program.blocks.append(old_block)
            curr_start_command = curr_command + 1
        elif (res := re.findall(r'ENDWHILE', line)):
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
        elif (res := re.findall(r'REPEAT\s+(\d+)', line)):
            n = res[0]
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
        elif (res := re.findall(r'ENDREPEAT', line)):
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
        elif (res := re.findall(r'(^[^\s\+]+(?=[\+\s]*)|(?<=[\+\s])[^\s\+]+$|(?<=[\+\s])[^\s\+]+(?=[\+\s]))', line)):
            assert all(command in controller_commands for command in res[:-1])
            assert res[-1].isnumeric()
            program.commands.append(("|".join(res[:-1]), res[-1]))
            curr_command += 1

    old_block = curr_block
    old_block.command_range = (curr_start_command, curr_command)
    if curr_command < curr_start_command:
        old_block.command_range = (-1, 0)
    program.blocks.append(old_block)
    curr_start_command = curr_command + 1

    return program
