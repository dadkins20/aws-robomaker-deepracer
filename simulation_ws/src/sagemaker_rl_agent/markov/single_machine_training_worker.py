"""
This is single machine training worker. It starts a local training and stores the model in S3.
"""

import argparse
import copy

from markov.s3_boto_data_store import S3BotoDataStore, S3BotoDataStoreParameters
from rl_coach.base_parameters import TaskParameters, Frameworks
from rl_coach.utils import short_dynamic_import
import imp

import markov
from markov import utils
import markov.environments
import os

MARKOV_DIRECTORY = os.path.dirname(markov.__file__)
CUSTOM_FILES_PATH = "./custom_files"

if not os.path.exists(CUSTOM_FILES_PATH):
    os.makedirs(CUSTOM_FILES_PATH)


def start_graph(graph_manager: 'GraphManager', task_parameters: 'TaskParameters'):
    # this will load any previous checkpoints
    graph_manager.create_graph(task_parameters)

    # save randomly initialized graph or resave the current checkpoint.... with a new step count and checkpoint number of 0...
    # TODO: figure out how to update total step count and cumulative rewards
    graph_manager.save_checkpoint()

    # Start the training
    graph_manager.improve()

def should_stop_training_based_on_evaluation():
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--markov-preset-file',
                        help="(string) Name of a preset file to run in Markov's preset directory.",
                        type=str,
                        default=os.environ.get("MARKOV_PRESET_FILE", "deepracer.py"))
    parser.add_argument('-c', '--local_model_directory',
                        help='(string) Path to a folder containing a checkpoint to restore the model from.',
                        type=str,
                        default=os.environ.get("LOCAL_MODEL_DIRECTORY", "./checkpoint"))
    parser.add_argument('-n', '--num_workers',
                        help="(int) Number of workers for multi-process based agents, e.g. A3C",
                        default=1,
                        type=int)
    parser.add_argument('--model-s3-bucket',
                        help='(string) S3 bucket where trained models are stored. It contains model checkpoints.',
                        type=str,
                        default=os.environ.get("MODEL_S3_BUCKET"))
    parser.add_argument('--model-s3-prefix',
                        help='(string) S3 prefix where trained models are stored. It contains model checkpoints.',
                        type=str,
                        default=os.environ.get("MODEL_S3_PREFIX"))
    parser.add_argument('--aws-region',
                        help='(string) AWS region',
                        type=str,
                        default=os.environ.get("ROS_AWS_REGION", "us-west-2"))
    parser.add_argument('--checkpoint-save-secs',
                        help="(int) Time period in second between 2 checkpoints",
                        type=int,
                        default=900)
    parser.add_argument('--save-frozen-graph',
                        help="(bool) True if we need to store the frozen graph",
                        type=bool,
                        default=True)

    args = parser.parse_args()

    if args.markov_preset_file:
        markov_path = imp.find_module("markov")[1]
        preset_location = os.path.join(markov_path, "presets", args.markov_preset_file)
        path_and_module = preset_location + ":graph_manager"
        graph_manager = short_dynamic_import(path_and_module, ignore_module_case=True)
        print("Using custom preset file from Markov presets directory!")
    else:
        raise ValueError("Unable to determine preset file")

    # TODO: support other frameworks
    if os.path.isfile(args.local_model_directory+"/checkpoint"):
        local = args.local_model_directory
    else:
        local = None
    task_parameters = TaskParameters(framework_type=Frameworks.tensorflow,
                                     checkpoint_save_secs=args.checkpoint_save_secs,
                                     checkpoint_restore_path=local,
                                     checkpoint_save_dir=args.local_model_directory)

    data_store_params_instance = S3BotoDataStoreParameters(bucket_name=args.model_s3_bucket,
                                                           s3_folder=args.model_s3_prefix,
                                                           checkpoint_dir=args.local_model_directory,
                                                           aws_region=args.aws_region)
    data_store = S3BotoDataStore(data_store_params_instance)

    if args.save_frozen_graph:
        data_store.graph_manager = graph_manager

    graph_manager.data_store_params = data_store_params_instance
    graph_manager.data_store = data_store
    graph_manager.should_stop = should_stop_training_based_on_evaluation
    start_graph(graph_manager=graph_manager, task_parameters=task_parameters)


if __name__ == '__main__':
    main()
