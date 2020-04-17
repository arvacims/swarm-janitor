#!/usr/bin/env python3

import docker


def main():
    client = docker.from_env()
    print(client.info())


if __name__ == '__main__':
    main()
