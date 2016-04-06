#/usr/bin/bash
cid=$1
maxLecture=$2
sennadir=../../qualityprediction_server/data/senna
for c in $cid; do
	for (( w=1; w<=$maxLecture; w++ ))
    do
		for t in q1 q2 q3 q4; do
            file=../data/$c/senna/senna.$w.$t.input
            echo $file
            if [ -f "$file" ]
            then
			    $sennadir/senna-linux64 -path $sennadir/ < $file > ../data/$c/senna/senna.$w.$t.output
            fi
		done
	done
done
