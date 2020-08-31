# Copyright (C) 2020  ViiSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import platform
import stat
import pathlib


PSD_HOME = str(pathlib.Path().parent.absolute()) + "/.."
if platform.system() == 'Windows':
    script = str(pathlib.Path("..\\linux\\psd.bat").parent.absolute()) + "\\psd.bat"
else:
    script = str(pathlib.Path("../linux/psd.sh").parent.absolute()) + "/psd.sh"

print("Create PSD_HOME environment variable...")
if platform.system() == 'Windows':
    os.environ["PSD_HOME"] = PSD_HOME
else:
    shell = os.environ["SHELL"]
    home = os.environ["HOME"]
    if "zsh" in shell:
        file = home + "/.zshrc"
    elif "bash" in shell:
        file = home + "~/.bashrc"
    else:
        file = home + "~/.shrc"
    with open(file, 'a') as rc:
        rc.write("\n# psd auto-generated\nexport PSD_HOME=" + PSD_HOME + "\n")
        rc.close()

print("PSD_HOME:" + PSD_HOME)

print("Export psd to path...")
if platform.system() == 'Windows':
    os.environ["PATH"] += os.pathsep + os.pathsep.join([script])
    print("PATH:")
    print(os.environ["PATH"])
else:
    st = os.stat('../linux/psd.sh')
    os.chmod('../linux/psd.sh', st.st_mode | stat.S_IEXEC)
    shell = os.environ["SHELL"]
    home = os.environ["HOME"]
    if "zsh" in shell:
        file = home + "/.zshrc"
    elif "bash" in shell:
        file = home + "~/.bashrc"
    else:
        file = home + "~/.shrc"

    with open(file, 'a') as rc:
        rc.write("alias psd='" + script + "'\n")
        rc.close()
print("Done!")

if platform.system() == 'Windows':
    print("Reload current command prompt from applying changes.")
else:
    print("Reload terminal from applying changes.")
