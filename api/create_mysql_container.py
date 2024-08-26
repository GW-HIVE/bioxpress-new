import sys
import argparse
import subprocess
import json

def main():
    ### handle command line arguments
    parser = argparse.ArgumentParser(
        prog="create_mysql_container.py", usage="python create_mysql_container.py [options] server"
    )
    parser.add_argument("-s", "--server", help="tst/prd")
    options = parser.parse_args()
    if not options.server or options.server not in {"tst", "prd"}:
        parser.print_help()
        sys.exit(1)
    server = options.server

    ### get config info for docker container creation
    config_obj = json.load(open("config.json", "r"))
    if not isinstance(config_obj, dict):
        print(f"Error reading config JSON, expected type dict and got {type(config_obj)}.")
        sys.exit(1)
    mysql_container_name = f"running_{config_obj['project']}_mysql_{server}"
    mysql_network_name = f"{config_obj['dbinfo']['bridge_network']}_{server}"
    mysql_port = config_obj["dbinfo"]["port"][server]
    data_path = config_obj["data_path"]
    root_password = config_obj["dbinfo"]["admin"]["password"]
    db_name = config_obj["dbinfo"]["dbname"]
    db_user = config_obj["dbinfo"][db_name]["user"]
    db_password = config_obj["dbinfo"][db_name]["password"]

    ### create and populate command list
    cmd_list = []

    # check if container already exists (whether running or in a stopped state)
    cmd = f"docker ps --all | grep {mysql_container_name}"
    container_id = subprocess.getoutput(cmd).split(" ")[0].strip()
    if container_id.strip() != "":
        print(f"Found container: {mysql_container_name}")
        cmd_list.append(f"docker rm -f {container_id}")

    # check if docker network already exists
    network_cmd = f"docker network ls | grep {mysql_network_name}"
    network_cmd_output = subprocess.getoutput(network_cmd).split()
    if network_cmd_output != []:
        if network_cmd_output[1] == mysql_network_name:
            print(f"Found network: {network_cmd_output[1]}")
            cmd_list.append(f"docker network rm {mysql_network_name} | true")

    # create docker network command
    cmd_list.append(f"docker network create -d bridge {mysql_network_name}")

    # create MySQL container command
    mysql_cmd = (
        f"docker create --name {mysql_container_name} --network {mysql_network_name} "
        f"-p 127.0.0.1:{mysql_port}:3306 "
        f"-v {data_path}/api_db/{server}:/var/lib/mysql "
        f"-e MYSQL_ROOT_PASSWORD={root_password} "
        f"-e MYSQL_DATABASE={db_name} "
        f"-e MYSQL_USER={db_user} "
        f"-e MYSQL_PASSWORD={db_password} "
        "mysql:latest"
    )
    cmd_list.append(mysql_cmd)

    # run the commands
    for cmd in cmd_list:
        x = subprocess.getoutput(cmd)
        print(x)

if __name__ == "__main__":
    main()

