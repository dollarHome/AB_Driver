#!/usr/bin/python
#/*
# * Copyright @2016 Intel Corporation
# *
# * This library is free software; you can redistribute it and/or
# * modify it under the terms of the GNU Lesser General Public
# * License as published by the Free Software Foundation; either
# * version 2.1 of the License, or (at your option) any later version.
# *
# * This library is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# * Lesser General Public License for more details.
# *
# * You should have received a copy of the GNU Lesser General Public
# * License along with this library. If not, see <http://www.gnu.org/licenses/>.
# *
# * Author: Sirisha Gandikota <sirisha.gandikota@intel.com>
#
# DEPENDENCIES:
# APITrace (https://github.com/apitrace/apitrace) installed on your system
# Python Image Library (PIL) installed
# python-numpy installed on your system
#
# */

import Image
import ImageChops
import tarfile
import subprocess
import sys
import getopt
import tempfile
import shutil
import os
from numpy import mean, sqrt, square


######### generate() ###########
def generate(traceFile, frameNo, archFile):
    cmd = "apitrace dump-images --calls=" + frameNo + " ./" + traceFile
    targetImgFile = frameNo + ".png"
    mvCmd = "mv *" + frameNo + ".png " + targetImgFile
    frameFile = "frameNum.txt"

    # Write the frame number to a file
    fp = open(frameFile, 'w')
    fp.write(frameNo)
    fp.close()

    # Extract image from tracefile
    retCode = subprocess.call(cmd, shell=True)
    retCode = subprocess.call(mvCmd, shell=True)

    #Tar the tracefile and imagefile
    tar = tarfile.open(archFile, "w:gz")
    tar.add(traceFile)
    tar.add(frameFile)
    tar.add(targetImgFile)
    tar.close()

    #Delete intermediary files
    os.remove(frameFile)
    os.remove(targetImgFile)
    return retCode


########## verify() ############
def verify(archFile, threshold):
    tmpDir = tempfile.mkdtemp(prefix='tmp') + "/"
    frameNo = 0
    frameFile = tmpDir + "frameNum.txt"
    traceFile = tmpDir + "*.trace"
    sourceImgFile = ""
    targetImgFile = ""

    # untar the tar file
    tar = tarfile.open(archFile, "r:gz")
    tar.extractall(tmpDir)
    tar.close()

    #Extract image from tracefile
    fp = open(frameFile, "r")
    frameNo = fp.readline()
    fp.close()
    sourceImgFile = tmpDir + frameNo + ".png"

    cmd = "apitrace dump-images --calls=" + frameNo + " " + traceFile
    targetImgFile = tmpDir + frameNo + "_target.png"
    mvCmd = "mv " + "?*" + frameNo + ".png " + targetImgFile
    retCode = subprocess.call(cmd, shell=True)
    retCode = subprocess.call(mvCmd, shell=True)

    #compare the image from tar and extracted image
    img1 = Image.open(targetImgFile)
    img2 = Image.open(sourceImgFile)

    diff = ImageChops.difference(img1, img2)
    diff.save(tmpDir + "image_diff.png")

    hist1 = img1.histogram()
    hist2 = img2.histogram()

    # Find rms error between the image histograms
    rmse = sqrt(mean(square([(hist1[i] - hist2[i]) for i in range(len(hist1))])))
    print(("RMSE =" + str(rmse) + ", Threshold = " + threshold))

    if int(rmse) > int(threshold):
        print("FAIL")
    else:
        print("PASS")

    #Clean up tmp folder
    shutil.rmtree(tmpDir)
    return retCode


########## main() ############
def main(argv):
    usageMsg = "Usage: \n python imagecompare.py generate  -i <tracefile> -f <f no> -a <output.tar.gz> \n python imagecompare.py verify  -a <output.tar.gz> -t <threshold>\n "
    traceFile = ''
    archFile = ''
    frameNo = 0
    cmdFunc = ''
    retVal = 0
    threshold = 0

    #Scan inputs
    try:
        opts, args = getopt.getopt(argv, "hgvi:f:a:t:", ["help", "generate", "verify", "ifile=", "frameno=", "afile=", "threshold="])
    except getopt.GetoptError:
        print(usageMsg)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usageMsg)
            sys.exit()
        elif opt in ("-g", "--generate"):
            cmdFunc = opt
        elif opt in ("-v", "--verify"):
            cmdFunc = opt
        elif opt in ("-i", "--ifile"):
            traceFile = arg
        elif opt in ("-f", "--frameno"):
            frameNo = arg
        elif opt in ("-a", "--afile"):
            archFile = arg
        elif opt in ("-t", "--threshold"):
            threshold = arg

    if cmdFunc == '--generate':
        if len(sys.argv) < 8:
            print(usageMsg)
            sys.exit()
        else:
            retVal = generate(traceFile, frameNo, archFile)
    elif cmdFunc == '--verify':
        if len(sys.argv) < 6:
            print(usageMsg)
            sys.exit()
        else:
            retVal = verify(archFile, threshold)

    return retVal


if __name__ == "__main__":
    main(sys.argv[1:])