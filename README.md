# Deep Racer

This Sample Application runs a simulation which trains a reinforcement learning (RL) model to drive a car around a track.  This version has been modified from the original to support the University at Buffalo CSE department in training various RL models locally without using Amazon Web Services to load and store data.

_AWS RoboMaker sample applications include third-party software licensed under open-source licenses and is provided for demonstration purposes only. Incorporation or use of RoboMaker sample applications in connection with your production workloads or a commercial products or devices may affect your legal rights or obligations under the applicable open-source licenses. Source code information can be found [here](https://s3.console.aws.amazon.com/s3/buckets/robomaker-applications-us-east-1-72fc243f9355/deep-racer/?region=us-east-1)._

Keywords: Reinforcement learning, AWS, RoboMaker

![deepracer-hard-track-world.jpg](docs/images/deepracer-hard-track-world.jpg)

## Requirements

- Python 3 (install modules through pip: `python3 -m pip install tensorflow==1.15.2 rl_coach intel_tensorflow==2.01 boto3`)
- ROS Kinetic / Melodic - To run the simulation locally. Other distributions of ROS may work, however they have not been tested
- Gazebo - To run the simulation locally. You may need this URL to fix a [GPG error](https://askubuntu.com/questions/611221/gpg-error-http-packages-osrfoundation-org).
- An AWS S3 bucket (optional) - To store the trained reinforcement learning model
- AWS RoboMaker (optional) - To run the simulation and to deploy the trained model to the robot

## AWS Account Setup (If you plan to store models in S3)

### AWS Credentials
You will need to create an AWS Account and configure the credentials to be able to communicate with AWS services. You may find [AWS Configuration and Credential Files](https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html) helpful.

### AWS Permissions

To train the reinforcement learning model in simulation, you need an IAM role with the following policy. You can find instructions for creating a new IAM Policy
[here](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html#access_policies_create-start). In the JSON tab paste the following policy document:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "cloudwatch:PutMetricData",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "s3:Get*",
                "s3:List*",
                "s3:Put*",
                "s3:DeleteObject"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
```

## Usage

### Training the model

#### Building the simulation bundle

```bash
cd simulation_ws
rosws update
rosdep install --from-paths src --ignore-src -r -y
colcon build && colcon bundle
```

#### Running the simulation


The following environment variables must be set when you run your simulation:

- `MARKOV_PRESET_FILE` - Defines the hyperparameters of the reinforcement learning algorithm. This should be set to `deepracer.py`.
- `WORLD_NAME` - The track to train the model on. Can be one of easy_track, medium_track, or hard_track.

These must be set, but can be filled with dummy data if you do not want to store data in Amazon S3.

- `MODEL_S3_BUCKET` - The name of the S3 bucket in which you want to store the trained model.
- `MODEL_S3_PREFIX` - The path where you want to store the model.
- `ROS_AWS_REGION` - The region of the S3 bucket in which you want to store the model.
- `AWS_ACCESS_KEY_ID` - The access key for the role you created in the "AWS Permissions" section
- `AWS_SECRET_ACCESS_KEY` - The secret access key for the role you created in the "AWS Permissions" section
- `AWS_SESSION_TOKEN` - The session token for the role you created in the "AWS Permissions" section

Once the environment variables are set, you can run local training using the roslaunch command

```bash
cd ..
source simulation_ws/install/setup.sh
roslaunch deepracer_simulation local_training.launch gui:=true
```

#### Seeing your robot learn

As the reinforcement learning model improves, the reward function will increase. You can see the graph of this reward function at

All -> AWSRoboMakerSimulation -> Metrics with no dimensions -> Metric Name -> DeepRacerRewardPerEpisode

You can think of this metric as an indicator into how well your model has been trained. If the graph has plateaus, then your robot has finished learning.

![deepracer-metrics.png](docs/images/deepracer-metrics.png)

The reward data from each episode is also stored in the deepracer-reward.txt file, which you can make using matplotlib or some other visualization tool.

### Evaluating the model

#### Building the simulation bundle

You can reuse the bundle from the training phase again in the simulation phase.

#### Running the simulation

The evaluation phase requires that the same environment variables be set as in the training phase. Once the environment variables are set, you can run
evaluation using the roslaunch command

```bash
source simulation_ws/install/setup.sh
roslaunch deepracer_simulation evaluation.launch gui:=true
```

### Troubleshooting

###### The robot does not look like it is training

The training algorithm has two phases. The first is when the reinforcement learning model is used to make the car move in the track, 
while the second is when the algorithm uses the information gathered in the first phase to improve the model. In the second
phase, no new commands are sent to the car, meaning it will appear as if it is stopped, spinning in circles, or drifting off
aimlessly.

###### When running training you see an error similar to:
`GPG error: http://packages.osrfoundation.org trusty InRelease: The following signatures couldn't be verified because the public key is not available: NO_PUBKEY 67170598AF249743`

You are missing the key needed to run Gazebo.  Read this [article](https://askubuntu.com/questions/611221/gpg-error-http-packages-osrfoundation-org).

###### When running training you see an error similar to No module named rl_coach

You are missing python packages that are necessary for the application to run.  Depending on your configuration you may need to install things using one of several different commands:

`pip install --ignore-installed tensorflow==1.15.2 rl_coach intel_tensorflow==2.01 boto3`

`python -m pip install tensorflow==1.15.2 rl_coach intel_tensorflow==2.01 boto3`

`python3 -m pip install tensorflow==1.15.2 rl_coach intel_tensorflow==2.01 boto3`

`pip3 --ignore-installed install tensorflow==1.15.2 rl_coach intel_tensorflow==2.01 boto3`

`sudo python3 -m pip install tensorflow==1.15.2 rl_coach intel_tensorflow==2.01 boto3`

`sudo pip3 install tensorflow==1.15.2 rl_coach intel_tensorflow==2.01 boto3`


## Using this sample with AWS RoboMaker

You first need to install colcon. Python 3.5 or above is required.

```bash
apt-get update
apt-get install -y python3-pip python3-apt
pip3 install colcon-ros-bundle
```

After colcon is installed you need to build your robot or simulation, then you can bundle with:

```bash
# Bundling Simulation Application
cd simulation_ws
colcon bundle
```

This produces `simulation_ws/bundle/output.tar`.
You'll need to upload this artifact to an S3 bucket. You can then use the bundle to
[create a simulation application](https://docs.aws.amazon.com/robomaker/latest/dg/create-simulation-application.html),
and [create a simulation job](https://docs.aws.amazon.com/robomaker/latest/dg/create-simulation-job.html) in AWS RoboMaker.

## License

Most of this code is licensed under the MIT-0 no-attribution license. However, the sagemaker_rl_agent package is
licensed under Apache 2. See LICENSE.txt for further information.

## How to Contribute

Create issues and pull requests against this Repository on Github
