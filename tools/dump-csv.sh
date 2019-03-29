#!/bin/sh

PROJECT_BASE=${1}
PROJECT_NAME=${2}

RETURN_PWD=${PWD}

if [ ! -d $PROJECT_BASE ] ; then
    mkdir -p $PROJECT_BASE
fi

cd $PROJECT_BASE

if [ ! -d $PROJECT_NAME ] ; then
    git clone "https://github.com/${PROJECT_BASE}/${PROJECT_NAME}.git"
    if [ $? != 0 ] ; then
        rm -rf $PROJECT_NAME
	exit -1
    fi
else
    cd $PROJECT_NAME
    git pull
    if [ $? != 0 ] ; then
        echo "Git pull error"
        exit -1
    fi
    cd ..
fi

cd $RETURN_PWD

cd ${PROJECT_BASE}/${PROJECT_NAME}

if [ "${3}" = "" ] ; then
    git log --date=short --pretty=format:'%H|%an|%ae|%ad' > /tmp/${PROJECT_NAME}-log.csv
else
    git log --date=short --pretty=format:'%H|%an|%ae|%ad' | grep -v "${3}" > /tmp/${PROJECT_NAME}-log.csv
fi

echo "SHA|NAME|EMAIL|DOMAIN|DATE|LINES" > ${PROJECT_NAME}-log.csv

while read LINE
do
    SHA=`echo $LINE | cut -d'|' -f1`
    echo $SHA
    NAME=`echo $LINE | cut -d'|' -f2`
    EMAIL=`echo $LINE | cut -d'|' -f3`
    DATE=`echo $LINE | cut -d'|' -f4`
    LINES=`git show $SHA | grep -v "+++" | grep -v "\-\-\-" | grep "^[+/-]" | wc -l`
    DOMAIN=`echo $EMAIL | cut -d'@' -f2`
    echo "$SHA|$NAME|$EMAIL|$DOMAIN|$DATE|$LINES" >> ${PROJECT_NAME}-log.csv

    git show $SHA | grep "+++" > /tmp/${PROJECT_NAME}-temp.diff
    while read FILELINE
    do
        if [ "$FILELINE" = "+++" ] ; then
            continue
	fi
        FOLDER1=`echo $FILELINE | cut -d'/' -f2`
        FOLDER2=`echo $FILELINE | cut -d'/' -f3`
        if [ "$FOLDER1" = "\.*" ] ; then
            continue
        fi
        if [ "$FOLDER2" = "\.*" ] ; then
            continue
	fi

	if [ -f "$FOLDER1/$FOLDER2" ] ; then
            echo "$SHA|$FOLDER1" >> ${PROJECT_NAME}-modules.csv
        elif [ -d "$FOLDER1/$FOLDER2" ] ; then
            echo "$SHA|$FOLDER1/$FOLDER2" >> ${PROJECT_NAME}-modules.csv
	else
            continue
	fi
    done < /tmp/${PROJECT_NAME}-temp.diff
done < /tmp/${PROJECT_NAME}-log.csv

echo "SHA|SUBMODULE" > ${PROJECT_NAME}-modules-uniq.csv
cat ${PROJECT_NAME}-modules.csv  | sort | uniq >> ${PROJECT_NAME}-modules-uniq.csv

rm -rf ${PROJECT_NAME}-modules.csv
rm -rf /tmp/${PROJECT_NAME}-log.csv

cd $RETURN_PWD
