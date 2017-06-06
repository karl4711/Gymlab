# Gymlab
This is a gym test project for the basic RL model.

---

### Dependency:

You need Python 3 and Gym to run the project.

---
### Run the project:

To run the project, you need to:

###### 1. Copy `test_env.py` to the Gym classic_control envs folder (like "..\gym\gym\envs\classic_control") ; 
###### 2. Add this line into `__init__.py` under the classic_control folder:
```
from gym.envs.classic_control.test_env import TestEnv
```
###### 3. Register the test environment by adding this code to `__init__.py` under the envs folder:
```
register(
    id='TestEnv-v0',
    entry_point='gym.envs.classic_control:TestEnv',
    max_episode_steps=200,
    reward_threshold=100.0,
)
```

###### 4. You can then run the project by typing this line under the project folder:

```
python main.py
```

---

### Usages:

There is currently only a simple interaction command line to send events and engagements to the model and see its learning process and feedback.


  