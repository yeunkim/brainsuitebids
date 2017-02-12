#! /bin/sh
#***IMPORTANT: $2 MUST HAVE A TRAILING SLASH.***
# recommended usage: ./ms_to_bids /ifs/faculty/shattuck/MS2016 ~/Documents/MS_BIDS
# $1: base directory of MS data
# $2: base directory where you want to create new BIDS formatted directory. Will create this dir for you

base=$2
participantsTSV="${base}participants.tsv"
log="${base}reformatting.log"
mkdir -p ${base}
touch ${participantsTSV}
echo "participant_id" >> $participantsTSV
ls ${1} | while read s
do
    #Regex changes something like: 01-122-31 into 01c122s31. (c means clinicID, s means subjectID)
    sub=`echo $s | sed -r 's/(.*)_(.*)_(.*)/sub-\1c\2s\3/'`
    echo $sub >> $participantsTSV
    subBase="$base$sub/"
    mkdir -p $subBase
    ls $1$s | while read ses
    do
        session=`echo $ses | sed 's/.*_\(M.*\)/\1/g'`
        sessionDir="ses-$session"
        inpaintFile="${1}${s}/${ses}/${ses}.t1w.inpaint.nii.gz"
        rawFile="${1}${s}/${ses}/${ses}.t1w.raw.nii.gz"
        
        if [ ! -e $inpaintFile ]
        then
            echo "Error file $inpaintFile does not exist. Skipping"
        else

            bids_inpaintFile="${subBase}${sessionDir}_inpaint/anat/${sub}_${sessionDir}_inpaint_T1w.nii.gz"
            mkdir -p `dirname $bids_inpaintFile`
            cp $inpaintFile $bids_inpaintFile
            echo "${inpaintFile} --> ${bids_inpaintFile}" >> $log
        fi


        if [ ! -e $rawFile ]
        then
            echo "Error file $rawFile does not exist. Skipping"
        else
            bids_rawFile="${subBase}${sessionDir}_raw/anat/${sub}_${sessionDir}_raw_T1w.nii.gz"
            mkdir -p `dirname $bids_rawFile`
            cp $rawFile $bids_rawFile
            echo "${rawFile} --> ${bids_rawFile} " >> $log
        fi

    done
done

