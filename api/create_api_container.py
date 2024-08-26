import sys
import argparse
import json
import subprocess

def main():
    ### handle command line arguments
    parser = argparse.ArgumentParser(
        prog="create_api_container.py",
        usage="python create_api_container.py [options] server",
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
        print("Invalid config object type, expected dict.")
        sys.exit(1)
    api_image = f"{config_obj['project']}_api_{server}"
    api_container_name = f"running_{api_image}"
    mysql_container_name = f"running_{config_obj['project']}_mysql_{server}"
    api_port = config_obj["api_port"][server]
    db_name = config_obj["dbinfo"]["dbname"]
    data_path = config_obj["data_path"]
    mysql_network_name = f"{config_obj['dbinfo']['bridge_network']}_{server}"
    db_user = config_obj["dbinfo"][db_name]["user"]
    db_pass = config_obj["dbinfo"][db_name]["password"]
    conn_str = f"mysql+pymysql://{db_user}:{db_pass}@{mysql_container_name}:3306/{db_name}"

    ### create and populate command list
    cmd_list = []

    # command to package the api
    cmd_list.append("python setup.py bdist_wheel")

    cmd_list.append(f"docker build -t {api_image} .")

    # create the command to delete the api container if it already exists
    container_id = (
        subprocess.getoutput(f"docker ps --all | grep {api_container_name}")
        .split(" ")[0]
        .strip()
    )
    if container_id.strip() != "":
        cmd_list.append(f"docker rm -f {container_id}")

    # create the command to create the api docker container
    cmd = (
        f"docker create --name {api_container_name} --network {mysql_network_name} "
        f"-p 127.0.0.1:{api_port}:80 "
        f"-v {data_path}:{data_path} "
        f"-e MYSQL_CONNSTRING={conn_str} "
        f"-e DB_NAME={db_name} "
        f"-e DATA_PATH={data_path} "
        f"-e SERVER={server} {api_image}"
    )
    cmd_list.append(cmd)

    def run_command(cmd):
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if result.returncode != 0:
            print(
                f"Command failed with error code {result.returncode}: {result.stderr}"
            )
        else:
            print(result.stdout)

    # run the commands
    for cmd in cmd_list:
        run_command(cmd)

if __name__ == "__main__":
    main()

