#!/usr/bin/env python3
# ruff: noqa: T201, DOC
"""Convert H2 retargeted data to motion_lib format for SONIC H2 training.

Adapted from convert_soma_csv_to_motion_lib.py for H2's 31 DOF and joint mapping.

Supports:
  1. Single H2 retarget NPZ file
  2. Directory of H2 retarget NPZ files
  3. Parent directory containing H2 retarget batches

Usage:
    python gear_sonic/data_process/convert_h2_retarget_to_motion_lib.py \
        --input demo_results/h2/robot_only/lafan/dance2_subject1.npz \
        --output data/motion_lib_h2/dance2_subject1.pkl --fps 30

    python gear_sonic/data_process/convert_h2_retarget_to_motion_lib.py \
        --input demo_results/h2/robot_only/lafan \
        --output data/motion_lib_h2/robot \
        --fps 30 --individual --num_workers 16
"""

import argparse
import os
import sys
from pathlib import Path

import joblib
import numpy as np
from scipy.spatial import transform

# H2 Constants (from gear_sonic/envs/manager_env/robots/h2.py)
# ========================================================
NUM_H2_DOF = 31
NUM_H2_BODIES = 32  # pelvis + 31 actuated links

# IsaacLab -> MuJoCo DOF mapping for H2
H2_ISAACLAB_TO_MUJOCO_DOF = np.array(
    [
        0,  # left_hip_pitch_link -> mj_0
        3,  # right_hip_pitch_link -> mj_3
        6,  # waist_yaw_link -> mj_6
        9,  # left_hip_roll_link -> mj_9
        14, # right_hip_roll_link -> mj_14
        19, # waist_roll_link -> mj_19
        1,  # left_hip_yaw_link -> mj_1
        4,  # right_hip_yaw_link -> mj_4
        7,  # torso_link -> mj_7
        10, # left_knee_link -> mj_10
        15, # right_knee_link -> mj_15
        20, # head_pitch_link -> mj_20
        2,  # left_shoulder_pitch_link -> mj_2
        5,  # right_shoulder_pitch_link -> mj_5
        8,  # left_ankle_roll_link -> mj_8
        11, # right_ankle_roll_link -> mj_11
        16, # head_yaw_link -> mj_16
        12, # left_shoulder_roll_link -> mj_12
        17, # right_shoulder_roll_link -> mj_17
        21, # left_ankle_pitch_link -> mj_21
        23, # right_ankle_pitch_link -> mj_23
        25, # left_shoulder_yaw_link -> mj_25
        27, # right_shoulder_yaw_link -> mj_27
        29, # left_elbow_link -> mj_29
        13, # right_elbow_link -> mj_13
        18, # left_wrist_roll_link -> mj_18
        22, # right_wrist_roll_link -> mj_22
        24, # left_wrist_pitch_link -> mj_24
        26, # right_wrist_pitch_link -> mj_26
        28, # left_wrist_yaw_link -> mj_28
        30, # right_wrist_yaw_link -> mj_30
    ],
    dtype=np.int32,
)

# H2 DOF axis definitions (from h2.xml MJCF)
# Each DOF rotates around a single axis
H2_DOF_AXIS = np.array(
    [
        [0, 1, 0],  # left_hip_pitch - Y axis
        [1, 0, 0],  # left_hip_roll - X axis
        [0, 0, 1],  # left_hip_yaw - Z axis
        [0, 1, 0],  # left_knee - Y axis
        [0, 1, 0],  # left_ankle_pitch - Y axis
        [1, 0, 0],  # left_ankle_roll - X axis
        # right leg (same as left)
        [0, 1, 0],  # right_hip_pitch - Y axis
        [1, 0, 0],  # right_hip_roll - X axis
        [0, 0, 1],  # right_hip_yaw - Z axis
        [0, 1, 0],  # right_knee - Y axis
        [0, 1, 0],  # right_ankle_pitch - Y axis
        [1, 0, 0],  # right_ankle_roll - X axis
        # waist
        [0, 0, 1],  # waist_yaw - Z axis
        [1, 0, 0],  # waist_roll - X axis
        # torso (head + arms, placeholder)
        [0, 1, 0],  # head_pitch - Y axis
        [0, 1, 0],  # left_shoulder_pitch - Y axis
        [1, 0, 0],  # left_shoulder_roll - X axis
        [0, 0, 1],  # left_shoulder_yaw - Z axis
        [0, 1, 0],  # left_elbow - Y axis
        [1, 0, 0],  # left_wrist_roll - X axis
        [0, 1, 0],  # left_wrist_pitch - Y axis
        [0, 0, 1],  # left_wrist_yaw - Z axis
        # right arm (same as left)
        [0, 1, 0],  # right_shoulder_pitch - Y axis
        [1, 0, 0],  # right_shoulder_roll - X axis
        [0, 0, 1],  # right_shoulder_yaw - Z axis
        [0, 1, 0],  # right_elbow - Y axis
        [1, 0, 0],  # right_wrist_roll - X axis
        [0, 1, 0],  # right_wrist_pitch - Y axis
        [0, 0, 1],  # right_wrist_yaw - Z axis
        # head (additional pitch/yaw)
        [0, 0, 1],  # head_yaw - Z axis
    ],
    dtype=np.float32,
)


def load_h2_npz(npz_path: str) -> dict:
    """Load H2 retargeted NPZ file."""
    data = np.load(npz_path, allow_pickle=True)

    return {
        "joint_pos": data["q"].astype(np.float32),  # (T, 31)
        "body_pos_w": data.get("body_pos", data.get("root_pos", np.zeros((data["q"].shape[0], 32, 3)))).astype(np.float32),
        "body_quat_w": data.get("body_quat", np.zeros((data["q"].shape[0], 32, 4))).astype(np.float32),
    }


def convert_h2_sequence(seq_data: dict, fps: int) -> dict:
    """Convert a single H2 retargeted sequence to motion_lib format.

    Args:
        seq_data: dict with joint_pos (T, 31), body_pos_w (T, 32, 3),
                  body_quat_w (T, 32, 4 wxyz)
        fps: frame rate of the input data

    Returns:
        motion_lib entry dict with root_trans_offset, pose_aa, dof, root_rot, fps
    """
    joint_pos = seq_data["joint_pos"]  # (T, 31)
    body_pos_w = seq_data["body_pos_w"]  # (T, 32, 3)
    body_quat_w = seq_data["body_quat_w"]  # (T, 32, 4) wxyz

    T = joint_pos.shape[0]

    # 1. Root position: body_0 (pelvis) position
    root_trans_offset = body_pos_w[:, 0, :].copy()  # (T, 3)

    # 2. Root quaternion: wxyz → xyzw (scipy convention)
    root_quat_wxyz = body_quat_w[:, 0, :]  # (T, 4) [w, x, y, z]
    root_quat_xyzw = root_quat_wxyz[:, [1, 2, 3, 0]]  # (T, 4) [x, y, z, w]

    # 3. Reorder DOFs to MuJoCo order if needed
    joint_order = seq_data.get("joint_order", "mj")
    if joint_order == "il":
        # Input is IsaacLab order → reorder to MuJoCo
        dof_mj = joint_pos[:, H2_ISAACLAB_TO_MUJOCO_DOF]
    else:
        # Input is already in MuJoCo order
        dof_mj = joint_pos

    # 4. Convert DOF → pose_aa using H2 axis definitions
    dof = dof_mj[:, :NUM_H2_DOF]

    # pose_aa[body_idx] = dof_axis * dof_value (axis-angle representation)
    pose_aa = np.zeros((T, NUM_H2_BODIES, 3), dtype=np.float32)
    # Body 0 = pelvis (root), bodies 1-31 = actuated joints
    pose_aa[:, 1:NUM_H2_BODIES, :] = H2_DOF_AXIS[None, :, :] * dof[:, :, None]

    # Set root rotation as axis-angle
    pose_aa[:, 0, :] = transform.Rotation.from_quat(root_quat_xyzw).as_rotvec()

    return {
        "root_trans_offset": root_trans_offset.astype(np.float32),
        "pose_aa": pose_aa.astype(np.float32),
        "dof": dof.astype(np.float32),
        "root_rot": root_quat_xyzw.astype(np.float32),  # xyzw (scipy convention)
        "smpl_joints": np.zeros((T, 24, 3), dtype=np.float32),  # placeholder
        "fps": fps,
    }


def downsample_sequence(entry: dict, fps_source: int, fps_target: int) -> dict:
    """Downsample a motion_lib entry using stride-based frame skipping."""
    if fps_source == fps_target:
        return entry

    jump = int(fps_source / fps_target)
    if jump <= 1:
        return entry

    return {
        "root_trans_offset": entry["root_trans_offset"][::jump],
        "pose_aa": entry["pose_aa"][::jump],
        "dof": entry["dof"][::jump],
        "root_rot": entry["root_rot"][::jump],
        "smpl_joints": entry["smpl_joints"][::jump],
        "fps": fps_target,
    }


def main():
    parser = argparse.ArgumentParser(description="Convert H2 retargeted data to motion_lib format")
    parser.add_argument("--input", required=True, help="Input NPZ file or directory")
    parser.add_argument("--output", required=True, help="Output PKL file or directory")
    parser.add_argument("--fps", type=int, default=30, help="Target output FPS")
    parser.add_argument(
        "--fps_source",
        type=int,
        default=None,
        help="Source data FPS. If set and != --fps, data is downsampled.",
    )
    parser.add_argument(
        "--individual",
        action="store_true",
        help="Write individual PKLs per motion (preserves directory structure)",
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=8,
        help="Number of parallel workers for --individual mode",
    )
    args = parser.parse_args()

    print(f"H2 {NUM_H2_DOF} DOFs, {NUM_H2_BODIES} bodies")

    # ==================== Single NPZ file ====================
    if args.input.endswith(".npz") and os.path.isfile(args.input):
        print(f"Converting single H2 NPZ: {args.input}")

        motion_name = Path(args.input).stem
        seq = load_h2_npz(args.input)

        entry = convert_h2_sequence(seq, args.fps_source or args.fps)
        if args.fps_source and args.fps_source != args.fps:
            entry = downsample_sequence(entry, args.fps_source, args.fps)

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        joblib.dump({motion_name: entry}, args.output, compress=True)
        print(f"✓ Saved to {args.output}")

    # ==================== Directory of NPZ files ====================
    elif os.path.isdir(args.input):
        npz_files = sorted(Path(args.input).glob("*.npz"))
        print(f"Found {len(npz_files)} NPZ files in {args.input}")

        if args.individual:
            # Write individual PKLs
            os.makedirs(args.output, exist_ok=True)

            converted = 0
            failed = 0

            for npz_file in npz_files:
                motion_name = npz_file.stem
                output_path = Path(args.output) / f"{motion_name}.pkl"

                try:
                    seq = load_h2_npz(str(npz_file))
                    entry = convert_h2_sequence(seq, args.fps_source or args.fps)

                    if args.fps_source and args.fps_source != args.fps:
                        entry = downsample_sequence(entry, args.fps_source, args.fps)

                    joblib.dump({motion_name: entry}, output_path, compress=True)
                    converted += 1

                except Exception as e:
                    print(f"  ✗ Failed to convert {motion_name}: {e}")
                    failed += 1

            print(f"✓ Converted {converted}/{len(npz_files)} motions")
            if failed > 0:
                print(f"✗ Failed: {failed}")
        else:
            # Merge all into single PKL
            sequences = {}

            for npz_file in npz_files:
                motion_name = npz_file.stem

                try:
                    seq = load_h2_npz(str(npz_file))
                    entry = convert_h2_sequence(seq, args.fps_source or args.fps)

                    if args.fps_source and args.fps_source != args.fps:
                        entry = downsample_sequence(entry, args.fps_source, args.fps)

                    sequences[motion_name] = entry
                except Exception as e:
                    print(f"  ✗ Failed to convert {motion_name}: {e}")

            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            joblib.dump(sequences, args.output, compress=True)
            print(f"✓ Saved {len(sequences)} motions to {args.output}")

    else:
        print(f"ERROR: Input not found or not a valid path: {args.input}")
        sys.exit(1)


if __name__ == "__main__":
    main()
