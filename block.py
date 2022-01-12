class IF():
    def __init__(self, condition, true_block, false_block):
        self.condition = condition
        self.true_block = true_block
        self.false_block = false_block

class Assign():
    def __init__(self, variable_name, value):
        self.variable_name = variable_name
        self.value = value

class Increment():
    def __init__(self, variable_name):
        self.variable_name = variable_name

class Decrement():
    def __init__(self, variable_name):
        self.variable_name = variable_name

class Command_Block():
    def __init__(self, next_block):
        self.next_block = next_block

class Block():
    def __init__(self, block_num, command_range, assignments, command_block):
        self.block_num = block_num
        self.command_range = command_range
        self.assignments = assignments
        self.next_block = command_block

class Program():
    def __init__(self):
        self.variables = []
        self.config_variables = []
        self.commands = []
        self.blocks = []
