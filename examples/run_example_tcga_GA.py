# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 2020

@author: Yoann Pradat

    CentraleSupelec
    MICS laboratory
    9 rue Juliot Curie, Gif-Sur-Yvette, 91190 France

Example of how to annotate a list of VCF from one project/study.

Example
-----------
python examples/run_example_tcga_GA.py \
    --i_split 1 \
    --n_split 1 \
    --vep_data ~/.vep \
    --vep_n_fork 4 \
    --fasta ~/.vep/homo_sapiens/101_GRCh37/Homo_sapiens.GRCh37.75.dna.primary_assembly.fa
"""
import argparse
import os
import pandas as pd
import sys

if "." not in sys.path:
    sys.path.append(".")

from varannot import run_annotator, Vcf2mafConfig, VepConfig

#### # SCRIPT PARAMETERS 
#### #####################################################################################################

default_vep_data = os.path.expanduser("~/.vep")
default_fasta = os.path.expanduser("~/.vep/homo_sapiens/101_GRCh37/Homo_sapiens.GRCh37.75.dna.primary_assembly.fa")

parser = argparse.ArgumentParser()
parser.add_argument('--i_split'    , type=int , default=1                , help='the split processed')
parser.add_argument('--n_split'    , type=int , default=1                , help='total number of splits')
parser.add_argument('--vep_data'   , type=str , default=default_vep_data , help='path to the .vep data folder')
parser.add_argument('--vep_n_fork' , type=int , default=4                , help='number of forks to be used by VEP')
parser.add_argument('--fasta'      , type=str , default=default_fasta    , help='path to reference genome FASTA file')
args = parser.parse_args()

print("Parameters", flush=True)
for arg in vars(args):
    print("%s: %s" % (arg, getattr(args, arg)), flush=True)

#### # SCRIPT FUNCTION
#### #####################################################################################################

if __name__ == "__main__":

    vcf_folder = "./examples/data/TCGA_GA/"
    out_folder = "./examples/results/TCGA_GA/"
    vcf_meta_path = os.path.join(vcf_folder, "vcf_meta.txt")

    #### paths to results folders
    dt_folders = {
        'manual_out_folder'  : os.path.join(out_folder, "tmp/out_manual"),
        'vcf2maf_tmp_folder' : os.path.join(out_folder, "tmp/tmp_vcf2maf"),
        'vcf2maf_out_folder' : os.path.join(out_folder, "tmp/out_vcf2maf"),
        'vep_out_folder'     : os.path.join(out_folder, "tmp/out_vep"),
        'maf_folder'         : os.path.join(out_folder, "maf"),
    }

    #### # 1. LOAD
    #### # ##################################################################################################

    for k, v in dt_folders.items():
        if "folder" in k:
            os.makedirs(v, exist_ok=True)

    #### load meta data
    df_meta = pd.read_csv(
        filepath_or_buffer = vcf_meta_path,
        sep                = "\t"
    )

    vcf_files = [x for x in os.listdir(vcf_folder) if x.endswith(".vcf")]

    #### # 2. SPLIT
    #### # ##################################################################################################

    count_one_split = len(vcf_files)//args.n_split

    if args.i_split == args.n_split:
        vcf_files  = vcf_files[(args.i_split-1)*count_one_split:]
    else:
        vcf_files  = vcf_files[(args.i_split-1)*count_one_split:args.i_split*count_one_split]

    count = 0
    count_total = len(vcf_files)

    #### # 3. CONFIG
    #### # ##################################################################################################

    #### configure vep (for inside vcf2maf and for custom if set to use custom vep commands)
    vep_config = VepConfig(
        data             = args.vep_data,
        n_fork           = args.vep_n_fork,
        fasta            = args.fasta,
        custom_run       = False,
        # custom_opt       = "~/.vep/custom/ClinVar/clinvar.vcf.gz,ClinVar,vcf,exact,0,CLNSIG,CLNREVSTAT,CLNDN",
        custom_overwrite = True,
    )

    #### configure vcf2maf
    vcf2maf_config = Vcf2mafConfig(
        run       = True,
        overwrite = True
    )

    #### # 4. ANNOTATE
    #### # ##################################################################################################

    #### loop over the list
    for vcf_file in vcf_files:
        count += 1
        print("="*80, flush=True)
        print("vcf %d/%d" % (count, count_total), flush=True)
        print("processing %s\n" % vcf_file, flush=True)

        #### get vcf identifiers
        mask_vcf_file  = df_meta["file_name_GA"] == vcf_file
        index_vcf_file = mask_vcf_file[mask_vcf_file].index[0]

        dt_identifiers = {
            "Tumor_Sample"                : df_meta.loc[index_vcf_file, "tumor_sample"],
            "Tumor_Sample_Barcode"        : df_meta.loc[index_vcf_file, "tumor_sample_barcode"],
            "Matched_Norm_Sample_Barcode" : df_meta.loc[index_vcf_file, "normal_sample_barcode"],
            "Tumor_Sample_Site"           : df_meta.loc[index_vcf_file, "tumor_sample_barcode"].split("-")[3][:2],
        }

        #### get parameter values
        col_normal    = "NORMAL"
        if dt_identifiers["Tumor_Sample_Site"] == "01":
            col_tumor = "PRIMARY"
        else:
            col_tumor = "METASTATIC"
        infos_n_reads = ["AD", "DP", "FA"]
        infos_other   = ["SS", "GT"]

        run_annotator(
            vcf_folder        = vcf_folder,
            vcf_file          = vcf_file,
            col_normal        = col_normal,
            col_tumor         = col_tumor,
            infos_n_reads     = infos_n_reads,
            infos_other       = infos_other,
            dt_folders        = dt_folders,
            dt_identifiers    = dt_identifiers,
            vep_config        = vep_config,
            vcf2maf_config    = vcf2maf_config
        )
