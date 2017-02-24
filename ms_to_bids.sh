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
    #Regex changes something like: 01_122_31 into 01c122s31. (c means clinicID, s means subjectID)
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

        bvalFile="${1}${s}/${ses}/${ses}.dwi.bval"
        bvecFile="${1}${s}/${ses}/${ses}.dwi.bvec"
        dwiFile="${1}${s}/${ses}/${ses}.dwi.nii.gz"
        
        if [ ! -e $inpaintFile ] || [ ! -e $bvalFile ] || [ ! -e $bvecFile ] || [ ! -e $dwiFile ]
        then
            echo "Error file $inpaintFile, $bvalFile, $bvecFile or $dwiFile does not exist. Skipping"
        else
            bids_inpaintFile="${subBase}${sessionDir}inpaint/anat/${sub}_${sessionDir}inpaint_T1w.nii.gz"
            mkdir -p `dirname $bids_inpaintFile`
            cp $inpaintFile $bids_inpaintFile
            echo "T1w:${inpaintFile} --> ${bids_inpaintFile}" >> $log

            bids_in_bvalFile="${subBase}${sessionDir}inpaint/dwi/${sub}_${sessionDir}inpaint_dwi.bval"
            bids_in_bvecFile="${subBase}${sessionDir}inpaint/dwi/${sub}_${sessionDir}inpaint_dwi.bvec"
            bids_in_dwiFile="${subBase}${sessionDir}inpaint/dwi/${sub}_${sessionDir}inpaint_dwi.nii.gz"

            mkdir -p `dirname $bids_in_dwiFile`
            cp $bvalFile $bids_in_bvalFile
            cp $bvecFile $bids_in_bvecFile
            cp $dwiFile $bids_in_dwiFile
            
            echo "Bval:${bvalFile} --> ${bids_in_bvalFile}" >> $log
            echo "Bvec:${bvecFile} --> ${bids_in_bvecFile}" >> $log
            echo "Dwi:${dwiFile} --> ${bids_in_dwiFile}" >> $log

        fi


        if [ ! -e $rawFile ]
        then
            echo "Error file $rawFile does not exist. Skipping"
        else
            bids_rawFile="${subBase}${sessionDir}raw/anat/${sub}_${sessionDir}raw_T1w.nii.gz"
            mkdir -p `dirname $bids_rawFile`
            cp $rawFile $bids_rawFile
            echo "T1w:${rawFile} --> ${bids_rawFile} " >> $log


            bids_raw_bvalFile="${subBase}${sessionDir}raw/dwi/${sub}_${sessionDir}raw_dwi.bval"
            bids_raw_bvecFile="${subBase}${sessionDir}raw/dwi/${sub}_${sessionDir}raw_dwi.bvec"
            bids_raw_dwiFile="${subBase}${sessionDir}raw/dwi/${sub}_${sessionDir}raw_dwi.nii.gz"


            mkdir -p `dirname $bids_raw_dwiFile`
            cp $bvalFile $bids_raw_bvalFile
            cp $bvecFile $bids_raw_bvecFile
            cp $dwiFile $bids_raw_dwiFile
            
            echo "Bval:${bvalFile} --> ${bids_raw_bvalFile}" >> $log
            echo "Bvec:${bvecFile} --> ${bids_raw_bvecFile}" >> $log
            echo "Dwi:${dwiFile} --> ${bids_raw_dwiFile}" >> $log
        fi

    done
done

