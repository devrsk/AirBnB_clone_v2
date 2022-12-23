#!/usr/bin/env python3

from fabric.api import *

# Set the host and user to be used for the deployment
env.hosts = ['52.201.219.192', '100.25.143.187']
env.user = '<username>'

def do_pack():
    """
    Archives the static files.

    Returns:
    The path to the packed archive, or None if the packing failed.
    """
    if not os.path.isdir("versions"):
        os.mkdir("versions")
    cur_time = datetime.now()
    output = "versions/web_static_{}{}{}{}{}{}.tgz".format(
        cur_time.year,
        cur_time.month,
        cur_time.day,
        cur_time.hour,
        cur_time.minute,
        cur_time.second
    )
    try:
        print("Packing web_static to {}".format(output))
        local("tar -cvzf {} web_static".format(output))
        archize_size = os.stat(output).st_size
        print("web_static packed: {} -> {} Bytes".format(output, archize_size))
    except Exception:
        output = None
    return output

def do_deploy(archive_path):
    """
    Distributes an archive to the web servers.

    Arguments:
    archive_path -- the path to the archive to be deployed

    Returns:
    True if the deployment was successful, False otherwise
    """
    # Check if the file at the given path exists
    if not exists(archive_path):
        return False

    # Upload the archive to the /tmp/ directory of the web server
    temp = archive_path.split("/")[-1]
    filename = archive_path
    if temp:
        filename = temp
    tmp_archive = '/tmp/{}'.format(filename)
    result = put(archive_path, tmp_archive)
    if result.failed:
        return False

    # Uncompress the archive to the /data/web_static/releases/<archive filename without extension> directory
    targetFile = filename.split(".")[0]
    deploy_path = '/data/web_static/releases/{}'.format(targetFile)
    result = run("mkdir -p {}".format(deploy_path))
    if result.failed:
        return False
    result = run("tar zxvf {} -C {}".format(tmp_archive, deploy_path))
    if result.failed:
        return False

    # Delete the archive from the web server
    result = run("rm -f {}".format(tmp_archive))
    if result.failed:
        return False

    # Delete the symbolic link /data/web_static/current from the web server
    result = sudo("rm -f /data/web_static/current")
    if result.failed:
        return False

    # Create a new symbolic link /data/web_static/current on the web server, linked to the new version of your code (/data/web_static/releases/<archive filename without extension>)
    result = sudo("ln -s {} /data/web_static/current".format(deploy_path))
    return True

