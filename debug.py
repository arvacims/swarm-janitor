#!/usr/bin/env python3

import docker


def main():
    client = docker.from_env()

    swarm_info = client.info()['Swarm']

    print(swarm_info)
    print(client.nodes.get(swarm_info['NodeID']).attrs)
    print(client.swarm.attrs)


if __name__ == '__main__':
    main()
