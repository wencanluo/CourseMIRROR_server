cid=$1
maxLecture=$2
SEMILADir=../../SEMILA/data/
java  -Xmx2048m -jar optimalLSA.jar $SEMILADir ../data/$cid/np/ $maxLecture