#!/usr/bin/env python3

"""
Utility functions for preparing input and output for model inference.
"""

import os
import json
import logging
from pathlib import Path
import numpy as np
from datasets import load_dataset, load_from_disk

logger = logging.getLogger(__name__)


def prepare_output(
    dataset_name_or_path,
    split,
    output_dir,
    shard_id=None,
    num_shards=None,
    model_name_or_path=None,
    image_name=None,
):
    """
    Prepares the output file path and collects existing IDs from the file if it exists.
    
    Args:
        dataset_name_or_path (str): The name or path of the dataset.
        split (str): The dataset split to use.
        shard_id (int, optional): The shard ID to process.
        num_shards (int, optional): The number of shards.
        output_dir (str): The directory to write the output file to.
        model_name_or_path (str, optional): The name or path of the model to use.
        image_name (str, optional): The name of the image to use. Used instead of model_name_or_path if provided.
        
    Returns:
        tuple: A tuple containing (output_file, existing_ids)
        
    Raises:
        ValueError: If neither model_name_or_path nor image_name is provided, or if both are provided.
    """
    if image_name is not None and model_name_or_path is not None:
        raise ValueError("Only one of model_name_or_path or image_name should be provided, not both")
    
    if image_name is not None:
        # Use image_name instead of model_name_or_path
        model_nickname = image_name
    elif model_name_or_path is not None:
        model_nickname = model_name_or_path
        if "checkpoint" in Path(model_name_or_path).name:
            model_nickname = Path(model_name_or_path).parent.name
        else:
            model_nickname = Path(model_name_or_path).name
    else:
        raise ValueError("Either model_name_or_path or image_name must be provided")
    
    output_file = f"{model_nickname}__{dataset_name_or_path.split('/')[-1]}__{split}"
    
    if shard_id is not None and num_shards is not None:
        output_file += f"__shard-{shard_id}__num_shards-{num_shards}"
    
    output_file = Path(output_dir, output_file + ".jsonl")
    logger.info(f"Will write to {output_file}")
    
    existing_ids = set()
    if os.path.exists(output_file):
        with open(output_file) as f:
            for line in f:
                data = json.loads(line)
                instance_id = data["instance_id"]
                existing_ids.add(instance_id)
    logger.info(f"Read {len(existing_ids)} already completed ids from {output_file}")
    
    return output_file, existing_ids


def prepare_input(
    dataset_name_or_path,
    split,
    existing_ids,
    shard_id,
    num_shards,
):
    """
    Prepares the input dataset by loading it, filtering out existing IDs, and applying sharding if needed.
    
    Args:
        dataset_name_or_path (str): The name or path of the dataset.
        split (str): The dataset split to use.
        existing_ids (set): Set of IDs that have already been processed.
        shard_id (int, optional): The shard ID to process.
        num_shards (int, optional): The number of shards.
        
    Returns:
        datasets.Dataset: The prepared dataset.
    """
    if Path(dataset_name_or_path).exists():
        dataset = load_from_disk(dataset_name_or_path)
    else:
        dataset = load_dataset(dataset_name_or_path)
    
    if split not in dataset:
        raise ValueError(f"Invalid split {split} for dataset {dataset_name_or_path}")
    
    dataset = dataset[split]
    lens = np.array(list(map(len, dataset["text"])))
    dataset = dataset.select(np.argsort(lens))
    
    if len(existing_ids) > 0:
        dataset = dataset.filter(
            lambda x: x["instance_id"] not in existing_ids,
            desc="Filtering out existing ids",
            load_from_cache_file=False,
        )
    
    if shard_id is not None and num_shards is not None:
        dataset = dataset.shard(num_shards, shard_id, contiguous=True)
    
    return dataset 