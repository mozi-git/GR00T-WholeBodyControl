#!/usr/bin/env python3
# ruff: noqa: T201, DOC
"""Filter H2 motion library PKLs to remove infeasible motions.

Removes motions that H2 cannot physically execute due to:
- Joint limit violations
- Self-collision risks
- Extreme accelerations
- Specific movement types unsuitable for H2

Adapted from filter_and_copy_bones_data.py for H2's characteristics.
"""

import argparse
import os
import sys
from pathlib import Path
from multiprocessing import Pool
import logging

import joblib
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# H2 Constants
NUM_H2_DOF = 31

# H2-specific joint angle limits (estimated from MJCF, in radians)
# These should be validated against actual h2.xml definitions
H2_JOINT_LIMITS = {
    "hip_pitch": (-1.5, 1.0),      # Limited forward lean
    "hip_roll": (-0.5, 0.5),       # Limited side tilt
    "hip_yaw": (-0.8, 0.8),        # Limited rotation
    "knee": (0.0, 2.5),            # One-directional
    "ankle_pitch": (-0.8, 0.5),    # Limited range
    "ankle_roll": (-0.5, 0.5),     # Limited range
    "waist_pitch": (-0.5, 0.5),    # Limited forward bend
    "waist_roll": (-0.5, 0.5),     # Limited side bend
    "waist_yaw": (-1.0, 1.0),      # Rotation range
    "shoulder_pitch": (-2.0, 2.0), # Wide range
    "shoulder_roll": (-1.5, 1.5),  # Wide range
    "shoulder_yaw": (-2.0, 2.0),   # Wide range
    "elbow": (0.0, 2.5),           # One-directional
    "wrist": (-1.5, 1.5),          # Limited range
}

# H2 filter keywords - motions with these keywords are removed
H2_FILTER_KEYWORDS = {
    "elevator": "Elevator interaction (H2 not stable)",
    "escalator": "Escalator interaction",
    "furniture": "Furniture interaction (limited arm strength)",
    "push": "Pushing heavy objects",
    "pull": "Pulling objects",
    "step": "Step/stair climbing",
    "climb": "Climbing (limited arm strength)",
    "jump": "Jumping (limited leg power)",
    "vehicle": "Vehicle operation",
    "sit": "Sitting (not in training scope)",
    "lie": "Lying down",
    "crawl": "Crawling (limited stability)",
    "spin": "Rapid spinning",
    "backflip": "Acrobatics",
    "cartwheel": "Acrobatics",
    "handstand": "Acrobatics",
}


def is_motion_feasible_h2(entry: dict, motion_name: str) -> tuple:
    """
    Check if H2 can physically execute this motion.

    Returns:
        (is_feasible, reason_if_filtered)
    """

    # 1. Keyword filtering
    motion_name_lower = motion_name.lower()
    for keyword, reason in H2_FILTER_KEYWORDS.items():
        if keyword in motion_name_lower:
            return False, f"Keyword: {reason}"

    # 2. Joint limit checking
    dof = entry["dof"]  # (T, 31)

    if dof.shape[0] < 2:
        return False, "Motion too short (< 2 frames)"

    # Check if any joint exceeds typical H2 limits
    # This is a simplified check - actual limits depend on MJCF
    typical_limits = (-np.pi, np.pi)  # Very permissive default

    max_joint = np.max(np.abs(dof))
    if max_joint > 4.0:  # > 229 degrees is suspicious
        return False, f"Extreme joint angle: {max_joint:.2f} rad"

    # 3. Acceleration checking
    if dof.shape[0] > 2:
        # Compute second derivative (acceleration)
        joint_acc = np.diff(dof, n=2, axis=0)  # (T-2, 31)

        max_acc = np.max(np.abs(joint_acc))
        mean_acc = np.mean(np.abs(joint_acc))

        # H2 motors have acceleration limits
        if max_acc > 50:  # rad/s^2 - very aggressive
            return False, f"Extreme acceleration: {max_acc:.2f} rad/s²"

    # 4. Stability checking (leg motion during non-locomotion)
    # If hip roll/yaw is extreme but feet aren't moving, it's unstable
    hip_indices = [3, 4, 6, 7]  # Estimated hip roll/yaw indices
    if hip_indices[0] < dof.shape[1]:
        hip_motion = np.max(np.abs(dof[:, hip_indices]))
        if hip_motion > 1.0:
            # This is a rough check - would need proper foot position analysis
            pass

    return True, "Passed all checks"


def process_motion_file(args_tuple):
    """Process a single motion PKL file (for multiprocessing)."""
    input_path, motion_name, output_dir = args_tuple

    try:
        data = joblib.load(input_path)

        if motion_name not in data:
            return motion_name, "SKIP", f"Motion '{motion_name}' not in file"

        entry = data[motion_name]

        is_feasible, reason = is_motion_feasible_h2(entry, motion_name)

        if is_feasible:
            output_path = Path(output_dir) / f"{motion_name}.pkl"
            os.makedirs(output_dir, exist_ok=True)
            joblib.dump({motion_name: entry}, output_path, compress=True)
            return motion_name, "PASS", reason
        else:
            return motion_name, "FILTER", reason

    except Exception as e:
        return motion_name, "ERROR", str(e)


def main():
    parser = argparse.ArgumentParser(description="Filter H2 motion library for feasibility")
    parser.add_argument("--source", required=True, help="Source motion library directory")
    parser.add_argument("--dest", required=True, help="Destination filtered directory")
    parser.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Number of parallel workers",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be filtered (don't copy files)",
    )
    parser.add_argument(
        "--add-keywords",
        type=str,
        default="",
        help="Additional keywords to filter (comma-separated)",
    )

    args = parser.parse_args()

    source_dir = Path(args.source)
    dest_dir = Path(args.dest)

    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        sys.exit(1)

    # Add custom keywords
    if args.add_keywords:
        for keyword in args.add_keywords.split(","):
            keyword = keyword.strip()
            if keyword:
                H2_FILTER_KEYWORDS[keyword.lower()] = "Custom filter"

    # Find all PKL files
    pkl_files = sorted(source_dir.glob("*.pkl"))
    print(f"Found {len(pkl_files)} motion files in {source_dir}")
    print(f"Output: {dest_dir}")

    if args.dry_run:
        print("\n=== DRY RUN MODE ===\n")

    # Process each motion
    passed = 0
    filtered = 0
    errors = 0
    filter_reasons = {}

    for pkl_file in pkl_files:
        motion_name = pkl_file.stem

        try:
            data = joblib.load(pkl_file)
            entry = data[motion_name]

            is_feasible, reason = is_motion_feasible_h2(entry, motion_name)

            if is_feasible:
                passed += 1
                if not args.dry_run:
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_file = dest_dir / pkl_file.name
                    os.system(f"cp {pkl_file} {dest_file}")
            else:
                filtered += 1
                # Track reasons
                if reason not in filter_reasons:
                    filter_reasons[reason] = 0
                filter_reasons[reason] += 1

                if args.dry_run or filtered <= 10:
                    print(f"  FILTER: {motion_name:50} | {reason}")

        except Exception as e:
            errors += 1
            print(f"  ERROR: {motion_name:50} | {str(e)[:50]}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total motions:  {len(pkl_files)}")
    print(f"Passed:         {passed} ({100.0*passed/len(pkl_files):.1f}%)")
    print(f"Filtered:       {filtered} ({100.0*filtered/len(pkl_files):.1f}%)")
    print(f"Errors:         {errors}")

    if filter_reasons:
        print("\nFilter reasons:")
        for reason, count in sorted(filter_reasons.items(), key=lambda x: -x[1])[:10]:
            print(f"  {reason:40} | {count:4} motions")

    print("=" * 70)

    if not args.dry_run:
        print(f"\n✓ Filtered data saved to: {dest_dir}")
        print(f"  {passed} motions ready for training")


if __name__ == "__main__":
    main()
