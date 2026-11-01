部署合同与验收
==============
合同候选见training/isaaclab_tinker/contracts/v10_model100_r2。该模型仅证明导出一致性，不是通过步态验收的模型。

观测39每帧、5历史、按term拼接195维：gyro*0.25、body projected gravity、cmd(vx,vy,wz)、q-default、dq*0.05、previous requested raw action。各term历史由旧到新；启动重复真实首帧，不能全零。WXYZ四元数；命令时序revision2。
关节顺序左5再右5，具体JOINTS和限位见task.py/合同。默认角[0,.08,.56,-1.12,-.57,0,-.08,-.56,1.12,.57]，目标为default+.25action再物理限位，无相位参考、无滤波。策略50Hz、物理1ms。Kp每腿[15,17,17,17,15]，Kd[.5,1.5,1.5,1.5,.5]，力矩上限[12,20,20,20,12]Nm。

acceptance.json是不可降低的门槛。两引擎必须使用同checkpoint SHA和合同SHA，5seeds、每工况20trial、60s且5s热身、8指令，名义与独立/组合边界分别记录。正常超时不算跌倒；缺失数据不能算零。包括实际交替净空、滑移、姿态、关节限位、非有限、延迟/抖动/独立突发丢包/传感器陈旧、质量重心摩擦增益、坡度推扰、>200ms失联响应。

矩阵计划文件PLAN_ONLY不代表执行；独立初态、完整runner/aggregate、原地面接触点滑移和watchdog等仍有未完成项。源USD与URDF支撑几何一致不证明PhysX cooked hull、外扩和摩擦动力学一致。旧地面triangle标签已更正，实际USD库存为Plane。
