#!/usr/bin/env python3
import os
import sys
import getpass
import time
import stat
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import check_call, check_output
import subprocess


def install_visual_code():
    cmd = """
    wget -q https://packages.microsoft.com/keys/microsoft.asc -O- | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main"
    sudo apt update && sudo apt install code -y
    """
    if not Path("/usr/bin/code").is_file():
        check_call(cmd, shell=True)

def install_rust(asuser):
    # rustup uninstall - is how you uninstall rust
    cmd = """
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > /tmp/x
    chmod a+x /tmp/x
    /tmp/x -y -v --profile default
    """
    if not Path("~" + asuser + "/.cargo/bin/cargo").expanduser().is_file():
        execute(cmd, asuser=asuser)
    cmd = str(Path("~" + asuser + "/.cargo/bin/cargo").expanduser()) + " install starship"
    execute(cmd, asuser=asuser)

def install_exa(asuser):
    cmd = """
    wget https://github.com/ogham/exa/releases/download/v0.9.0/exa-linux-x86_64-0.9.0.zip -O /tmp/x.zip
    pushd . && cd /tmp && unzip -f x.zip && popd
    """
    epath = Path("~" + asuser + "/bin/exa-linux-x86_64").expanduser()
    if not epath.is_file():
        execute(cmd, asuser = asuser)
        execute("cp /tmp/exa-linux-x86_64 " + str(epath), asuser = asuser)
        
def install_signal():
    cmd = """
    curl -s https://updates.signal.org/desktop/apt/keys.asc | sudo apt-key add -
    echo "deb [arch=amd64] https://updates.signal.org/desktop/apt xenial main" | sudo tee -a /etc/apt/sources.list.d/signal-xenial.list
    sudo apt update && sudo apt install signal-desktop -y
    """
    if not Path("/etc/apt/sources.list.d/signal-xenial.list").is_file():
        check_call(cmd, shell=True)


def execute(s, asuser="root"):
    if asuser != "root":
        s = "sudo -u " + asuser + " bash -c " + '"' + s + '"'
    print("Executing:", s)
    output = check_output(s, shell=True)
    # os.system(s)
    return output


if __name__ == "__main__":
    print("Detecting username:", end=" ")
    print(getpass.getuser())
    username = getpass.getuser()
    parentuser = (
        os.environ["SUDO_USER"] if "SUDO_USER" in os.environ else os.environ["USER"]
    )
    print("Parent user = ", parentuser)

    assert (
        os.environ["SHELL"] == "/bin/bash"
    ), "FATAL: Use this script only if you use bash as your main shell."
    if username != "root":
        print("Please use sudo to execute this script!")
        sys.exit(1)

    # Running apt-update/upgrade
    filePath = "/var/lib/apt/periodic/update-success-stamp"
    fileStatsObj = os.stat(filePath)
    accessTime = time.ctime(fileStatsObj[stat.ST_ATIME])
    now = datetime.now()
    then = datetime.strptime(accessTime, "%a %b %d %H:%M:%S %Y")
    tdelta = now - then
    seconds = tdelta.total_seconds()
    if seconds > 7200:
        os.system("apt update && apt upgrade -y")

    # Install basics
    cmd = "apt install -y " + " ".join(x.strip() for x in open("aptreq.txt").readlines())
    os.system(cmd)

    # Install sublime text
    durl = "https://download.sublimetext.com/sublime_text_3_build_3211_x64.tar.bz2"
    spath = "~" + parentuser + "/bin/sublime_text_3/sublime_text"
    spath = Path(spath).expanduser()
    print("Checking:", spath, end="...")
    if not spath.is_file():
        os.system("rm -rf sublime_*")
        cmd = (
            "wget "
            + durl
            + " && bzip2 -d sublime_text_3_build_3211_x64.tar.bz2 && tar xvf sublime_text_3_build_3211_x64.tar"
        )
        print("Executing:", cmd)
        execute(cmd)
        execute("rm -f *.tar")
        execute("mkdir -p ~/bin", asuser=parentuser)
        execute("cp -r sublime_text_3 ~/bin", asuser=parentuser)
        execute("rm -rf sublime_text_3")
        execute(
            "ln -sf ~/bin/sublime_text_3/sublime_text ~/bin/subl", asuser=parentuser
        )
    else:
        print("Found")

    # Install chrome
    if not Path("/usr/bin/google-chrome").is_file():
        execute(
            "wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
        )
        execute("dpkg -i google-chrome-stable_current_amd64.deb")
        execute("rm google-chrome-stable_current_amd64.deb")

    # Install brave
    cmd = """
    sudo apt install apt-transport-https curl -y

    curl -s https://brave-browser-apt-release.s3.brave.com/brave-core.asc | sudo apt-key --keyring /etc/apt/trusted.gpg.d/brave-browser-release.gpg add -

    echo "deb [arch=amd64] https://brave-browser-apt-release.s3.brave.com/ stable main" | sudo tee /etc/apt/sources.list.d/brave-browser-release.list

    sudo apt update
    sudo apt install brave-browser -y
    """
    if not Path("/etc/apt/sources.list.d/brave-browser-release.list").is_file():
        check_call(cmd, shell=True)

    # Install docker
    cmd = """
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

    sudo apt update

    sudo apt install docker-ce -y
    """
    check_call(cmd, shell=True)

    install_signal()
    install_visual_code()
    install_rust(parentuser)
    install_exa(parentuser)

    # Install dropbox as user
    ps = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    if "dropboxd" not in ps:
        cmd = """cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -"" """
        execute(cmd, asuser=parentuser)
        cmd = """sudo -u """ + parentuser + """ bash -c "~/.dropbox-dist/dropboxd" & """
        print("Dropbox install command: ", cmd)
        check_call(cmd, shell=True)

    cmd = """
    sudo sensors-detect --auto
    sudo sensors
    sudo apt install psensor
    """

    # Remove snapd -- Todo someday
    # List comes from snap list
    cmd = """
    sudo snap remove snap-store
    sudo snap remove gtk-common-themes
    sudo snap remove gnome-3-34-1804
    sudo snap remove core18
    """
    # Use df to find xxxx mount name
    cmd = 'df -h | grep "/snap/" '
    # sudo umount /snap/core/xxxx
    # sudo apt purge snapd

    cmd = """
    rm -rf ~/snap
    sudo rm -rf /snap
    sudo rm -rf /var/snap
    sudo rm -rf /var/lib/snapd
    """

    # Install nix
    # cmd = "curl -L https://nixos.org/nix/install | sh"
    # execute(cmd, asuser=parentuser)
    #   . /home/uname/.nix-profile/etc/profile.d/nix.sh

    # Install pyenv
    spath = "~" + parentuser + "/.pyenv/bin/pyenv"
    spath = Path(spath).expanduser()
    print("Checking:", spath, end="...")
    if not spath.is_file():
        print("Not found. Installing pyenv.")
        cmd = "curl https://pyenv.run | bash"
        execute(cmd, asuser=parentuser)
    else:
        print("Present. Skipping pyenv install.")

    # Install .bashrc
    spath = "~" + parentuser + "/.bashrc"
    spath = Path(spath).expanduser()
    bashrc = open("dotfiles/.bashrc").read().format(username=parentuser)
    open(spath, "w").write(bashrc)

    # Install .tmux.conf
    cmd = "cp dotfiles/.tmux.conf ~/"
    execute(cmd, asuser=parentuser)

    print("Open a new terminal for paths to take effect!")
