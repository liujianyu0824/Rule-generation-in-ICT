#!/bin/bash

python merge_llama2_with_chinese_lora_low_mem.py \
	--base_model /seu_share/home/qiguilin/220224365/huawei/chinese-llama-2-7b-hf \
	--lora /seu_share/home/qiguilin/220224365/huawei/dir_for_chinese_llama/output_dir/pt_lora_model \
	--output_dir /seu_share/home/qiguilin/220224365/huawei/dir_for_chinese_llama/llama2-7b-zh-ict_pretrained \
	--output_type huggingface | tee /seu_share/home/qiguilin/220224365/huawei/log/merge_llama2-7b-zh-ict_pre.log 2>&1 &
