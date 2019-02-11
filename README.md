# RexCam
This repo contains Python implementations of ReXCam: Resource-Efficient, Cross-Camera Video Analytics at Scale.

## Dependencies

- [PyTorch](http://pytorch.org/) (0.4.0)
- [torchvision](https://github.com/pytorch/vision/) (0.2.1)
- [OpenCV]() ()
- [AWS Deeplens]() ()
- [MXNet]() ()

Python2 is recommended for current version.

## Install
1. `cd` to the folder where you want to download this repo.
2. run `git clone https://github.com/skybigzhou/RexCam.git`.

## Prepare data
Create a directory to store reid datasets under this repo via

## Controller
Run the controller on remote laptop with
```
PYTHONPATH=. python src/controller/messenger_run.py
```
And 

Inside ```messenger_run.py``` rememeber to modify spatial temporal correlation matrix ```corr_matrix```, ```start_times```, and ```end_times```. 

Then in function ```trigger()``` message sending format is ```(ip_address, instruction, keyword, task, model, video, bAnalysis, query, start_time, end_time)```

## Worker

### Model Management
run model management

```
bash script.sh run modelmanagement
```

or

```
PYTHONPATH=. python src/worker/modelManagement.py -mps {list of model_path}
```

arguments: ```-mps``` model_path loading to GPU

### Data Management
run data management

```
bash script.sh run datamanagement
```

or 

```
PYTHONPATH=. python src/worker/dataManagement.py -t {duration_time}
```

arguments: ```-t``` duration time

### Worker Thread
run worker for local version

```
PYTHONPATH=. python src/worker/script.py -f intel_mo_IR -mp /opt/awscam/artifacts/deploy_ssd_mobilenet_512 -t ssd -s AWSCAM -n deploy_ssd_mobilenet_512
```

arguments: ```-f {format}
-mp {model_path}
-t {task}
-s {video source}
-n {model_nickname}``` 

run worker for remote control version

```
PTYHONPATH=. python src/worker/script.py
```