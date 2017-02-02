#! /bin/sh


base=$2
participantsTSV="${base}participants.tsv"
log="${base}reformatting.log"
mkdir -p ${base}
touch ${participantsTSV}
echo "participant_id" >> $participantsTSV
ls ${1} | while read s
do
    sub="sub-$s"
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

            bids_inpaintFile="${subBase}${sessionDir}_inpaint/anat/sub-${s}_${sessionDir}_inpaint_T1w.nii.gz"
            mkdir -p `dirname $bids_inpaintFile`
            cp $inpaintFile $bids_inpaintFile
            echo "${inpaintFile} --> ${bids_inpaintFile}" >> $log
        fi


        if [ ! -e $rawFile ]
        then
            echo "Error file $rawFile does not exist. Skipping"
        else
            bids_rawFile="${subBase}${sessionDir}_raw/anat/sub-${s}_${sessionDir}_raw_T1w.nii.gz"
            mkdir -p `dirname $bids_rawFile`
            cp $rawFile $bids_rawFile
            echo "${rawFile} --> ${bids_rawFile} " >> $log
        fi

    done
done

