from generator import generate_code
from parser import parse
def main():
    generate_code(input('Name of project: '), parse(input('Path of file: ')))

if __name__ == "__main__":
    main()
