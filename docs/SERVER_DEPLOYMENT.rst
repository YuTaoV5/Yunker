训练服务器部署与复现
====================
已知运行栈：Ubuntu24.04、Isaac Sim5.1、Isaac Lab2.3.2（包0.54.2）、PyTorch2.7 CUDA、RSL-RL3.1.2，L40 GPU。原环境/isaac-sim/python.sh、/workspace/isaaclab；这些是历史路径，不是仓库提供的软件安装。

1. 按 NVIDIA 官方发行许可安装匹配版本 Isaac Sim/Isaac Lab；本归档不分发其专有运行时或完整CUDA SDK。安装RSL-RL3.1.2、ONNX/ONNXRuntime、MuJoCo、numpy、gymnasium等；具体依赖以脚本import和原环境锁定清单补齐为准，尚未做洁净机器安装验证。
2. 将training/isaaclab_tinker复制至独立目录。task.py要求assets/usd/tinker.usd；MuJoCo脚本还要求同源URDF/meshes。必须先核对ARCHIVE_STATUS的缺失项及源码中的路径，不能用别的机器人替代。
3. 先备份active_run.json，读取PID/cmdline确认当前任务。已有训练时不要再启动同项目训练。快照源码、配置、初始化actor、随机种子与checkpoint SHA256。
4. V10历史命令（仅在无旧任务且资产齐全时）：
   /isaac-sim/python.sh train.py --task Tinker-Robust-v10 --num_envs 1024 --max_iterations 3000 --seed 49 --run_name dagger_init_control_seed49 --pretrained_actor /ABS/PATH/cloned_actor_dagger1.pt --headless
5. MuJoCo使用单独环境执行mujoco_evaluate.py；运行前查看--help。Isaac evaluate.py --version 10 --nominal --command-suite full --seconds 60 --warmup-seconds 5 --robots-per-case 1 --seed 11 --checkpoint /ABS/model.pt --output diagnostic.json --headless。
6. 上述仅单seed单trial诊断。满训练故障不加--nominal并强制override1；独立fault-profile禁用原随机化后逐项注入。必须读输出实际参数，不以配置文件存在作为生效证明。

保留所有失败结果和检查点。训练停止不代表完成，执行完整验收后才允许发布候选。凭据通过SSH Agent/交互输入管理，不写脚本、git或日志。
