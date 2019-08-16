import c4d
from c4d import utils


def main():
    edges = c4d.BaseSelect()
    print edges.Select(0)


if __name__ == '__main__':
    main()